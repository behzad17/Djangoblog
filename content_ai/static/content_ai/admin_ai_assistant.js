/* AI Editorial Assistant — Admin modal (ephemeral previews only). */
(function () {
  'use strict';

  var MAX_VERSIONS = 3;

  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  function csrfToken() {
    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  function setFieldValue(id, value) {
    var el = document.getElementById(id);
    if (!el) {
      return;
    }
    el.value = value == null ? '' : String(value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function formatTelemetry(telemetry) {
    if (!telemetry) {
      return 'No telemetry.';
    }
    try {
      return JSON.stringify(telemetry, null, 2);
    } catch (err) {
      return String(telemetry);
    }
  }

  ready(function () {
    var root = document.getElementById('ai-editorial-assistant');
    if (!root) {
      return;
    }

    var generateUrl = root.getAttribute('data-generate-url');
    var openBtn = document.getElementById('ai-assistant-open');
    var modal = document.getElementById('ai-assistant-modal');
    var backdrop = document.getElementById('ai-assistant-backdrop');
    var form = document.getElementById('ai-assistant-form');
    var errorBox = document.getElementById('ai-assistant-error');
    var preview = document.getElementById('ai-assistant-preview');
    var previewTitle = document.getElementById('ai-preview-title');
    var previewSummary = document.getElementById('ai-preview-summary');
    var previewBody = document.getElementById('ai-preview-body');
    var previewTelemetry = document.getElementById('ai-preview-telemetry');
    var versionsEl = document.getElementById('ai-assistant-versions');
    var generateBtn = document.getElementById('ai-assistant-generate');
    var regenerateBtn = document.getElementById('ai-assistant-regenerate');
    var acceptBtn = document.getElementById('ai-assistant-accept');
    var cancelBtns = document.querySelectorAll('[data-ai-assistant-cancel]');
    var busy = false;
    var versions = [];
    var activeIndex = null;
    var lastRequest = null;

    function showError(message) {
      errorBox.textContent = message || 'Generation failed. Please try again.';
      errorBox.hidden = false;
    }

    function clearError() {
      errorBox.textContent = '';
      errorBox.hidden = true;
    }

    function renderVersions() {
      versionsEl.innerHTML = '';
      if (!versions.length) {
        versionsEl.hidden = true;
        return;
      }
      versionsEl.hidden = false;
      versions.forEach(function (version, index) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className =
          'ai-assistant-version-btn' +
          (index === activeIndex ? ' is-active' : '');
        btn.textContent = 'Version ' + (index + 1);
        btn.addEventListener('click', function () {
          activeIndex = index;
          showPreview(versions[activeIndex]);
          renderVersions();
        });
        versionsEl.appendChild(btn);
      });
    }

    function showPreview(version) {
      preview.hidden = false;
      previewTitle.textContent = version.title || '(untitled)';
      previewSummary.textContent = version.summary || '';
      previewBody.textContent = version.body || '';
      previewTelemetry.textContent = formatTelemetry(version.telemetry);
      regenerateBtn.disabled = false;
      acceptBtn.disabled = false;
    }

    function hidePreview() {
      preview.hidden = true;
      regenerateBtn.disabled = true;
      acceptBtn.disabled = true;
    }

    function resetSession() {
      versions = [];
      activeIndex = null;
      lastRequest = null;
      clearError();
      hidePreview();
      renderVersions();
      if (form) {
        form.reset();
        var lang = form.querySelector('[name="language"]');
        if (lang && !lang.value) {
          lang.value = 'sv';
        }
        var initialTitle = root.getAttribute('data-initial-title') || '';
        var initialCategory = root.getAttribute('data-initial-category') || '';
        if (initialTitle) {
          form.querySelector('[name="title"]').value = initialTitle;
        }
        if (initialCategory) {
          form.querySelector('[name="category_id"]').value = initialCategory;
        }
      }
    }

    function openModal() {
      resetSession();
      modal.hidden = false;
      backdrop.hidden = false;
      document.body.classList.add('ai-assistant-open');
    }

    function closeModal() {
      modal.hidden = true;
      backdrop.hidden = true;
      document.body.classList.remove('ai-assistant-open');
      resetSession();
    }

    function collectRequest() {
      var categorySelect = form.querySelector('[name="category_id"]');
      var categoryId = categorySelect.value;
      var categoryName = '';
      if (categorySelect.selectedIndex >= 0) {
        categoryName = categorySelect.options[categorySelect.selectedIndex].text;
      }
      return {
        title: form.querySelector('[name="title"]').value || '',
        category_id: categoryId ? Number(categoryId) : null,
        category: categoryName,
        language: form.querySelector('[name="language"]').value || '',
        context: form.querySelector('[name="context"]').value || '',
        instructions: form.querySelector('[name="instructions"]').value || '',
        post_id: root.getAttribute('data-post-id') || '',
      };
    }

    function setBusy(isBusy) {
      busy = isBusy;
      generateBtn.disabled = isBusy;
      regenerateBtn.disabled = isBusy || !versions.length;
      acceptBtn.disabled = isBusy || activeIndex === null;
      generateBtn.textContent = isBusy ? 'Generating…' : 'Generate';
    }

    function addVersion(preview) {
      versions.push(preview);
      if (versions.length > MAX_VERSIONS) {
        versions = versions.slice(-MAX_VERSIONS);
      }
      activeIndex = versions.length - 1;
      showPreview(versions[activeIndex]);
      renderVersions();
    }

    function generate(fromRegenerate) {
      if (busy) {
        return;
      }
      clearError();
      var payload = fromRegenerate && lastRequest ? lastRequest : collectRequest();
      if (!payload.category_id) {
        showError('Please choose a category.');
        return;
      }
      lastRequest = payload;
      setBusy(true);

      fetch(generateUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken(),
          Accept: 'application/json',
        },
        body: JSON.stringify(payload),
      })
        .then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, status: response.status, data: data };
          });
        })
        .then(function (result) {
          if (!result.ok) {
            var message =
              (result.data && result.data.error && result.data.error.message) ||
              'Generation failed. Previous versions are still available.';
            showError(message);
            return;
          }
          addVersion(result.data.preview);
        })
        .catch(function () {
          showError(
            'Could not reach the AI assistant. Previous versions are still available.'
          );
        })
        .finally(function () {
          setBusy(false);
        });
    }

    function acceptActive() {
      if (activeIndex === null || !versions[activeIndex]) {
        return;
      }
      var version = versions[activeIndex];
      var title = version.title || form.querySelector('[name="title"]').value || '';
      setFieldValue('id_title', title);
      setFieldValue('id_content', version.body || '');
      setFieldValue('id_excerpt', version.summary || '');
      if (version.category_id) {
        setFieldValue('id_category', version.category_id);
      }
      setFieldValue('id_status', '0');
      closeModal();
    }

    if (openBtn) {
      openBtn.addEventListener('click', openModal);
    }
    cancelBtns.forEach(function (btn) {
      btn.addEventListener('click', closeModal);
    });
    if (backdrop) {
      backdrop.addEventListener('click', closeModal);
    }
    if (generateBtn) {
      generateBtn.addEventListener('click', function () {
        generate(false);
      });
    }
    if (regenerateBtn) {
      regenerateBtn.addEventListener('click', function () {
        generate(true);
      });
    }
    if (acceptBtn) {
      acceptBtn.addEventListener('click', acceptActive);
    }
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && modal && !modal.hidden) {
        closeModal();
      }
    });
  });
})();
