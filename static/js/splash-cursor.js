/**
 * Splash Cursor Effect for Hero Section
 * 
 * Creates expanding ripple/splash particles when the cursor moves over the hero section.
 * Lightweight, performant, and mobile-friendly implementation.
 * 
 * CUSTOMIZATION:
 * - SPLASH_COLOR: Change the color of splash particles (default: rgba(255, 255, 255, 0.6))
 * - SPLASH_SIZE: Base size of splash particles in pixels (default: 20)
 * - SPLASH_COUNT: Number of particles per splash (default: 8)
 * - SPLASH_DURATION: Animation duration in milliseconds (default: 800)
 * - INTENSITY: Controls how often splashes appear (lower = more frequent, default: 50)
 */

(function() {
  'use strict';

  // Configuration - Easy to customize
  const CONFIG = {
    SPLASH_COLOR: 'rgba(255, 255, 255, 0.6)',  // White with transparency
    SPLASH_SIZE: 20,                             // Base size in pixels
    SPLASH_COUNT: 8,                              // Number of particles per splash
    SPLASH_DURATION: 800,                         // Animation duration in ms
    INTENSITY: 50,                                // Throttle delay in ms (lower = more frequent)
    MAX_PARTICLES: 50                             // Maximum particles on screen at once
  };

  let heroSection = null;
  let isInsideHero = false;
  let lastSplashTime = 0;
  let activeParticles = 0;
  let throttleTimer = null;

  /**
   * Initialize the splash cursor effect
   */
  function initSplashCursor() {
    // Find the hero section
    heroSection = document.querySelector('.hero-section');
    
    if (!heroSection) {
      return; // Hero section not found, exit gracefully
    }

    // Create container for splash particles
    const splashContainer = document.createElement('div');
    splashContainer.className = 'splash-cursor-container';
    splashContainer.setAttribute('aria-hidden', 'true'); // Hide from screen readers
    heroSection.appendChild(splashContainer);

    // Mouse move event - create splashes
    heroSection.addEventListener('mousemove', handleMouseMove, { passive: true });
    
    // Track when mouse enters/leaves hero section
    heroSection.addEventListener('mouseenter', function() {
      isInsideHero = true;
    });
    
    heroSection.addEventListener('mouseleave', function() {
      isInsideHero = false;
    });

    // Touch events for mobile (optional - creates splash on touch)
    heroSection.addEventListener('touchstart', handleTouch, { passive: true });
  }

  /**
   * Handle mouse movement and create splashes
   */
  function handleMouseMove(e) {
    if (!isInsideHero) return;

    // Throttle to prevent too many particles
    const now = Date.now();
    if (now - lastSplashTime < CONFIG.INTENSITY) {
      return;
    }

    // Check particle limit
    if (activeParticles >= CONFIG.MAX_PARTICLES) {
      return;
    }

    lastSplashTime = now;
    createSplash(e.clientX, e.clientY);
  }

  /**
   * Handle touch events for mobile
   */
  function handleTouch(e) {
    if (e.touches.length > 0) {
      const touch = e.touches[0];
      const rect = heroSection.getBoundingClientRect();
      const x = touch.clientX;
      const y = touch.clientY;
      
      // Check if touch is within hero section bounds
      if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
        createSplash(x, y);
      }
    }
  }

  /**
   * Create a splash effect at the given coordinates
   */
  function createSplash(x, y) {
    const container = heroSection.querySelector('.splash-cursor-container');
    if (!container) return;

    const rect = heroSection.getBoundingClientRect();
    const relativeX = x - rect.left;
    const relativeY = y - rect.top;

    // Create multiple particles for the splash
    for (let i = 0; i < CONFIG.SPLASH_COUNT; i++) {
      if (activeParticles >= CONFIG.MAX_PARTICLES) break;

      const particle = document.createElement('div');
      particle.className = 'splash-particle';
      
      // Random angle for particle direction
      const angle = (Math.PI * 2 * i) / CONFIG.SPLASH_COUNT;
      const distance = CONFIG.SPLASH_SIZE * (2 + Math.random() * 2);
      
      // Random size variation
      const size = CONFIG.SPLASH_SIZE * (0.5 + Math.random() * 0.5);
      particle.style.width = size + 'px';
      particle.style.height = size + 'px';
      
      // Set initial position
      particle.style.left = relativeX + 'px';
      particle.style.top = relativeY + 'px';
      
      // Calculate end position
      const endX = relativeX + Math.cos(angle) * distance;
      const endY = relativeY + Math.sin(angle) * distance;
      
      // Set CSS custom properties for animation
      particle.style.setProperty('--end-x', endX + 'px');
      particle.style.setProperty('--end-y', endY + 'px');
      particle.style.setProperty('--splash-duration', CONFIG.SPLASH_DURATION + 'ms');
      particle.style.setProperty('--splash-color', CONFIG.SPLASH_COLOR);
      
      container.appendChild(particle);
      activeParticles++;

      // Remove particle after animation
      setTimeout(function() {
        if (particle.parentNode) {
          particle.parentNode.removeChild(particle);
          activeParticles--;
        }
      }, CONFIG.SPLASH_DURATION);
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSplashCursor);
  } else {
    initSplashCursor();
  }
})();

