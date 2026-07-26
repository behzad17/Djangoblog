(function () {
  'use strict';

  var root = document.getElementById('ai-editorial-workspace');
  if (!root) return;

  var apiBase = root.getAttribute('data-api-base') || '/content-ai/workspace/api';
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

  function applySession(session) {
    if (!session) return;
    applyingClassification = true;
    var s = session.sections || {};
    document.getElementById('ai-ws-headline').value = s.headline || '';
    document.getElementById('ai-ws-lead').value = s.lead || '';
    document.getElementById('ai-ws-body').value = s.body || '';
    document.getElementById('ai-ws-summary').value = s.summary || '';
    document.getElementById('ai-ws-excerpt').value = s.excerpt || '';
    document.getElementById('ai-ws-category').value = s.category || '';
    document.getElementById('ai-ws-tags').value = (s.tags || []).join(', ');
    document.getElementById('ai-ws-source-text').value = session.source_material || '';
    document.getElementById('ai-ws-source-url').value = session.source_url || '';
    document.getElementById('ai-ws-research').value = session.research_notes || '';
    document.getElementById('ai-ws-import-post-id').value = '';

    var wf = document.getElementById('ai-ws-workflow');
    if (wf) {
      var desired = session.workflow_state || 'researching';
      wf.value = desired;
      if (wf.value !== desired) {
        wf.selectedIndex = 0;
      }
    }

    var typeEl = document.getElementById('ai-ws-content-type');
    var goalEl = document.getElementById('ai-ws-goal');
    var styleEl = document.getElementById('ai-ws-writing-style');
    if (typeEl) typeEl.value = session.content_type || 'news';
    if (goalEl) goalEl.value = session.goal || 'inform';
    if (styleEl) styleEl.value = session.writing_style || 'journalistic';
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
      '<div><strong>Language:</strong> ' + (src.detected_language || '—') + '</div>' +
      '<div><strong>Country:</strong> ' + (src.detected_country || '—') + '</div>' +
      '<div><strong>Type:</strong> ' + (src.source_type || '—') + '</div>' +
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
    return fetch(apiBase.replace(/\/$/, '') + '/' + action + '/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
      },
      body: JSON.stringify(payload || {}),
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok || data.ok === false) {
          var msg = (data.error && data.error.message) || data.error || 'Request failed';
          throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
        }
        return data;
      });
    }).catch(function (err) {
      window.alert(err.message || String(err));
      return { ok: false };
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
      regenerate: !!regenerate,
      sections: readSections(),
      source_text: document.getElementById('ai-ws-source-text').value,
      source_url: document.getElementById('ai-ws-source-url').value,
      title: document.getElementById('ai-ws-source-title').value,
    };
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

  document.getElementById('ai-ws-generate').addEventListener('click', function () {
    post('generate_draft', {
      source_text: document.getElementById('ai-ws-source-text').value,
      source_url: document.getElementById('ai-ws-source-url').value,
      title: document.getElementById('ai-ws-source-title').value,
      language: 'fa',
      content_type: document.getElementById('ai-ws-content-type').value,
      goal: document.getElementById('ai-ws-goal').value,
      writing_style: document.getElementById('ai-ws-writing-style').value,
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
