(function () {
  'use strict';

  var root = document.getElementById('ai-studio');
  if (!root) return;

  var apiBase = root.getAttribute('data-api-base') || '/content-ai/studio/api';
  var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  var csrf = csrfInput ? csrfInput.value : '';

  function getCookie(name) {
    var match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : '';
  }
  if (!csrf) csrf = getCookie('csrftoken');

  function fillSelect(el, values, selected) {
    if (!el) return;
    el.innerHTML = '';
    (values || []).forEach(function (value) {
      var opt = document.createElement('option');
      opt.value = value;
      opt.textContent = value;
      if (value === selected) opt.selected = true;
      el.appendChild(opt);
    });
  }

  function renderExplanations(items) {
    var ul = document.getElementById('ai-studio-explanations');
    ul.innerHTML = '';
    (items || []).forEach(function (text) {
      var li = document.createElement('li');
      li.textContent = text;
      ul.appendChild(li);
    });
  }

  function applySession(session) {
    if (!session) return;
    var env = session.environment || 'testing';
    document.getElementById('ai-studio-environment').value = env;
    document.getElementById('ai-studio-env-badge').textContent = env;
    renderExplanations(session.last_explanations || []);
    document.getElementById('ai-studio-comparison').textContent = JSON.stringify(
      session.last_comparison || {},
      null,
      2
    );
    if (session.active_module) showModule(session.active_module);
  }

  function showModule(moduleId) {
    document.querySelectorAll('.ai-studio__panel').forEach(function (panel) {
      panel.hidden = panel.getAttribute('data-panel') !== moduleId;
    });
    document.querySelectorAll('.ai-studio__nav-btn').forEach(function (btn) {
      btn.classList.toggle('is-active', btn.getAttribute('data-module') === moduleId);
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

  function writeOut(id, data) {
    document.getElementById(id).textContent = JSON.stringify(data, null, 2);
  }

  try {
    var boot = document.getElementById('ai-studio-session-data');
    if (boot) applySession(JSON.parse(boot.textContent || '{}'));
    var opts = JSON.parse(
      (document.getElementById('ai-studio-prompt-options') || {}).textContent || '{}'
    );
    fillSelect(document.getElementById('pl-version-a'), opts.versions, opts.default_version);
    fillSelect(document.getElementById('pl-version-b'), opts.versions, opts.default_version);
    fillSelect(document.getElementById('pl-style-a'), opts.styles, opts.default_style);
    fillSelect(document.getElementById('pl-style-b'), opts.styles, 'analysis');
  } catch (e) {
    /* ignore */
  }

  document.querySelectorAll('.ai-studio__nav-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (btn.disabled) return;
      var moduleId = btn.getAttribute('data-module');
      showModule(moduleId);
      post('set_module', { module: moduleId }).then(function (data) {
        if (data.ok) applySession(data.session);
      });
    });
  });

  document.getElementById('ai-studio-environment').addEventListener('change', function (ev) {
    post('set_environment', { environment: ev.target.value }).then(function (data) {
      if (data.ok) applySession(data.session);
    });
  });

  document.getElementById('ai-studio-reset').addEventListener('click', function () {
    if (!window.confirm('Reset Studio session?')) return;
    post('reset', {
      environment: document.getElementById('ai-studio-environment').value,
    }).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('pl-out', {});
        writeOut('kl-out', {});
        writeOut('pr-out', {});
        writeOut('ev-out', {});
        writeOut('wf-out', {});
        writeOut('gh-out', {});
        writeOut('sh-out', {});
      }
    });
  });

  document.getElementById('pl-preview').addEventListener('click', function () {
    post('prompt_preview', {
      version: document.getElementById('pl-version-a').value,
      style: document.getElementById('pl-style-a').value,
      user_prompt: document.getElementById('pl-user-prompt').value,
    }).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('pl-out', data.result);
      }
    });
  });

  document.getElementById('pl-compare').addEventListener('click', function () {
    post('prompt_compare', {
      version_a: document.getElementById('pl-version-a').value,
      style_a: document.getElementById('pl-style-a').value,
      version_b: document.getElementById('pl-version-b').value,
      style_b: document.getElementById('pl-style-b').value,
      user_prompt: document.getElementById('pl-user-prompt').value,
    }).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('pl-out', data.result);
      }
    });
  });

  document.getElementById('pl-run-test').addEventListener('click', function () {
    post('run_test', {
      version: document.getElementById('pl-version-a').value,
      style: document.getElementById('pl-style-a').value,
      user_prompt: document.getElementById('pl-user-prompt').value,
      provider: document.getElementById('pl-provider').value || 'mock',
    }).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('pl-out', data.result);
      }
    });
  });

  document.getElementById('kl-browse').addEventListener('click', function () {
    post('knowledge_browse', {}).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('kl-out', data.result);
      }
    });
  });

  document.getElementById('kl-compare').addEventListener('click', function () {
    post('knowledge_compare', {
      pack_a: document.getElementById('kl-pack-a').value,
      pack_b: document.getElementById('kl-pack-b').value,
    }).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('kl-out', data.result);
      }
    });
  });

  document.getElementById('pr-inspect').addEventListener('click', function () {
    post('provider_inspect', {}).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('pr-out', data.result);
      }
    });
  });

  document.getElementById('ev-run').addEventListener('click', function () {
    post('evaluate', {
      input_text: document.getElementById('ev-input').value,
      output_text: document.getElementById('ev-output').value,
    }).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('ev-out', data.result);
      }
    });
  });

  document.getElementById('wf-inspect').addEventListener('click', function () {
    post('workflow_inspect', {
      state: document.getElementById('wf-state').value,
    }).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('wf-out', data.result);
      }
    });
  });

  document.getElementById('gh-refresh').addEventListener('click', function () {
    post('history', {}).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('gh-out', data.result);
      }
    });
  });

  document.getElementById('gh-compare').addEventListener('click', function () {
    post('compare_generations', {
      generation_id_a: document.getElementById('gh-id-a').value,
      generation_id_b: document.getElementById('gh-id-b').value,
    }).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('gh-out', data.result);
      }
    });
  });

  document.getElementById('sh-refresh').addEventListener('click', function () {
    post('system_health', {}).then(function (data) {
      if (data.ok) {
        applySession(data.session);
        writeOut('sh-out', data.result);
      }
    });
  });
})();
