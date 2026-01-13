/**
 * jQuery Alias Fix - MUST load before any Summernote scripts
 * 
 * This script sets $ and jQuery as aliases for django.jQuery
 * Uses Object.defineProperty to intercept access even before django.jQuery loads.
 * 
 * CRITICAL: This must load BEFORE:
 * - jquery.iframe-transport.js
 * - jquery.fileupload.js  
 * - summernote.min.js
 */
(function() {
    'use strict';
    
    // Use Object.defineProperty to create getters that return django.jQuery
    // This intercepts ALL access to $ and jQuery, even if django.jQuery isn't loaded yet
    // Once django.jQuery is available, we'll replace getters with direct values
    
    var jqueryAvailable = false;
    
    function checkJQuery() {
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined' && django.jQuery) {
            jqueryAvailable = true;
            try {
                // Replace getters with direct values for better performance
                delete window.$;
                delete window.jQuery;
                window.$ = window.jQuery = django.jQuery;
                return true;
            } catch(e) {
                // If deletion fails, getters will handle it
            }
        }
        return false;
    }
    
    // Try immediately
    checkJQuery();
    
    // Define getters if jQuery not available yet
    if (!jqueryAvailable) {
        try {
            // Define $ as a getter
            if (!window.hasOwnProperty('$')) {
                Object.defineProperty(window, '$', {
                    get: function() {
                        if (checkJQuery()) {
                            return window.$;
                        }
                        return undefined;
                    },
                    configurable: true,
                    enumerable: true
                });
            }
            
            // Define jQuery as a getter
            if (!window.hasOwnProperty('jQuery')) {
                Object.defineProperty(window, 'jQuery', {
                    get: function() {
                        if (checkJQuery()) {
                            return window.jQuery;
                        }
                        return undefined;
                    },
                    configurable: true,
                    enumerable: true
                });
            }
        } catch(e) {
            // Fallback: direct assignment when available
        }
    }
    
    // Poll to replace getters with direct values once available
    var attempts = 0;
    var maxAttempts = 1000;
    var pollInterval = setInterval(function() {
        if (checkJQuery() || attempts++ >= maxAttempts) {
            clearInterval(pollInterval);
        }
    }, 10);
})();

