(function () {
  const root = document.getElementById('editorial-studio');
  if (!root) return;

  const apiUrl = root.dataset.apiUrl;
  const urlInput = document.getElementById('es-news-url');
  const generateBtn = document.getElementById('es-generate');
  const statusEl = document.getElementById('es-status');
  const errorEl = document.getElementById('es-error');
  const results = document.getElementById('es-results');
  const metadataPanel = document.getElementById('es-metadata-panel');
  const metadataEl = document.getElementById('es-metadata');
  const titleEl = document.getElementById('es-title');
  const leadEl = document.getElementById('es-lead');
  const bodyEl = document.getElementById('es-body');
  const summaryEl = document.getElementById('es-summary');
  const categoryEl = document.getElementById('es-category');
  const tagsEl = document.getElementById('es-tags');

  function csrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function selectedValue(name, fallback) {
    const checked = document.querySelector(
      'input[name="' + name + '"]:checked'
    );
    return checked ? checked.value : fallback;
  }

  function setError(message) {
    if (!message) {
      errorEl.hidden = true;
      errorEl.textContent = '';
      return;
    }
    errorEl.hidden = false;
    errorEl.textContent = message;
  }

  function setBusy(busy, message) {
    generateBtn.disabled = busy;
    if (busy) {
      statusEl.textContent = message || 'Generating Persian draft…';
    } else if (message) {
      statusEl.textContent = message;
    } else {
      statusEl.textContent = '';
    }
  }

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderMetadata(payload) {
    const meta = payload.metadata || {};
    const rows = [
      ['Source', payload.source_name || meta.source_name || '—'],
      ['Source URL', payload.source_url || meta.source_url || '—'],
      [
        'Language',
        payload.output_language ||
          payload.language ||
          meta.language ||
          '—',
      ],
      [
        'Source language',
        payload.source_language || meta.detected_language || '—',
      ],
      [
        'Workflow',
        (payload.workflow_stages || meta.workflow_stages || []).join(' → ') ||
          '—',
      ],
      ['Provider', payload.provider || meta.provider || '—'],
      [
        'Duration',
        payload.duration_ms != null
          ? payload.duration_ms + ' ms'
          : meta.duration_ms != null
            ? meta.duration_ms + ' ms'
            : '—',
      ],
      ['Content type', payload.content_type || meta.content_type || '—'],
      ['Output', payload.output_mode || meta.output_mode || '—'],
    ];
    metadataEl.innerHTML = rows
      .map(
        ([label, value]) =>
          `<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</div>`
      )
      .join('');
    metadataPanel.hidden = false;
  }

  function renderResult(payload) {
    titleEl.textContent = payload.title || '—';
    leadEl.textContent = payload.lead || '—';
    bodyEl.textContent = payload.body || payload.draft || '';
    summaryEl.textContent =
      payload.short_summary || payload.summary || '—';
    categoryEl.textContent = payload.suggested_category || '—';
    const tags = payload.suggested_tags || [];
    tagsEl.textContent = tags.length ? tags.join(', ') : '—';
    results.hidden = false;
    renderMetadata(payload);
  }

  async function generateDraft() {
    setError('');
    results.hidden = true;
    metadataPanel.hidden = true;
    const url = (urlInput.value || '').trim();
    if (!url) {
      setError('Please paste a news article URL.');
      return;
    }
    setBusy(true);
    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken(),
        },
        body: JSON.stringify({
          url: url,
          content_type: selectedValue('es-content-type', 'auto'),
          output_mode: selectedValue('es-output-mode', 'publish_ready'),
        }),
        credentials: 'same-origin',
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        const message =
          (data.error && data.error.message) ||
          'News import failed. Please try another URL.';
        setError(message);
        setBusy(false);
        return;
      }
      renderResult(data.result || {});
      setBusy(false, 'Draft ready.');
    } catch (err) {
      setError('Could not reach Editorial Studio. Check your connection.');
      setBusy(false);
    }
  }

  generateBtn.addEventListener('click', generateDraft);
  urlInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      generateDraft();
    }
  });
})();
