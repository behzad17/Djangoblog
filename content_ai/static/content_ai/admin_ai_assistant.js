/* AI Editorial Assistant — polished Admin modal (UX only). */
(function () {
  'use strict';

  var MAX_VERSIONS = 3;
  var IMPLEMENTED = { generate: true, regenerate: true };
  var STATUS_STEPS = [
    'Preparing request…',
    'Building prompt…',
    'Generating…',
    'Almost done…',
  ];

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

  function escapeHtml(text) {
    return String(text == null ? '' : text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function formatTime(date) {
    try {
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch (err) {
      return '';
    }
  }

  function renderMarkdownLite(source) {
    var text = String(source == null ? '' : source).replace(/\r\n/g, '\n');
    if (!text.trim()) {
      return '';
    }

    var codeBlocks = [];
    text = text.replace(/```([\s\S]*?)```/g, function (_, code) {
      var index = codeBlocks.length;
      codeBlocks.push(
        '<pre><code>' + escapeHtml(code.replace(/^\n/, '')) + '</code></pre>'
      );
      return '\n%%CODEBLOCK' + index + '%%\n';
    });

    var lines = text.split('\n');
    var html = [];
    var inUl = false;
    var inOl = false;
    var inTable = false;

    function closeLists() {
      if (inUl) {
        html.push('</ul>');
        inUl = false;
      }
      if (inOl) {
        html.push('</ol>');
        inOl = false;
      }
    }

    function closeTable() {
      if (inTable) {
        html.push('</tbody></table>');
        inTable = false;
      }
    }

    function inlineFormat(line) {
      var escaped = escapeHtml(line);
      escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
      escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      return escaped;
    }

    lines.forEach(function (line) {
      var codeMatch = line.match(/^%%CODEBLOCK(\d+)%%$/);
      if (codeMatch) {
        closeLists();
        closeTable();
        html.push(codeBlocks[Number(codeMatch[1])] || '');
        return;
      }

      if (/^\s*\|?.+\|.+\|\s*$/.test(line) && line.indexOf('|') !== -1) {
        closeLists();
        var cells = line
          .replace(/^\|/, '')
          .replace(/\|$/, '')
          .split('|')
          .map(function (cell) {
            return cell.trim();
          });
        if (/^:?-{3,}:?$/.test(cells.join('').replace(/\|/g, '')) ||
            cells.every(function (cell) {
              return /^:?-{3,}:?$/.test(cell);
            })) {
          return;
        }
        if (!inTable) {
          html.push('<table><tbody>');
          inTable = true;
          html.push(
            '<tr>' +
              cells
                .map(function (cell) {
                  return '<th>' + inlineFormat(cell) + '</th>';
                })
                .join('') +
              '</tr>'
          );
        } else {
          html.push(
            '<tr>' +
              cells
                .map(function (cell) {
                  return '<td>' + inlineFormat(cell) + '</td>';
                })
                .join('') +
              '</tr>'
          );
        }
        return;
      }
      closeTable();

      var heading = line.match(/^(#{1,3})\s+(.*)$/);
      if (heading) {
        closeLists();
        var level = heading[1].length;
        html.push(
          '<h' + level + '>' + inlineFormat(heading[2]) + '</h' + level + '>'
        );
        return;
      }

      var ul = line.match(/^\s*[-*]\s+(.*)$/);
      if (ul) {
        closeTable();
        if (inOl) {
          html.push('</ol>');
          inOl = false;
        }
        if (!inUl) {
          html.push('<ul>');
          inUl = true;
        }
        html.push('<li>' + inlineFormat(ul[1]) + '</li>');
        return;
      }

      var ol = line.match(/^\s*\d+\.\s+(.*)$/);
      if (ol) {
        closeTable();
        if (inUl) {
          html.push('</ul>');
          inUl = false;
        }
        if (!inOl) {
          html.push('<ol>');
          inOl = true;
        }
        html.push('<li>' + inlineFormat(ol[1]) + '</li>');
        return;
      }

      closeLists();
      if (!line.trim()) {
        return;
      }
      html.push('<p>' + inlineFormat(line) + '</p>');
    });

    closeLists();
    closeTable();
    return html.join('');
  }

  function wordDiffHtml(previousText, nextText) {
    var previous = String(previousText || '').split(/(\s+)/);
    var next = String(nextText || '').split(/(\s+)/);
    var max = Math.max(previous.length, next.length);
    var parts = [];
    for (var i = 0; i < max; i += 1) {
      var a = previous[i];
      var b = next[i];
      if (a === b) {
        if (b != null) {
          parts.push(escapeHtml(b));
        }
      } else {
        if (a != null && a !== '') {
          parts.push('<span class="ai-diff-del">' + escapeHtml(a) + '</span>');
        }
        if (b != null && b !== '') {
          parts.push('<span class="ai-diff-add">' + escapeHtml(b) + '</span>');
        }
      }
    }
    return parts.join('') || '<em>No textual difference detected.</em>';
  }

  function telemetrySummary(telemetry) {
    var data = telemetry && typeof telemetry === 'object' ? telemetry : {};
    var tokens = data.token_usage;
    var tokenText = '—';
    if (tokens && typeof tokens === 'object') {
      try {
        tokenText = JSON.stringify(tokens);
      } catch (err) {
        tokenText = String(tokens);
      }
    }
    var cost =
      data.estimated_cost == null || data.estimated_cost === ''
        ? '—'
        : String(data.estimated_cost);
    var duration =
      data.duration_ms == null || data.duration_ms === ''
        ? '—'
        : data.duration_ms + ' ms';
    return [
      ['Provider', data.provider || '—'],
      ['Model', data.model || '—'],
      ['Duration', duration],
      ['Tokens', tokenText],
      ['Estimated cost', cost],
    ];
  }

  function parseActions(root) {
    var raw = root.getAttribute('data-actions') || '[]';
    try {
      return JSON.parse(raw);
    } catch (err) {
      return [];
    }
  }

  function copyText(text) {
    var value = text == null ? '' : String(text);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(value);
    }
    return new Promise(function (resolve, reject) {
      var area = document.createElement('textarea');
      area.value = value;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.left = '-9999px';
      document.body.appendChild(area);
      area.select();
      try {
        document.execCommand('copy');
        resolve();
      } catch (err) {
        reject(err);
      } finally {
        document.body.removeChild(area);
      }
    });
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
    var fieldRoot = document.getElementById('ai-assistant-form');
    var errorBox = document.getElementById('ai-assistant-error');
    var loadingEl = document.getElementById('ai-assistant-loading');
    var statusText = document.getElementById('ai-assistant-status-text');
    var preview = document.getElementById('ai-assistant-preview');
    var previewTitle = document.getElementById('ai-preview-title');
    var previewSummary = document.getElementById('ai-preview-summary');
    var previewBody = document.getElementById('ai-preview-body');
    var previewTelemetry = document.getElementById('ai-preview-telemetry');
    var telemetrySummaryEl = document.getElementById(
      'ai-preview-telemetry-summary'
    );
    var diffDetails = document.getElementById('ai-preview-diff-details');
    var diffBody = document.getElementById('ai-preview-diff');
    var versionsEl = document.getElementById('ai-assistant-versions');
    var generateBtn = document.querySelector('[data-ai-action="generate"]');
    var regenerateBtn = document.querySelector('[data-ai-action="regenerate"]');
    var useDraftBtn = document.getElementById('ai-assistant-use-draft');
    var rejectBtn = document.getElementById('ai-assistant-reject');
    var cancelBtns = document.querySelectorAll('[data-ai-assistant-cancel]');
    var actionButtons = document.querySelectorAll('[data-ai-action]');
    var ratingButtons = document.querySelectorAll('.ai-feedback-rating');
    var commentEl = document.getElementById('ai-feedback-comment');
    var copyButtons = document.querySelectorAll('[data-ai-copy]');
    var busy = false;
    var versions = [];
    var activeIndex = null;
    var lastRequest = null;
    var selectedRating = '';
    var statusTimer = null;
    var statusStep = 0;
    var lastFocused = null;

    function showError(message) {
      errorBox.textContent = message || 'Generation failed. Please try again.';
      errorBox.hidden = false;
    }

    function clearError() {
      errorBox.textContent = '';
      errorBox.hidden = true;
    }

    function focusableElements() {
      return Array.prototype.slice
        .call(
          modal.querySelectorAll(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          )
        )
        .filter(function (el) {
          return el.offsetParent !== null || el === document.activeElement;
        });
    }

    function trapFocus(event) {
      if (event.key !== 'Tab' || modal.hidden) {
        return;
      }
      var items = focusableElements();
      if (!items.length) {
        return;
      }
      var first = items[0];
      var last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
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
        btn.setAttribute('aria-pressed', 'false');
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
      return {
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
          'ai-version-card' + (index === activeIndex ? ' is-active' : '');
        btn.setAttribute('aria-pressed', index === activeIndex ? 'true' : 'false');
        btn.setAttribute(
          'aria-label',
          'Version ' +
            (index + 1) +
            (index === activeIndex ? ', current' : '') +
            (version.accepted ? ', accepted' : '')
        );

        var label = document.createElement('span');
        label.className = 'ai-version-label';
        label.textContent = 'Version ' + (index + 1);
        btn.appendChild(label);

        var time = document.createElement('span');
        time.className = 'ai-version-meta';
        time.textContent = version.createdLabel || '';
        btn.appendChild(time);

        var badges = document.createElement('div');
        badges.className = 'ai-version-badges';
        if (index === activeIndex) {
          var current = document.createElement('span');
          current.className = 'ai-version-badge';
          current.textContent = 'Current';
          badges.appendChild(current);
        }
        if (version.accepted) {
          var accepted = document.createElement('span');
          accepted.className = 'ai-version-badge';
          accepted.textContent = 'Accepted';
          badges.appendChild(accepted);
        }
        btn.appendChild(badges);

        btn.addEventListener('click', function () {
          selectVersion(index);
        });
        versionsEl.appendChild(btn);
      });
    }

    function renderTelemetry(version) {
      var rows = telemetrySummary(version.telemetry);
      telemetrySummaryEl.innerHTML = '';
      rows.forEach(function (row) {
        var dt = document.createElement('dt');
        dt.textContent = row[0];
        var dd = document.createElement('dd');
        dd.textContent = row[1];
        telemetrySummaryEl.appendChild(dt);
        telemetrySummaryEl.appendChild(dd);
      });
      if (previewTelemetry) {
        try {
          previewTelemetry.textContent = JSON.stringify(
            version.telemetry || {},
            null,
            2
          );
        } catch (err) {
          previewTelemetry.textContent = String(version.telemetry || '');
        }
      }
    }

    function renderDiff(version, previous) {
      if (!diffDetails || !diffBody) {
        return;
      }
      if (!previous) {
        diffDetails.hidden = true;
        diffBody.innerHTML = '';
        return;
      }
      diffDetails.hidden = false;
      diffBody.innerHTML = wordDiffHtml(previous.body || '', version.body || '');
    }

    function showPreview(version) {
      preview.hidden = false;
      previewTitle.textContent = version.title || '(untitled)';
      previewSummary.innerHTML = renderMarkdownLite(version.summary || '');
      previewBody.innerHTML = renderMarkdownLite(version.body || '');
      renderTelemetry(version);
      var previous =
        activeIndex > 0 ? versions[activeIndex - 1] : null;
      renderDiff(version, previous);
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
      if (diffDetails) {
        diffDetails.hidden = true;
      }
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

    function selectVersion(index) {
      if (index < 0 || index >= versions.length) {
        return;
      }
      activeIndex = index;
      showPreview(versions[activeIndex]);
      renderVersions();
    }

    function resetAssistantFields() {
      if (!fieldRoot) {
        return;
      }
      var title = fieldRoot.querySelector('[name="title"]');
      var category = fieldRoot.querySelector('[name="category_id"]');
      var language = fieldRoot.querySelector('[name="language"]');
      var context = fieldRoot.querySelector('[name="context"]');
      var instructions = fieldRoot.querySelector('[name="instructions"]');
      var initialTitle = root.getAttribute('data-initial-title') || '';
      var initialCategory = root.getAttribute('data-initial-category') || '';
      if (title) {
        title.value = initialTitle;
      }
      if (category) {
        category.value = initialCategory;
      }
      if (language) {
        language.value = 'sv';
      }
      if (context) {
        context.value = '';
      }
      if (instructions) {
        instructions.value = '';
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
      stopLoading();
      resetAssistantFields();
    }

    function openModal() {
      lastFocused = document.activeElement;
      resetSession();
      modal.hidden = false;
      backdrop.hidden = false;
      document.body.classList.add('ai-assistant-open');
      var titleField = document.getElementById('ai-field-title');
      if (titleField) {
        titleField.focus();
      }
    }

    function closeModal() {
      modal.hidden = true;
      backdrop.hidden = true;
      document.body.classList.remove('ai-assistant-open');
      resetSession();
      if (lastFocused && typeof lastFocused.focus === 'function') {
        lastFocused.focus();
      }
    }

    function collectRequest() {
      // Modal lives inside Django Admin's <form>; assistant fields must not be a nested
      // <form> (browsers drop it → container is null). Resolve the field container each call.
      var container =
        fieldRoot || document.getElementById('ai-assistant-form');
      if (!container) {
        console.error('AI Assistant container not found.');
        showError('Assistant form is unavailable. Reload the page and try again.');
        return null;
      }
      var categorySelect = container.querySelector('[name="category_id"]');
      if (!categorySelect) {
        showError('Category field is missing.');
        return null;
      }
      var categoryId = categorySelect.value;
      var categoryName = '';
      if (categorySelect.selectedIndex >= 0) {
        categoryName = categorySelect.options[categorySelect.selectedIndex].text;
      }
      var titleEl = container.querySelector('[name="title"]');
      var languageEl = container.querySelector('[name="language"]');
      var contextEl = container.querySelector('[name="context"]');
      var instructionsEl = container.querySelector('[name="instructions"]');
      return {
        title: (titleEl && titleEl.value) || '',
        category_id: categoryId ? Number(categoryId) : null,
        category: categoryName,
        language: (languageEl && languageEl.value) || '',
        context: (contextEl && contextEl.value) || '',
        instructions: (instructionsEl && instructionsEl.value) || '',
        post_id: root.getAttribute('data-post-id') || '',
      };
    }

    function startLoading() {
      if (!loadingEl) {
        return;
      }
      loadingEl.hidden = false;
      statusStep = 0;
      if (statusText) {
        statusText.textContent = STATUS_STEPS[0];
      }
      clearInterval(statusTimer);
      statusTimer = setInterval(function () {
        statusStep = Math.min(statusStep + 1, STATUS_STEPS.length - 1);
        if (statusText) {
          statusText.textContent = STATUS_STEPS[statusStep];
        }
      }, 900);
    }

    function stopLoading() {
      clearInterval(statusTimer);
      statusTimer = null;
      if (loadingEl) {
        loadingEl.hidden = true;
      }
    }

    function setBusy(isBusy) {
      busy = isBusy;
      if (isBusy) {
        startLoading();
      } else {
        stopLoading();
      }
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
      actionButtons.forEach(function (btn) {
        var actionId = btn.getAttribute('data-ai-action');
        var meta = actionsById[actionId];
        if (!meta || !meta.enabled) {
          return;
        }
        if (actionId === 'generate') {
          return;
        }
        if (actionId === 'regenerate') {
          btn.disabled = isBusy || !versions.length;
        }
      });
    }

    function addVersion(previewPayload) {
      var stamped = Object.assign({}, previewPayload, {
        createdAt: new Date(),
        createdLabel: formatTime(new Date()),
        accepted: false,
      });
      versions.push(stamped);
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
      if (!payload) {
        return;
      }
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
      version.accepted = true;
      renderVersions();
      submitFeedback({
        accepted: true,
        action: 'use_draft',
      }).finally(function () {
        var titleInput =
          (fieldRoot && fieldRoot.querySelector('[name="title"]')) ||
          document.getElementById('ai-field-title');
        var title =
          version.title ||
          (titleInput && titleInput.value) ||
          '';
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
        showError(
          'Feedback recorded as Rejected. Previous versions remain available.'
        );
      });
    }

    function handleCopy(kind) {
      if (activeIndex === null || !versions[activeIndex]) {
        return;
      }
      var version = versions[activeIndex];
      var text = '';
      if (kind === 'title') {
        text = version.title || '';
      } else if (kind === 'summary') {
        text = version.summary || '';
      } else if (kind === 'body') {
        text = version.body || '';
      } else {
        text =
          (version.title || '') +
          '\n\n' +
          (version.summary || '') +
          '\n\n' +
          (version.body || '');
      }
      copyText(text).catch(function () {
        showError('Could not copy to clipboard.');
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
          var selected = other === btn;
          other.classList.toggle('is-selected', selected);
          other.setAttribute('aria-pressed', selected ? 'true' : 'false');
        });
      });
    });
    copyButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        handleCopy(btn.getAttribute('data-ai-copy'));
      });
    });
    if (useDraftBtn) {
      useDraftBtn.addEventListener('click', useDraft);
    }
    if (rejectBtn) {
      rejectBtn.addEventListener('click', rejectDraft);
    }

    document.addEventListener('keydown', function (event) {
      if (modal.hidden) {
        return;
      }
      if (event.key === 'Escape') {
        event.preventDefault();
        closeModal();
        return;
      }
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        runAction('generate');
        return;
      }
      if (event.key === 'ArrowLeft' && versions.length) {
        event.preventDefault();
        selectVersion(Math.max(0, (activeIndex == null ? 0 : activeIndex) - 1));
        return;
      }
      if (event.key === 'ArrowRight' && versions.length) {
        event.preventDefault();
        selectVersion(
          Math.min(
            versions.length - 1,
            (activeIndex == null ? 0 : activeIndex) + 1
          )
        );
        return;
      }
      trapFocus(event);
    });
  });
})();
