/**
 * jQuery Alias Fix - MUST load before any Summernote scripts
 * 
 * This script sets $ and jQuery as aliases for django.jQuery
 * It uses synchronous blocking to ensure aliases are set before scripts execute.
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
    if (!setupJQueryAlias()) {
        // Block synchronously until django.jQuery is available
        // This ensures aliases are set before any other scripts execute
        var startTime = Date.now();
        var maxWait = 5000; // 5 seconds max wait
        
        while (!setupJQueryAlias() && (Date.now() - startTime) < maxWait) {
            // Synchronous blocking wait - check every 1ms
            // This is a busy-wait, but necessary to ensure aliases are set
            var checkTime = Date.now();
            while (Date.now() - checkTime < 1) {
                // Busy wait for 1ms
            }
        }
        
        // If still not ready after blocking, fall back to async polling
        if (!setupJQueryAlias()) {
            var attempts = 0;
            var maxAttempts = 500;
            var interval = setInterval(function() {
                if (setupJQueryAlias() || attempts++ >= maxAttempts) {
                    clearInterval(interval);
                }
            }, 10);
        }
    }
})();

