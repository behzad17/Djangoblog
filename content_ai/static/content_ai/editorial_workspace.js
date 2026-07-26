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
    document.getElementById('ai-ws-workflow').value = session.workflow_state || 'idea';

    var typeEl = document.getElementById('ai-ws-content-type');
    var goalEl = document.getElementById('ai-ws-goal');
    if (typeEl) typeEl.value = session.content_type || 'news';
    if (goalEl) goalEl.value = session.goal || 'inform';
    document.getElementById('ai-ws-content-type-meta').textContent =
      'Detected: ' + (session.content_type_detected || session.content_type || 'news') +
      ' (' + Number(session.content_type_confidence || 0).toFixed(2) + ')' +
      (session.content_type_override ? ' · overridden' : '');
    document.getElementById('ai-ws-goal-meta').textContent =
      'Detected: ' + (session.goal_detected || session.goal || 'inform') +
      ' (' + Number(session.goal_confidence || 0).toFixed(2) + ')' +
      (session.goal_override ? ' · overridden' : '');

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
    if (titleEl && src.title) titleEl.value = src.title;
    if (pubEl && src.publisher) pubEl.value = src.publisher;
    renderSourceMeta(src);
    renderPipeline(session.pipeline_steps || []);
    renderActions(session.actions || []);
    renderExplanations(session.last_explanations || []);
    renderHistory(session.history || []);
    if (meta.seo) {
      document.getElementById('ai-ws-seo-out').textContent = JSON.stringify(meta.seo, null, 2);
    }
    if (meta.evaluation) {
      document.getElementById('ai-ws-eval-out').textContent = JSON.stringify(meta.evaluation, null, 2);
    }
    if (meta.fact_check) {
      document.getElementById('ai-ws-factcheck-out').textContent = JSON.stringify(meta.fact_check, null, 2);
    }
    applyingClassification = false;
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
    if (!wrap || !actions || !actions.length) return;
    wrap.innerHTML = '';
    actions.forEach(function (action) {
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
    if (!el) return;
    if (!src || !Object.keys(src).length) {
      el.textContent = '';
      return;
    }
    el.innerHTML =
      '<div><strong>Language:</strong> ' + (src.detected_language || '—') + '</div>' +
      '<div><strong>Country:</strong> ' + (src.detected_country || '—') + '</div>' +
      '<div><strong>Type:</strong> ' + (src.source_type || '—') + '</div>' +
      '<div><strong>Trust:</strong> ' + (src.trust_score != null ? src.trust_score : '—') + '</div>' +
      '<div><strong>Warnings:</strong> ' + ((src.warnings || []).join('; ') || 'none') + '</div>';
    document.getElementById('ai-ws-source-intel').textContent = JSON.stringify(src, null, 2);
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

  function currentClassificationPayload(regenerate) {
    return {
      content_type: document.getElementById('ai-ws-content-type').value,
      goal: document.getElementById('ai-ws-goal').value,
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

  document.getElementById('ai-ws-generate').addEventListener('click', function () {
    post('generate_draft', {
      source_text: document.getElementById('ai-ws-source-text').value,
      source_url: document.getElementById('ai-ws-source-url').value,
      title: document.getElementById('ai-ws-source-title').value,
      language: 'fa',
      content_type: document.getElementById('ai-ws-content-type').value,
      goal: document.getElementById('ai-ws-goal').value,
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

  document.getElementById('ai-ws-save-sections').addEventListener('click', function () {
    post('update_sections', {
      sections: readSections(),
      research_notes: document.getElementById('ai-ws-research').value,
    }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

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
    post('reset', {}).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });
})();
