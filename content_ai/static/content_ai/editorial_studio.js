(function () {
  const root = document.getElementById('editorial-studio');
  if (!root) return;

  const apiUrl = root.dataset.apiUrl;
  const urlInput = document.getElementById('es-news-url');
  const generateBtn = document.getElementById('es-generate');
  const statusEl = document.getElementById('es-status');
  const errorEl = document.getElementById('es-error');
  const results = document.getElementById('es-results');
  const sourceMeta = document.getElementById('es-source-meta');
  const titleEl = document.getElementById('es-title');
  const draftEl = document.getElementById('es-draft');
  const metadataEl = document.getElementById('es-metadata');

  function csrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
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
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderResult(payload) {
    const source = payload.source || {};
    const meta = payload.metadata || {};
    sourceMeta.innerHTML = [
      ['Source URL', source.url || meta.source_url || ''],
      ['Domain', source.domain || meta.source_domain || ''],
      ['Detected language', source.detected_language || meta.detected_language || ''],
      ['Source type', source.source_type || ''],
    ]
      .map(
        ([label, value]) =>
          `<div><strong>${label}:</strong> ${escapeHtml(String(value || '—'))}</div>`
      )
      .join('');
    titleEl.textContent = payload.title || '—';
    draftEl.textContent = payload.draft || '';
    metadataEl.textContent = JSON.stringify(
      {
        source_url: meta.source_url,
        source_domain: meta.source_domain,
        detected_language: meta.detected_language,
        workflow_stages: meta.workflow_stages,
        workflow_state: meta.workflow_state,
        provider: meta.provider,
        duration_ms: meta.duration_ms,
        prompt_version: meta.prompt_version,
      },
      null,
      2
    );
    results.hidden = false;
  }

  async function generateDraft() {
    setError('');
    results.hidden = true;
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
        body: JSON.stringify({ url: url }),
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
