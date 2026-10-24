(function () {
  'use strict';
  // Bump only when a significant terms update warrants another notice.
  var VERSION = '2026-10-24';
  var KEY = 'peyvand.termsNotice';
  var RETURN_KEY = 'peyvand.termsNotice.return';
  var notice = document.getElementById('terms-notice');
  var returnPanel = document.getElementById('terms-return');
  var banner = document.getElementById('adBanner');
  var bannerHidden = false;

  function read(storage, key) {
    try { return JSON.parse(window[storage].getItem(key)); } catch (e) { return null; }
  }
  function write(storage, key, value) {
    try { window[storage].setItem(key, JSON.stringify(value)); } catch (e) {}
  }
  function remember(status) {
    var value = { version: VERSION, status: status };
    write('localStorage', KEY, value);
    // Session fallback if persistent storage is unavailable.
    write('sessionStorage', KEY, value);
  }
  function hide() {
    if (notice) notice.hidden = true;
    if (banner && bannerHidden) {
      banner.hidden = false;
      bannerHidden = false;
    }
  }
  function safeReturn(path) {
    if (typeof path !== 'string') return null;
    try {
      var url = new URL(path, window.location.origin);
      if (url.origin !== window.location.origin || !/^\/(?!\/)/.test(path)) return null;
      if (url.pathname === '/about/terms/' || url.pathname === '/about/integritetspolicy/') return null;
      return url.pathname + url.search + url.hash;
    } catch (e) { return null; }
  }

  if (returnPanel) {
    // Only visitors who followed the notice get a return/reading action.
    var destination = safeReturn(read('sessionStorage', RETURN_KEY));
    if (destination) {
      var returnLink = returnPanel.querySelector('a');
      returnLink.href = destination;
      returnPanel.hidden = false;
      returnLink.addEventListener('click', function () {
        remember('read'); // Explicit action; visiting or scrolling is not acceptance.
        try { window.sessionStorage.removeItem(RETURN_KEY); } catch (e) {}
      });
    }
    return;
  }
  if (!notice) return;
  var saved = read('localStorage', KEY);
  var sessionSaved = read('sessionStorage', KEY);
  function current(value) {
    return value && value.version === VERSION &&
      ['dismissed', 'acknowledged', 'read'].indexOf(value.status) !== -1;
  }
  if (current(saved) || current(sessionSaved)) return;

  notice.querySelectorAll('[data-terms-dismiss]').forEach(function (button) {
    button.addEventListener('click', function () {
      remember(button.getAttribute('data-terms-dismiss'));
      hide();
    });
  });
  notice.querySelector('[data-terms-read]').addEventListener('click', function () {
    write('sessionStorage', RETURN_KEY, window.location.pathname + window.location.search + window.location.hash);
    remember('dismissed'); // Opening the terms does not claim they were read.
    hide();
  });
  notice.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      remember('dismissed');
      hide();
    }
  });
  window.addEventListener('storage', function (event) {
    if (event.key === KEY && current(read('localStorage', KEY))) hide();
  });
  // Don't stack the existing guest banner with the first-visit notice.
  if (banner && !banner.hidden) { banner.hidden = true; bannerHidden = true; }
  notice.hidden = false;
})();
