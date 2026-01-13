/**
 * jQuery Alias Fix - MUST load before any Summernote scripts
 * 
 * This script sets $ and jQuery as aliases for django.jQuery
 * It runs immediately and polls until django.jQuery is available.
 * 
 * CRITICAL: This must load BEFORE:
 * - jquery.iframe-transport.js
 * - jquery.fileupload.js  
 * - summernote.min.js
 */
(function() {
    'use strict';
    
    // Function to setup jQuery aliases
    function setupJQueryAlias() {
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined' && django.jQuery) {
            try {
                // Set aliases - allow overwrite
                window.$ = django.jQuery;
                window.jQuery = django.jQuery;
                return true;
            } catch(e) {
                // Ignore errors
            }
        }
        return false;
    }
    
    // Try immediately
    var jqueryReady = setupJQueryAlias();
    
    // If not ready, poll aggressively until it is
    // This is critical - scripts will load immediately after this
    if (!jqueryReady) {
        var attempts = 0;
        var maxAttempts = 1000; // 10 seconds - very aggressive
        var interval = setInterval(function() {
            if (setupJQueryAlias()) {
                jqueryReady = true;
                clearInterval(interval);
            } else if (attempts++ >= maxAttempts) {
                clearInterval(interval);
                console.error('jQuery alias fix: django.jQuery not available after 10 seconds');
            }
        }, 10);
    }
})();

