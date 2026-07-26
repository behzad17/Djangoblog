(function () {
  'use strict';

  var root = document.getElementById('ai-editorial-workspace');
  if (!root) return;

  var apiBase = root.getAttribute('data-api-base') || '/content-ai/workspace/api';
  var debugMode = root.getAttribute('data-debug') === '1';
  var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  var csrf = csrfInput ? csrfInput.value : '';
  var applyingClassification = false;

  function getCookie(name) {
    var match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : '';
  }
  if (!csrf) csrf = getCookie('csrftoken');

  function readSections() {
    return {
      headline: document.getElementById('ai-ws-headline').value,
      lead: document.getElementById('ai-ws-lead').value,
      body: document.getElementById('ai-ws-body').value,
      summary: document.getElementById('ai-ws-summary').value,
      excerpt: document.getElementById('ai-ws-excerpt').value,
      category: document.getElementById('ai-ws-category').value,
      tags: (document.getElementById('ai-ws-tags').value || '')
        .split(',')
        .map(function (t) { return t.trim(); })
        .filter(Boolean),
    };
  }

  function safeSetSelect(el, value) {
    if (!el) return;
    var next = value == null ? '' : String(value);
    try {
      var options = el.options || [];
      var found = false;
      for (var i = 0; i < options.length; i++) {
        if (options[i].value === next) {
          found = true;
          break;
        }
      }
      if (!found && next !== '') {
        console.error('[ai-ws] select value rejected (pattern risk)', {
          id: el.id,
          value: next,
          allowed: Array.prototype.map.call(options, function (o) {
            return o.value;
          }),
        });
        return;
      }
      el.value = next;
    } catch (err) {
      console.error('[ai-ws] select.value threw', {
        id: el.id,
        value: next,
        message: err && err.message,
        stack: err && err.stack,
      });
    }
  }

  function applySession(session) {
    if (!session) return;
    applyingClassification = true;
    var s = session.sections || {};
    document.getElementById('ai-ws-headline').value = s.headline || '';
    document.getElementById('ai-ws-lead').value = s.lead || '';
    document.getElementById('ai-ws-body').value = s.body || '';
    document.getElementById('ai-ws-summary').value = s.summary || '';
    document.getElementById('ai-ws-excerpt').value = s.excerpt || '';
    safeSetSelect(document.getElementById('ai-ws-category'), s.category || '');
    document.getElementById('ai-ws-tags').value = (s.tags || []).join(', ');
    renderCategoryRecommendation(session.category_recommendation || (session.metadata || {}).category_recommendation || {});
    document.getElementById('ai-ws-source-text').value = session.source_material || '';
    document.getElementById('ai-ws-source-url').value = session.source_url || '';
    document.getElementById('ai-ws-research').value = session.research_notes || '';
    document.getElementById('ai-ws-import-post-id').value = '';
    lastKnownSourceUrl = (session.source_url || '').trim();

    var wf = document.getElementById('ai-ws-workflow');
    if (wf) {
      var desired = session.workflow_state || 'researching';
      safeSetSelect(wf, desired);
      if (wf.value !== desired) {
        wf.selectedIndex = 0;
      }
    }

    var typeEl = document.getElementById('ai-ws-content-type');
    var goalEl = document.getElementById('ai-ws-goal');
    var styleEl = document.getElementById('ai-ws-writing-style');
    safeSetSelect(typeEl, session.content_type || 'news');
    safeSetSelect(goalEl, session.goal || 'inform');
    safeSetSelect(styleEl, session.writing_style || 'journalistic');
    var lengthEl = document.getElementById('ai-ws-article-length');
    safeSetSelect(lengthEl, session.article_length || 'full');
    var lengthMeta = document.getElementById('ai-ws-length-meta');
    if (lengthMeta) {
      lengthMeta.textContent =
        (session.article_length_label || 'Full Article') +
        ' — length changes the generation prompt, not post-truncation.';
    }
    document.getElementById('ai-ws-content-type-meta').textContent =
      'Confidence: ' + confidencePct(session.content_type_confidence) +
      (session.content_type_override ? ' · overridden' : '');
    document.getElementById('ai-ws-goal-meta').textContent =
      'Confidence: ' + confidencePct(session.goal_confidence) +
      (session.goal_override ? ' · overridden' : '');
    var styleMeta = document.getElementById('ai-ws-style-meta');
    if (styleMeta) {
      styleMeta.textContent =
        'Confidence: ' + confidencePct(session.writing_style_confidence) +
        (session.writing_style_override ? ' · overridden' : '');
    }
    renderIntelligenceExplain(session);

    var leadLabel = session.lead_label || 'Lead';
    document.getElementById('ai-ws-lead-label').textContent = leadLabel;
    var regenLead = document.getElementById('ai-ws-regen-lead');
    if (regenLead) regenLead.textContent = 'Regen ' + leadLabel.toLowerCase();
    var headlineLabel = (session.section_labels && session.section_labels.headline) || 'Headline';
    document.getElementById('ai-ws-headline-label').childNodes[0].textContent = headlineLabel + ' ';
    var regenHeadline = document.getElementById('ai-ws-regen-headline');
    if (regenHeadline) {
      regenHeadline.textContent = 'Regen ' + headlineLabel.toLowerCase();
    }

    var meta = session.metadata || {};
    var src = meta.source || {};
    var titleEl = document.getElementById('ai-ws-source-title');
    var pubEl = document.getElementById('ai-ws-source-publisher');
    if (titleEl) titleEl.value = src.title || '';
    if (pubEl) pubEl.value = src.publisher || '';
    renderSourceMeta(src);
    renderPipeline(session.pipeline_steps || []);
    renderActions(session.actions || []);
    renderExplanations(session.last_explanations || []);
    renderHistory(session.history || []);
    document.getElementById('ai-ws-seo-out').textContent = meta.seo
      ? JSON.stringify(meta.seo, null, 2)
      : '';
    document.getElementById('ai-ws-eval-out').textContent = meta.evaluation
      ? JSON.stringify(meta.evaluation, null, 2)
      : '';
    document.getElementById('ai-ws-factcheck-out').textContent = meta.fact_check
      ? JSON.stringify(meta.fact_check, null, 2)
      : '';
    renderFeaturedImage(meta.featured_image || {});
    renderBlogDraft(session.blog_draft || meta.blog_draft || {});
    renderPublishSuccess(
      session.publish_success || meta.publish_success || null
    );
    // Defer clearing the guard so programmatic <select> updates do not
    // fire a competing set_classification request that races later UI updates.
    setTimeout(function () {
      applyingClassification = false;
    }, 0);
  }

  var imagePromptExpanded = false;
  var imageGenerating = false;

  function setImagePromptExpanded(expanded) {
    imagePromptExpanded = !!expanded;
    var advanced = document.getElementById('ai-ws-image-advanced');
    var toggleBtn = document.getElementById('ai-ws-toggle-image-prompt');
    var visibility = document.getElementById('ai-ws-image-prompt-visibility');
    if (advanced) advanced.hidden = !imagePromptExpanded;
    if (toggleBtn) {
      toggleBtn.textContent = imagePromptExpanded ? 'Hide Prompt' : 'Edit Prompt';
    }
    if (visibility) {
      visibility.textContent = imagePromptExpanded ? 'Visible (editing)' : 'Hidden';
    }
  }

  function setImageGenerating(busy) {
    imageGenerating = !!busy;
    var gen = document.getElementById('ai-ws-generate-image');
    var regen = document.getElementById('ai-ws-regenerate-image');
    var accept = document.getElementById('ai-ws-accept-image');
    var loading = document.getElementById('ai-ws-image-loading');
    if (gen) gen.disabled = imageGenerating;
    if (regen) regen.disabled = imageGenerating;
    if (accept) accept.disabled = imageGenerating;
    if (loading) loading.hidden = !imageGenerating;
  }

  function runImageAction(action) {
    setImageGenerating(true);
    var errorEl = document.getElementById('ai-ws-image-error');
    if (errorEl) {
      errorEl.hidden = true;
      errorEl.textContent = '';
    }
    var payload = featuredImagePayload();
    console.log('[ai-ws] IMAGE ACTION', {
      action: action,
      image_style: payload.image_style,
      promptChars: (payload.prompt || '').length,
      aspect_ratio: '16:9',
      endpoint: apiBase.replace(/\/$/, '') + '/' + action + '/',
    });
    return post(action, payload).then(function (data) {
      setImageGenerating(false);
      if (data && data.ok) {
        try {
          applySession(data.session);
        } catch (applyErr) {
          console.error(
            '[ai-ws] applySession after image action failed',
            applyErr,
            applyErr && applyErr.stack
          );
          window.alert(
            'Image response received but UI update failed:\n' +
              (applyErr && applyErr.message) +
              '\n\n' +
              (applyErr && applyErr.stack)
          );
        }
      }
      return data;
    });
  }

  function renderFeaturedImage(state) {
    var promptEl = document.getElementById('ai-ws-image-prompt');
    var explainEl = document.getElementById('ai-ws-image-explanation');
    var statusEl = document.getElementById('ai-ws-image-status');
    var wrap = document.getElementById('ai-ws-image-preview-wrap');
    var img = document.getElementById('ai-ws-image-preview');
    var styleEl = document.getElementById('ai-ws-image-style');
    var styleLabel = document.getElementById('ai-ws-image-style-label');
    var readyEl = document.getElementById('ai-ws-image-ready');
    var missingEl = document.getElementById('ai-ws-image-ready-missing');
    var prepareBtn = document.getElementById('ai-ws-prepare-image');
    var regenBtn = document.getElementById('ai-ws-regenerate-image');
    var acceptBtn = document.getElementById('ai-ws-accept-image');
    var errorEl = document.getElementById('ai-ws-image-error');
    if (!promptEl) return;

    var hasPrompt = !!(state && String(state.prompt || '').trim());
    if (state && (state.prompt || state.status)) {
      promptEl.value = state.prompt || '';
    }
    if (styleEl && state && state.image_style) {
      safeSetSelect(styleEl, state.image_style);
    }
    if (styleLabel) {
      styleLabel.textContent =
        (state && (state.image_style_label || state.image_style)) || 'Editorial Photo';
    }
    if (explainEl) {
      explainEl.textContent = (state && state.explanation) || '';
    }
    if (readyEl) readyEl.hidden = !hasPrompt;
    if (missingEl) missingEl.hidden = hasPrompt;
    if (prepareBtn) prepareBtn.hidden = hasPrompt;
    if (regenBtn) regenBtn.hidden = !(state && state.image_url);
    if (acceptBtn) {
      var needsAccept = !!(
        state &&
        state.image_url &&
        (!state.accepted || state.pending_accept)
      );
      acceptBtn.hidden = !needsAccept;
    }

    if (errorEl) {
      if (state && state.error) {
        errorEl.hidden = false;
        errorEl.textContent = 'Image generation failed: ' + state.error;
      } else {
        errorEl.hidden = true;
        errorEl.textContent = '';
      }
    }

    if (statusEl) {
      var bits = [];
      if (hasPrompt) bits.push('AI prompt ready');
      if (state && state.status) bits.push('Status: ' + state.status);
      if (state && state.provider) bits.push('Provider: ' + state.provider);
      if (state && state.accepted && !state.pending_accept) {
        bits.push('Accepted & attached to draft');
      }
      if (state && state.pending_accept) {
        bits.push('New image ready — Accept to attach');
      }
      if (state && state.previous_image_url && state.pending_accept) {
        bits.push('Previous image kept on draft until Accept');
      }
      if (state && state.cloudinary_public_id) bits.push(state.cloudinary_public_id);
      statusEl.textContent = bits.join(' · ');
    }
    var timingEl = document.getElementById('ai-ws-image-timing');
    if (timingEl) {
      var timing = (state && state.timing) || (state && state.metadata && state.metadata.timing);
      if (debugMode && timing) {
        timingEl.hidden = false;
        timingEl.textContent =
          'OpenAI:\n' +
          (timing.openai_seconds != null ? timing.openai_seconds : '—') +
          ' s\n\nCloudinary:\n' +
          (timing.cloudinary_seconds != null ? timing.cloudinary_seconds : '—') +
          ' s\n\nTotal:\n' +
          (timing.total_seconds != null ? timing.total_seconds : '—') +
          ' s\n\nPrompt chars: ' +
          (timing.prompt_chars != null ? timing.prompt_chars : '—') +
          (timing.prompt_chars_original &&
          timing.prompt_chars_original !== timing.prompt_chars
            ? ' (from ' + timing.prompt_chars_original + ')'
            : '');
      } else {
        timingEl.hidden = true;
        timingEl.textContent = '';
      }
    }
    if (wrap && img) {
      if (state && state.image_url) {
        var candidate = String(state.image_url);
        var okSrc =
          /^https?:\/\//i.test(candidate) ||
          /^data:image\//i.test(candidate);
        if (!okSrc) {
          console.error('[ai-ws] Rejected image_url (pattern)', {
            preview: candidate.slice(0, 200),
            length: candidate.length,
          });
          statusEl.textContent =
            (statusEl.textContent ? statusEl.textContent + ' · ' : '') +
            'Invalid image URL from server (see console)';
        } else {
          try {
            img.src = candidate;
            wrap.hidden = false;
          } catch (srcErr) {
            console.error('[ai-ws] img.src assignment failed', srcErr, srcErr && srcErr.stack);
            if (statusEl) {
              statusEl.textContent =
                'img.src failed: ' + (srcErr && srcErr.message);
            }
          }
        }
      } else {
        img.removeAttribute('src');
        wrap.hidden = true;
      }
    }
    setImagePromptExpanded(imagePromptExpanded);
    if (!imageGenerating) setImageGenerating(false);
  }

  function featuredImagePayload() {
    var styleEl = document.getElementById('ai-ws-image-style');
    return {
      sections: readSections(),
      prompt: document.getElementById('ai-ws-image-prompt').value,
      image_style: styleEl ? styleEl.value : 'editorial_photo',
    };
  }

  function renderBlogDraft(draft) {
    var el = document.getElementById('ai-ws-blog-draft-status');
    var publishBtn = document.getElementById('ai-ws-publish-blog');
    if (!el) return;
    if (!draft || !draft.post_id) {
      el.innerHTML = 'Not linked to a Blog draft yet. Save to create one under Draft Posts.';
      if (publishBtn) publishBtn.hidden = true;
      return;
    }
    var isPublished = draft.status === 'published';
    var label = isPublished ? 'Published' : (draft.created ? 'Created' : 'Linked');
    var url = draft.admin_url || ('/admin/blog/post/' + draft.post_id + '/change/');
    el.innerHTML =
      label + ' Blog post <strong>#' + draft.post_id + '</strong>: ' +
      (draft.title || 'Untitled') +
      ' — <a href="' + url + '">Open in Blog Admin</a>';
    if (publishBtn) {
      publishBtn.hidden = isPublished;
    }
  }

  function renderPublishSuccess(published) {
    var banner = document.getElementById('ai-ws-publish-success');
    var openLink = document.getElementById('ai-ws-open-published');
    if (!banner) return;
    if (!published || !published.post_id) {
      banner.hidden = true;
      if (openLink) openLink.removeAttribute('href');
      return;
    }
    banner.hidden = false;
    if (openLink) {
      openLink.href = published.public_url || published.admin_url || '#';
    }
  }

  function focusSourceUrl() {
    var urlEl = document.getElementById('ai-ws-source-url');
    if (!urlEl) return;
    urlEl.focus();
    if (typeof urlEl.select === 'function') urlEl.select();
  }

  function startFreshSession() {
    return post('reset', {}).then(function (data) {
      if (!data.ok) return data;
      applySession(data.session);
      renderPublishSuccess(null);
      try {
        if (window.history && window.history.replaceState) {
          window.history.replaceState(null, '', window.location.pathname);
        }
      } catch (e) {
        /* ignore */
      }
      focusSourceUrl();
      return data;
    });
  }

  function renderPipeline(steps) {
    var el = document.getElementById('ai-ws-pipeline');
    if (!el) return;
    el.innerHTML = '';
    (steps || []).forEach(function (step) {
      var item = document.createElement('div');
      item.className = 'ai-workspace__pipeline-step' + (step.done ? ' is-done' : '');
      item.textContent = (step.done ? '✓ ' : '○ ') + step.label;
      el.appendChild(item);
    });
  }

  function renderActions(actions) {
    var wrap = document.getElementById('ai-ws-actions');
    if (!wrap) return;
    wrap.innerHTML = '';
    (actions || []).forEach(function (action) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'button';
      btn.setAttribute('data-action-id', action.id);
      btn.textContent = action.label;
      if (!action.implemented) {
        btn.disabled = true;
        btn.title = 'Coming soon';
      }
      wrap.appendChild(btn);
    });
  }

  function renderSourceMeta(src) {
    var el = document.getElementById('ai-ws-source-meta');
    var intel = document.getElementById('ai-ws-source-intel');
    if (!el) return;
    if (!src || !Object.keys(src).length) {
      el.textContent = '';
      if (intel) intel.textContent = '';
      return;
    }
    el.innerHTML =
      '<div><strong>Title:</strong> ' + (src.title || '—') + '</div>' +
      '<div><strong>Publisher:</strong> ' + (src.publisher || '—') + '</div>' +
      '<div><strong>Published:</strong> ' + (src.publication_date || '—') + '</div>' +
      '<div><strong>Language:</strong> ' + (src.detected_language || '—') + '</div>' +
      '<div><strong>Country:</strong> ' + (src.detected_country || '—') + '</div>' +
      '<div><strong>Type:</strong> ' + (src.source_type || '—') + '</div>' +
      '<div><strong>Retrieval:</strong> ' + (src.retrieval || '—') + '</div>' +
      '<div><strong>Trust:</strong> ' + (src.trust_score != null ? src.trust_score : '—') + '</div>' +
      '<div><strong>Warnings:</strong> ' + ((src.warnings || []).join('; ') || 'none') + '</div>';
    if (intel) intel.textContent = JSON.stringify(src, null, 2);
  }

  function renderExplanations(items) {
    var ul = document.getElementById('ai-ws-explanations');
    ul.innerHTML = '';
    (items || []).forEach(function (text) {
      var li = document.createElement('li');
      li.textContent = text;
      ul.appendChild(li);
    });
  }

  function renderHistory(history) {
    var ul = document.getElementById('ai-ws-history');
    ul.innerHTML = '';
    (history || []).slice().reverse().forEach(function (entry) {
      var li = document.createElement('li');
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'linklike';
      btn.textContent = entry.label + ' — restore';
      btn.addEventListener('click', function () {
        post('restore_history', { entry_id: entry.entry_id }).then(function (data) {
          if (data.ok) applySession(data.session);
        });
      });
      li.appendChild(btn);
      ul.appendChild(li);
    });
  }

  function post(action, payload) {
    var url = apiBase.replace(/\/$/, '') + '/' + action + '/';
    var bodyObj = payload || {};
    var bodyText = JSON.stringify(bodyObj);
    console.log('[ai-ws] REQUEST', {
      action: action,
      url: url,
      apiBase: apiBase,
      method: 'POST',
      payloadKeys: Object.keys(bodyObj),
      provider: bodyObj.provider || null,
      image_style: bodyObj.image_style || null,
      promptChars: bodyObj.prompt ? String(bodyObj.prompt).length : 0,
      promptPreview: bodyObj.prompt
        ? String(bodyObj.prompt).slice(0, 180)
        : '',
      bodyBytes: bodyText.length,
      csrfPresent: !!csrf,
    });
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
      },
      body: bodyText,
    }).then(function (res) {
      return res.text().then(function (text) {
        var contentType = res.headers.get('content-type') || '';
        console.log('[ai-ws] RESPONSE raw', {
          action: action,
          url: url,
          status: res.status,
          ok: res.ok,
          contentType: contentType,
          bodyChars: (text || '').length,
          bodyPreview: (text || '').slice(0, 800),
        });
        var data;
        try {
          data = text ? JSON.parse(text) : {};
        } catch (parseErr) {
          console.error('[ai-ws] JSON PARSE FAILED', {
            action: action,
            status: res.status,
            contentType: contentType,
            parseError: parseErr,
            parseStack: parseErr && parseErr.stack,
            bodyPreview: (text || '').slice(0, 2000),
          });
          var masked =
            'Non-JSON response from ' +
            url +
            ' (HTTP ' +
            res.status +
            ', content-type=' +
            contentType +
            '). ' +
            'Safari often reports this as "The string did not match the expected pattern." ' +
            'Parse error: ' +
            (parseErr && parseErr.message) +
            '\n\nBody preview:\n' +
            (text || '').slice(0, 600);
          var enriched = new Error(masked);
          enriched.stack =
            (parseErr && parseErr.stack) || enriched.stack;
          throw enriched;
        }
        console.log('[ai-ws] RESPONSE json', {
          action: action,
          status: res.status,
          okFlag: data && data.ok,
          error: data && data.error,
          featuredStatus:
            data &&
            data.featured_image &&
            data.featured_image.status,
          imageUrlPreview:
            data &&
            data.featured_image &&
            data.featured_image.image_url
              ? String(data.featured_image.image_url).slice(0, 120)
              : '',
        });
        if (!res.ok || data.ok === false) {
          var msg =
            (data.error && data.error.message) ||
            data.error ||
            'Request failed';
          if (data.session) {
            try {
              applySession(data.session);
            } catch (applyErr) {
              console.error(
                '[ai-ws] applySession failed on error response',
                applyErr,
                applyErr && applyErr.stack
              );
            }
          }
          var fail = new Error(
            typeof msg === 'string' ? msg : JSON.stringify(msg)
          );
          fail.stack =
            (fail.stack || '') +
            '\n--- server error ---\n' +
            JSON.stringify(data.error || data, null, 2);
          throw fail;
        }
        return data;
      });
    }).catch(function (err) {
      console.error('[ai-ws] FAIL', {
        action: action,
        url: url,
        message: err && err.message,
        name: err && err.name,
        stack: err && err.stack,
        err: err,
      });
      var alertText =
        (err && err.message ? err.message : String(err)) +
        (err && err.stack ? '\n\n' + err.stack : '');
      window.alert(alertText.slice(0, 4000));
      return { ok: false, error: err && err.message };
    });
  }

  function confidencePct(value) {
    var n = Number(value || 0);
    if (n <= 1) n = Math.round(n * 100);
    else n = Math.round(n);
    return n + '%';
  }

  function renderIntelligenceExplain(session) {
    var el = document.getElementById('ai-ws-intel-explain');
    if (!el) return;
    var reasons = []
      .concat(session.classification_reasons || [])
      .concat(session.goal_reasons || [])
      .concat(session.style_reasons || [])
      .slice(0, 4);
    var lines = [
      'Detected Content Type: ' + (session.content_type_detected || session.content_type || '—'),
      'Detected Goal: ' + (session.goal_detected || session.goal || '—'),
      'Detected Style: ' + (session.writing_style_detected || session.writing_style || '—'),
      'Prompt Template: ' + (session.template_id || '—'),
      'Prompt Version: ' + (session.prompt_version || 'v1'),
      'Article Length: ' + (session.article_length_label || session.article_length || 'Full Article'),
    ];
    if (reasons.length) {
      lines.push('Reasoning: ' + reasons.join(' '));
    }
    el.innerHTML = lines.map(function (line) {
      return '<div>' + line + '</div>';
    }).join('');
  }

  function currentClassificationPayload(regenerate) {
    return {
      content_type: document.getElementById('ai-ws-content-type').value,
      goal: document.getElementById('ai-ws-goal').value,
      writing_style: document.getElementById('ai-ws-writing-style').value,
      article_length: document.getElementById('ai-ws-article-length').value,
      regenerate: !!regenerate,
      sections: readSections(),
      source_text: document.getElementById('ai-ws-source-text').value,
      source_url: document.getElementById('ai-ws-source-url').value,
      title: document.getElementById('ai-ws-source-title').value,
    };
  }

  var lastKnownSourceUrl = '';

  function renderCategoryRecommendation(rec) {
    var el = document.getElementById('ai-ws-category-rec-body');
    if (!el) return;
    if (!rec || !rec.selected) {
      el.textContent = 'Import a source to recommend a Blog category from the full article.';
      return;
    }
    var candidates = rec.candidates || [];
    var list = candidates.map(function (item) {
      return (
        '<div class="ai-workspace__category-rec-item">' +
        '<strong>' + item.name + '</strong> — ' +
        (item.confidence_pct != null ? item.confidence_pct : Math.round((item.confidence || 0) * 100)) +
        '%' +
        '</div>'
      );
    }).join('');
    var reasons = (rec.reasons || []).map(function (line) {
      return '<div>' + line + '</div>';
    }).join('');
    el.innerHTML =
      '<div class="ai-workspace__category-rec-message">' + (rec.message || '') + '</div>' +
      '<div class="ai-workspace__category-rec-list">' + list + '</div>' +
      '<div class="ai-workspace__category-rec-reasons">' + reasons + '</div>';
    var categoryEl = document.getElementById('ai-ws-category');
    if (categoryEl && rec.selected && rec.selected.name) {
      var exists = Array.prototype.some.call(categoryEl.options, function (opt) {
        return opt.value === rec.selected.name;
      });
      if (!exists) {
        var opt = document.createElement('option');
        opt.value = rec.selected.name;
        opt.textContent = rec.selected.name;
        categoryEl.appendChild(opt);
      }
      if (rec.auto_selected || !categoryEl.value) {
        categoryEl.value = rec.selected.name;
      }
    }
  }

  function clearArticleFields() {
    ['ai-ws-headline', 'ai-ws-lead', 'ai-ws-body', 'ai-ws-summary', 'ai-ws-excerpt', 'ai-ws-tags'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.value = '';
    });
    var categoryEl = document.getElementById('ai-ws-category');
    if (categoryEl) categoryEl.value = '';
    renderCategoryRecommendation(null);
  }

  function onSourceUrlEdited() {
    var urlEl = document.getElementById('ai-ws-source-url');
    if (!urlEl) return;
    var next = (urlEl.value || '').trim();
    if (lastKnownSourceUrl && next && next !== lastKnownSourceUrl) {
      document.getElementById('ai-ws-source-text').value = '';
      clearArticleFields();
    }
    lastKnownSourceUrl = next;
  }

  try {
    var boot = document.getElementById('ai-ws-session-data');
    if (boot) applySession(JSON.parse(boot.textContent || '{}'));
  } catch (e) {
    /* ignore */
  }

  document.getElementById('ai-ws-ingest').addEventListener('click', function () {
    post('ingest_source', {
      source_text: document.getElementById('ai-ws-source-text').value,
      source_url: document.getElementById('ai-ws-source-url').value,
      title: document.getElementById('ai-ws-source-title').value,
      publisher: document.getElementById('ai-ws-source-publisher').value,
    }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  var sourceUrlEl = document.getElementById('ai-ws-source-url');
  if (sourceUrlEl) {
    sourceUrlEl.addEventListener('change', onSourceUrlEdited);
    sourceUrlEl.addEventListener('blur', onSourceUrlEdited);
  }

  document.getElementById('ai-ws-import').addEventListener('click', function () {
    post('import_article', {
      post_id: document.getElementById('ai-ws-import-post-id').value,
    }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  document.getElementById('ai-ws-apply-classification').addEventListener('click', function () {
    post('set_classification', currentClassificationPayload(false)).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  function onClassificationChange() {
    if (applyingClassification) return;
    post('set_classification', currentClassificationPayload(false)).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  }
  document.getElementById('ai-ws-content-type').addEventListener('change', onClassificationChange);
  document.getElementById('ai-ws-goal').addEventListener('change', onClassificationChange);
  var styleSelect = document.getElementById('ai-ws-writing-style');
  if (styleSelect) {
    styleSelect.addEventListener('change', onClassificationChange);
  }
  var lengthSelect = document.getElementById('ai-ws-article-length');
  if (lengthSelect) {
    lengthSelect.addEventListener('change', onClassificationChange);
  }

  document.getElementById('ai-ws-generate').addEventListener('click', function () {
    post('generate_draft', {
      source_text: document.getElementById('ai-ws-source-text').value,
      source_url: document.getElementById('ai-ws-source-url').value,
      title: document.getElementById('ai-ws-source-title').value,
      language: 'fa',
      content_type: document.getElementById('ai-ws-content-type').value,
      goal: document.getElementById('ai-ws-goal').value,
      writing_style: document.getElementById('ai-ws-writing-style').value,
      article_length: document.getElementById('ai-ws-article-length').value,
    }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  document.querySelectorAll('[data-regen]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      post('regenerate_section', {
        section: btn.getAttribute('data-regen'),
        sections: readSections(),
      }).then(function (data) {
        if (data.ok) applySession(data.session);
      });
    });
  });

  var saveBlogBtn = document.getElementById('ai-ws-save-blog-draft');
  if (saveBlogBtn) {
    saveBlogBtn.addEventListener('click', function () {
      var statusEl = document.getElementById('ai-ws-blog-draft-status');
      if (statusEl) {
        statusEl.textContent = 'Saving Blog draft…';
      }
      post('save_draft', {
        sections: readSections(),
        research_notes: document.getElementById('ai-ws-research').value,
      }).then(function (data) {
        if (!data.ok) {
          if (statusEl) {
            statusEl.textContent = 'Save failed. See the error alert for details.';
          }
          return;
        }
        applySession(data.session);
      });
    });
  }

  var publishBlogBtn = document.getElementById('ai-ws-publish-blog');
  if (publishBlogBtn) {
    publishBlogBtn.addEventListener('click', function () {
      if (!window.confirm('Publish this article now? It will become public.')) {
        return;
      }
      post('publish_draft', {
        sections: readSections(),
        research_notes: document.getElementById('ai-ws-research').value,
      }).then(function (data) {
        if (!data.ok) return;
        applySession(data.session);
        renderPublishSuccess(data.published || data.session.publish_success);
      });
    });
  }

  var createAnotherBtn = document.getElementById('ai-ws-create-another');
  if (createAnotherBtn) {
    createAnotherBtn.addEventListener('click', function () {
      startFreshSession();
    });
  }

  document.getElementById('ai-ws-actions').addEventListener('click', function (ev) {
    var btn = ev.target.closest('[data-action-id]');
    if (!btn || btn.disabled) return;
    post('run_action', {
      action_id: btn.getAttribute('data-action-id'),
      sections: readSections(),
    }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  document.getElementById('ai-ws-factcheck').addEventListener('click', function () {
    post('fact_check', { sections: readSections() }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  document.getElementById('ai-ws-evaluate').addEventListener('click', function () {
    post('evaluate', { sections: readSections() }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  document.getElementById('ai-ws-seo').addEventListener('click', function () {
    post('prepare_seo', { sections: readSections() }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  var prepareImageBtn = document.getElementById('ai-ws-prepare-image');
  if (prepareImageBtn) {
    prepareImageBtn.addEventListener('click', function () {
      post('prepare_image_prompt', featuredImagePayload()).then(function (data) {
        if (data.ok) applySession(data.session);
      });
    });
  }
  var generateImageBtn = document.getElementById('ai-ws-generate-image');
  if (generateImageBtn) {
    generateImageBtn.addEventListener('click', function () {
      if (imageGenerating) return;
      runImageAction('generate_image');
    });
  }
  var regenerateImageBtn = document.getElementById('ai-ws-regenerate-image');
  if (regenerateImageBtn) {
    regenerateImageBtn.addEventListener('click', function () {
      if (imageGenerating) return;
      runImageAction('regenerate_image');
    });
  }
  var restoreOriginalPromptBtn = document.getElementById('ai-ws-restore-original-image-prompt');
  if (restoreOriginalPromptBtn) {
    restoreOriginalPromptBtn.addEventListener('click', function () {
      post('restore_original_image_prompt', featuredImagePayload()).then(function (data) {
        if (data.ok) {
          applySession(data.session);
          setImagePromptExpanded(true);
        }
      });
    });
  }
  var saveImagePromptBtn = document.getElementById('ai-ws-save-image-prompt-edits');
  if (saveImagePromptBtn) {
    saveImagePromptBtn.addEventListener('click', function () {
      post('save_image_prompt_edits', featuredImagePayload()).then(function (data) {
        if (data.ok) {
          applySession(data.session);
          setImagePromptExpanded(true);
        }
      });
    });
  }
  var acceptImageBtn = document.getElementById('ai-ws-accept-image');
  if (acceptImageBtn) {
    acceptImageBtn.addEventListener('click', function () {
      if (imageGenerating) return;
      runImageAction('accept_image');
    });
  }
  var toggleImagePromptBtn = document.getElementById('ai-ws-toggle-image-prompt');
  if (toggleImagePromptBtn) {
    toggleImagePromptBtn.addEventListener('click', function () {
      setImagePromptExpanded(!imagePromptExpanded);
      if (imagePromptExpanded) {
        var promptEl = document.getElementById('ai-ws-image-prompt');
        if (promptEl) {
          promptEl.focus();
          promptEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    });
  }
  var collapseImagePromptBtn = document.getElementById('ai-ws-collapse-image-prompt');
  if (collapseImagePromptBtn) {
    collapseImagePromptBtn.addEventListener('click', function () {
      setImagePromptExpanded(false);
    });
  }
  var imageStyleSelect = document.getElementById('ai-ws-image-style');
  if (imageStyleSelect) {
    imageStyleSelect.addEventListener('change', function () {
      post('set_image_style', {
        sections: readSections(),
        image_style: imageStyleSelect.value,
        rebuild_prompt: true,
        prompt: document.getElementById('ai-ws-image-prompt').value,
      }).then(function (data) {
        if (data.ok) applySession(data.session);
      });
    });
  }

  document.getElementById('ai-ws-workflow').addEventListener('change', function (ev) {
    post('set_workflow', { state: ev.target.value }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  document.getElementById('ai-ws-reset').addEventListener('click', function () {
    if (!window.confirm('Start a new workspace session?')) return;
    startFreshSession();
  });

  // BFCache / Back-Forward cache can resurrect a stale DOM after Create another.
  // Force a real reload so the page rehydrates from the current Django session only.
  window.addEventListener('pageshow', function (event) {
    if (event.persisted) {
      window.location.reload();
    }
  });
})();
