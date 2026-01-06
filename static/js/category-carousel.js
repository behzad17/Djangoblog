/**
 * 3D Category Carousel / Coverflow
 * 
 * A 3D card carousel for displaying categories with coverflow effect.
 * Supports RTL layout, touch gestures, mouse wheel, and keyboard navigation.
 */

(function() {
  'use strict';

  function initCategoryCarousel() {
    const carousel = document.querySelector('#categoryCarousel');
    if (!carousel) {
      return; // Carousel not on this page
    }

    const container = carousel.querySelector('.category-carousel-container');
    const cards = Array.from(carousel.querySelectorAll('.category-carousel-card'));
    const prevBtn = carousel.querySelector('.category-carousel-nav.prev');
    const nextBtn = carousel.querySelector('.category-carousel-nav.next');

    if (cards.length === 0) {
      return; // No cards to display
    }

    let currentIndex = 0;
    const totalCards = cards.length;
    const isRTL = document.documentElement.dir === 'rtl' || 
                  document.documentElement.getAttribute('dir') === 'rtl';

    // Get visible card count and spacing configuration based on breakpoint
    function getCarouselConfig() {
      const width = window.innerWidth;
      if (width >= 992) {
        // Desktop: 7 cards, tighter spacing for better clickability
        return {
          visibleCount: 7,
          halfVisible: 3,
          cardWidth: 185, // Match CSS desktop width
          spacingFactor: 0.85, // Reduced from 1.15 - cards closer together for better clickability
          scaleCurve: [1.0, 0.88, 0.78, 0.70], // Non-linear scale for offsets 0, 1, 2, 3
          translateZCurve: [0, -80, -150, -200], // Depth for offsets 0, 1, 2, 3
          rotateYCurve: [0, 18, 32, 42], // Rotation angles for offsets 0, 1, 2, 3
          opacityCurve: [1.0, 0.9, 0.75, 0.6] // Opacity for offsets 0, 1, 2, 3
        };
      } else if (width >= 768) {
        // Tablet: 5 cards, tighter spacing
        return {
          visibleCount: 5,
          halfVisible: 2,
          cardWidth: 170,
          spacingFactor: 0.9, // Reduced from 1.1
          scaleCurve: [1.0, 0.85, 0.72],
          translateZCurve: [0, -70, -130],
          rotateYCurve: [0, 20, 38],
          opacityCurve: [1.0, 0.85, 0.65]
        };
      } else {
        // Mobile: 3 cards, tighter spacing
        return {
          visibleCount: 3,
          halfVisible: 1,
          cardWidth: 144,
          spacingFactor: 1.0,
          scaleCurve: [1.0, 0.82],
          translateZCurve: [0, -60],
          rotateYCurve: [0, 25],
          opacityCurve: [1.0, 0.8]
        };
      }
    }

    // Update card positions with non-linear scaling and consistent spacing
    function updateCards() {
      const config = getCarouselConfig();
      const baseSpacing = config.cardWidth * config.spacingFactor;

      cards.forEach((card, index) => {
        // Calculate wrapped offset (handles circular carousel)
        let diff = index - currentIndex;
        // Handle wrapping for circular carousel
        if (diff > totalCards / 2) {
          diff -= totalCards;
        } else if (diff < -totalCards / 2) {
          diff += totalCards;
        }

        const absOffset = Math.abs(diff);
        const isVisible = absOffset <= config.halfVisible;

        if (!isVisible) {
          // Hide cards beyond visible range
          card.style.transform = '';
          card.style.opacity = '0';
          card.style.pointerEvents = 'none';
          card.style.zIndex = '1';
          card.classList.remove('active');
          return;
        }

        // Remove old classes
        card.classList.remove('active', 'prev-1', 'prev-2', 'prev-3', 'next-1', 'next-2', 'next-3', 'hidden');
        
        // Special handling for center card (diff === 0)
        if (diff === 0) {
          // Center card: no rotation, no translation, full scale, fully visible
          const transformStr = 'translateX(0) translateZ(0) rotateY(0deg) scale(1.0)';
          card.style.transform = transformStr;
          card.style.setProperty('--card-transform', transformStr);
          card.style.opacity = '1.0';
          card.style.zIndex = '10';
          card.style.pointerEvents = 'auto';
          card.classList.add('active');
          return; // Skip further processing for center card
        }

        // Get transform values from curves for side cards
        const scale = config.scaleCurve[absOffset] || config.scaleCurve[config.scaleCurve.length - 1];
        const translateZ = config.translateZCurve[absOffset] || config.translateZCurve[config.translateZCurve.length - 1];
        const rotateY = config.rotateYCurve[absOffset] || config.rotateYCurve[config.rotateYCurve.length - 1];
        const opacity = config.opacityCurve[absOffset] || config.opacityCurve[config.opacityCurve.length - 1];

        // Calculate translateX: consistent spacing based on offset
        const translateX = diff * baseSpacing;
        
        // Determine rotation direction (negative for left, positive for right)
        const rotation = diff < 0 ? rotateY : -rotateY;
        
        // Stable z-index: center card highest, decreases with distance
        const zIndex = 10 - absOffset;

        // Build transform string
        let transformStr;
        if (isRTL) {
          // RTL: flip translateX direction
          transformStr = `translateX(${-translateX}px) translateZ(${translateZ}px) rotateY(${-rotation}deg) scale(${scale})`;
        } else {
          transformStr = `translateX(${translateX}px) translateZ(${translateZ}px) rotateY(${rotation}deg) scale(${scale})`;
        }
        
        // Apply transforms
        card.style.transform = transformStr;
        // Store base transform in CSS variable for hover enhancement
        card.style.setProperty('--card-transform', transformStr);
        card.style.opacity = opacity.toString();
        card.style.zIndex = zIndex.toString();
        card.style.pointerEvents = 'auto';
      });

      // Update ARIA live region
      const liveRegion = carousel.querySelector('.category-carousel-live');
      if (liveRegion) {
        const currentCard = cards[currentIndex];
        const cardName = currentCard.querySelector('.category-carousel-card-name')?.textContent || '';
        liveRegion.textContent = `Category ${currentIndex + 1} of ${totalCards}: ${cardName}`;
      }
    }

    // Navigate to next card
    function next() {
      currentIndex = (currentIndex + 1) % totalCards;
      updateCards();
    }

    // Navigate to previous card
    function prev() {
      currentIndex = (currentIndex - 1 + totalCards) % totalCards;
      updateCards();
    }

    // Navigate to specific index
    function goTo(index) {
      if (index >= 0 && index < totalCards) {
        currentIndex = index;
        updateCards();
      }
    }

    // Touch gesture support
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;

    container.addEventListener('touchstart', function(e) {
      touchStartX = e.changedTouches[0].screenX;
      touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    container.addEventListener('touchend', function(e) {
      touchEndX = e.changedTouches[0].screenX;
      touchEndY = e.changedTouches[0].screenY;
      handleSwipe();
    }, { passive: true });

    function handleSwipe() {
      const deltaX = touchEndX - touchStartX;
      const deltaY = touchEndY - touchStartY;

      // Only handle horizontal swipes (ignore vertical scrolling)
      if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        if (isRTL) {
          // RTL: swipe right = next, swipe left = prev
          if (deltaX > 0) {
            next();
          } else {
            prev();
          }
        } else {
          // LTR: swipe left = next, swipe right = prev
          if (deltaX < 0) {
            next();
          } else {
            prev();
          }
        }
      }
    }

    // Mouse wheel support
    let wheelTimeout;
    container.addEventListener('wheel', function(e) {
      e.preventDefault();
      
      clearTimeout(wheelTimeout);
      wheelTimeout = setTimeout(function() {
        const delta = e.deltaY;
        if (delta > 0) {
          next();
        } else {
          prev();
        }
      }, 50);
    }, { passive: false });

    // Keyboard navigation
    carousel.addEventListener('keydown', function(e) {
      if (e.target.closest('.category-carousel-card')) {
        // Only handle when a card is focused
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          if (isRTL) {
            next();
          } else {
            prev();
          }
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          if (isRTL) {
            prev();
          } else {
            next();
          }
        } else if (e.key === 'Home') {
          e.preventDefault();
          goTo(0);
        } else if (e.key === 'End') {
          e.preventDefault();
          goTo(totalCards - 1);
        }
      }
    });

    // Button navigation
    if (prevBtn) {
      prevBtn.addEventListener('click', function() {
        if (isRTL) {
          next();
        } else {
          prev();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', function() {
        if (isRTL) {
          prev();
        } else {
          next();
        }
      });
    }

    // Click on cards - allow direct navigation to category page
    cards.forEach((card, index) => {
      card.addEventListener('click', function(e) {
        // Always allow the link to work - cards are clickable to navigate to category
        // The carousel navigation is handled by buttons, wheel, and keyboard
        // Users should be able to click any visible card to go to that category
        // No preventDefault - let the <a> tag work normally
      });
    });

    // Auto-rotate (optional - can be disabled)
    let autoRotateInterval;
    function startAutoRotate() {
      // Disabled by default - uncomment to enable
      // autoRotateInterval = setInterval(next, 5000);
    }

    function stopAutoRotate() {
      if (autoRotateInterval) {
        clearInterval(autoRotateInterval);
        autoRotateInterval = null;
      }
    }

    // Pause auto-rotate on hover/interaction
    carousel.addEventListener('mouseenter', stopAutoRotate);
    carousel.addEventListener('mouseleave', startAutoRotate);
    carousel.addEventListener('focusin', stopAutoRotate);
    carousel.addEventListener('focusout', startAutoRotate);

    // Handle window resize to update card positions
    let resizeTimeout;
    window.addEventListener('resize', function() {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(function() {
        updateCards();
      }, 150);
    });

    // Initialize
    updateCards();
    startAutoRotate();
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCategoryCarousel);
  } else {
    initCategoryCarousel();
  }
})();

