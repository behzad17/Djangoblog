/* AI Editorial Assistant — action-based Admin modal (ephemeral previews). */
(function () {
  'use strict';

  var MAX_VERSIONS = 3;
  var IMPLEMENTED = { generate: true, regenerate: true };

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

  function parseActions(root) {
    var raw = root.getAttribute('data-actions') || '[]';
    try {
      return JSON.parse(raw);
    } catch (err) {
      return [];
    }
  }

  ready(function () {
    var root = document.getElementById('ai-editorial-assistant');
    if (!root) {
      return;
    }

    var generateUrl = root.getAttribute('data-generate-url');
    var feedbackUrl = root.getAttribute('data-feedback-url');
    var actions = parseActions(root);
    var actionsById = {};
    actions.forEach(function (action) {
      actionsById[action.id] = action;
    });

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
    var generateBtn = document.querySelector('[data-ai-action="generate"]');
    var regenerateBtn = document.querySelector('[data-ai-action="regenerate"]');
    var useDraftBtn = document.getElementById('ai-assistant-use-draft');
    var rejectBtn = document.getElementById('ai-assistant-reject');
    var cancelBtns = document.querySelectorAll('[data-ai-assistant-cancel]');
    var actionButtons = document.querySelectorAll('[data-ai-action]');
    var ratingButtons = document.querySelectorAll('.ai-feedback-rating');
    var commentEl = document.getElementById('ai-feedback-comment');
    var busy = false;
    var versions = [];
    var activeIndex = null;
    var lastRequest = null;
    var selectedRating = '';

    function showError(message) {
      errorBox.textContent = message || 'Generation failed. Please try again.';
      errorBox.hidden = false;
    }

    function clearError() {
      errorBox.textContent = '';
      errorBox.hidden = true;
    }

    function selectedReasons() {
      var values = [];
      document
        .querySelectorAll('input[name="ai_feedback_reason"]:checked')
        .forEach(function (input) {
          values.push(input.value);
        });
      return values;
    }

    function resetFeedbackForm() {
      selectedRating = '';
      ratingButtons.forEach(function (btn) {
        btn.classList.remove('is-selected');
      });
      document
        .querySelectorAll('input[name="ai_feedback_reason"]')
        .forEach(function (input) {
          input.checked = false;
        });
      if (commentEl) {
        commentEl.value = '';
      }
    }

    function collectFeedbackPayload(extra) {
      var version = versions[activeIndex];
      if (!version || !version.generation_id) {
        return null;
      }
      var rating = selectedRating;
      if (extra && extra.rating) {
        rating = extra.rating;
      }
      if (!rating) {
        if (extra && extra.accepted) {
          rating = 'good';
        } else if (extra && extra.regenerated) {
          rating = 'needs_improvement';
        } else if (extra && extra.rejected) {
          rating = 'rejected';
        }
      }
      var payload = {
        generation_id: version.generation_id,
        prompt_task: version.prompt_task || 'post_generation',
        prompt_version: version.prompt_version || 'v1',
        provider: version.provider || '',
        model: version.model || '',
        language: version.language || '',
        rating: rating,
        reasons: selectedReasons(),
        comment: commentEl ? commentEl.value || '' : '',
        accepted: !!(extra && extra.accepted),
        regenerated: !!(extra && extra.regenerated),
        post_id: root.getAttribute('data-post-id') || '',
        action: (extra && extra.action) || '',
      };
      return payload;
    }

    function submitFeedback(extra) {
      if (!feedbackUrl) {
        return Promise.resolve(false);
      }
      var payload = collectFeedbackPayload(extra);
      if (!payload || !payload.rating) {
        return Promise.resolve(false);
      }
      return fetch(feedbackUrl, {
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
          return response.ok;
        })
        .catch(function () {
          return false;
        });
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
      if (regenerateBtn) {
        regenerateBtn.disabled = busy;
      }
      if (useDraftBtn) {
        useDraftBtn.disabled = busy;
      }
      if (rejectBtn) {
        rejectBtn.disabled = busy;
      }
    }

    function hidePreview() {
      preview.hidden = true;
      if (regenerateBtn) {
        regenerateBtn.disabled = true;
      }
      if (useDraftBtn) {
        useDraftBtn.disabled = true;
      }
      if (rejectBtn) {
        rejectBtn.disabled = true;
      }
    }

    function resetSession() {
      versions = [];
      activeIndex = null;
      lastRequest = null;
      clearError();
      hidePreview();
      renderVersions();
      resetFeedbackForm();
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
      if (generateBtn) {
        generateBtn.disabled = isBusy;
        generateBtn.textContent = isBusy ? '✨ Generating…' : '✨ Generate';
      }
      if (regenerateBtn) {
        regenerateBtn.disabled = isBusy || !versions.length;
      }
      if (useDraftBtn) {
        useDraftBtn.disabled = isBusy || activeIndex === null;
      }
      if (rejectBtn) {
        rejectBtn.disabled = isBusy || activeIndex === null;
      }
    }

    function addVersion(previewPayload) {
      versions.push(previewPayload);
      if (versions.length > MAX_VERSIONS) {
        versions = versions.slice(-MAX_VERSIONS);
      }
      activeIndex = versions.length - 1;
      resetFeedbackForm();
      showPreview(versions[activeIndex]);
      renderVersions();
    }

    function runAction(actionId) {
      var meta = actionsById[actionId];
      if (!meta || !meta.enabled || !IMPLEMENTED[actionId]) {
        return;
      }
      if (busy) {
        return;
      }
      clearError();

      var fromRegenerate = actionId === 'regenerate';
      var payload = fromRegenerate && lastRequest ? lastRequest : collectRequest();
      if (!payload.category_id) {
        showError('Please choose a category.');
        return;
      }

      var proceed = Promise.resolve(true);
      if (fromRegenerate && versions.length) {
        proceed = submitFeedback({
          regenerated: true,
          action: 'regenerate',
        });
      }

      lastRequest = payload;
      payload.action = actionId;
      setBusy(true);

      proceed
        .then(function () {
          return fetch(generateUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken(),
              Accept: 'application/json',
            },
            body: JSON.stringify(payload),
          });
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

    function useDraft() {
      if (activeIndex === null || !versions[activeIndex]) {
        return;
      }
      var version = versions[activeIndex];
      submitFeedback({
        accepted: true,
        action: 'use_draft',
      }).finally(function () {
        var title =
          version.title || form.querySelector('[name="title"]').value || '';
        setFieldValue('id_title', title);
        setFieldValue('id_content', version.body || '');
        setFieldValue('id_excerpt', version.summary || '');
        if (version.category_id) {
          setFieldValue('id_category', version.category_id);
        }
        setFieldValue('id_status', '0');
        closeModal();
      });
    }

    function rejectDraft() {
      if (activeIndex === null || !versions[activeIndex]) {
        return;
      }
      submitFeedback({
        rejected: true,
        rating: 'rejected',
        action: 'reject',
      }).finally(function () {
        resetFeedbackForm();
        showError('Feedback recorded as Rejected. Previous versions remain available.');
      });
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
    actionButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var actionId = btn.getAttribute('data-ai-action');
        runAction(actionId);
      });
    });
    ratingButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        selectedRating = btn.getAttribute('data-rating') || '';
        ratingButtons.forEach(function (other) {
          other.classList.toggle(
            'is-selected',
            other === btn
          );
        });
      });
    });
    if (useDraftBtn) {
      useDraftBtn.addEventListener('click', useDraft);
    }
    if (rejectBtn) {
      rejectBtn.addEventListener('click', rejectDraft);
    }
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && modal && !modal.hidden) {
        closeModal();
      }
    });
  });
})();
