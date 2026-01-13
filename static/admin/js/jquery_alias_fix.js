/**
 * jQuery Alias Fix and Summernote Initialization Delay
 * 
 * This script:
 * 1. Defines $ and jQuery as aliases for django.jQuery
 * 2. Intercepts Summernote initialization and delays it until jQuery is ready
 * 
 * Must be loaded before django-summernote's scripts.
 */
(function() {
    'use strict';
    
    // Function to setup jQuery aliases
    function setupJQueryAlias() {
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined' && django.jQuery) {
            // Define $ and jQuery as aliases for django.jQuery
            window.$ = window.jQuery = django.jQuery;
            return true;
        }
        return false;
    }
    
    // Try to setup immediately
    var jqueryReady = setupJQueryAlias();
    
    // If not ready, poll until it is
    if (!jqueryReady) {
        var attempts = 0;
        var maxAttempts = 500; // 5 seconds
        var interval = setInterval(function() {
            if (setupJQueryAlias()) {
                jqueryReady = true;
                clearInterval(interval);
                // Trigger any waiting Summernote initializations
                if (window._summernoteQueue && window._summernoteQueue.length > 0) {
                    window._summernoteQueue.forEach(function(fn) {
                        try {
                            fn();
                        } catch(e) {
                            console.error('Error initializing Summernote:', e);
                        }
                    });
                    window._summernoteQueue = [];
                }
            } else if (attempts++ >= maxAttempts) {
                clearInterval(interval);
            }
        }, 10);
    }
    
    // Intercept Summernote initialization
    // Store original summernote function if it exists
    var originalSummernote = null;
    var summernoteIntercepted = false;
    
    // Function to intercept Summernote when it loads
    function interceptSummernote() {
        if (summernoteIntercepted) return;
        
        // Wait for Summernote to be defined
        if (typeof window.$ !== 'undefined' && window.$ && window.$.fn) {
            // Check if summernote is already defined
            if (window.$.fn.summernote) {
                // Summernote already loaded, wrap it
                originalSummernote = window.$.fn.summernote;
                window.$.fn.summernote = function(options) {
                    // Ensure jQuery is ready before initializing
                    if (jqueryReady || setupJQueryAlias()) {
                        return originalSummernote.call(this, options);
                    } else {
                        // Queue for later
                        if (!window._summernoteQueue) {
                            window._summernoteQueue = [];
                        }
                        var self = this;
                        window._summernoteQueue.push(function() {
                            originalSummernote.call(self, options);
                        });
                    }
                };
                summernoteIntercepted = true;
            }
        }
    }
    
    // Poll to intercept Summernote when it loads
    var interceptAttempts = 0;
    var interceptInterval = setInterval(function() {
        interceptSummernote();
        if (summernoteIntercepted || interceptAttempts++ >= 200) {
            clearInterval(interceptInterval);
        }
    }, 25);
})();

