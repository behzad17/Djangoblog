/**
 * jQuery Alias Fix for Summernote in Django Admin
 * 
 * This script defines $ and jQuery as aliases for django.jQuery
 * BEFORE Summernote scripts load. This fixes "$ is not a function" errors.
 * 
 * Must be loaded before django-summernote's scripts.
 */
(function() {
    'use strict';
    
    // Function to setup jQuery aliases
    function setupJQueryAlias() {
        if (typeof django !== 'undefined' && django.jQuery) {
            // Define $ and jQuery as aliases for django.jQuery
            window.$ = window.jQuery = django.jQuery;
            return true;
        }
        return false;
    }
    
    // Try to setup immediately
    if (!setupJQueryAlias()) {
        // If django.jQuery not available yet, poll until it is
        // This handles cases where this script loads before Django admin's jQuery
        var attempts = 0;
        var maxAttempts = 100; // Try for up to 1 second (100 * 10ms)
        var interval = setInterval(function() {
            if (setupJQueryAlias() || attempts++ >= maxAttempts) {
                clearInterval(interval);
            }
        }, 10);
    }
})();

