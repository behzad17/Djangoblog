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

    // Get visible card count based on breakpoint
    function getVisibleCount() {
      const width = window.innerWidth;
      if (width >= 992) {
        return 7; // Desktop: 7 cards (center + 3 each side)
      } else if (width >= 768) {
        return 5; // Tablet: 5 cards (center + 2 each side)
      } else {
        return 3; // Mobile: 3 cards (center + 1 each side)
      }
    }

    // Update card positions based on current index and visible count
    function updateCards() {
      const visibleCount = getVisibleCount();
      const halfVisible = Math.floor(visibleCount / 2); // 3 for desktop, 2 for tablet, 1 for mobile

      cards.forEach((card, index) => {
        // Remove all position classes
        card.classList.remove('active', 'prev-1', 'prev-2', 'prev-3', 'next-1', 'next-2', 'next-3', 'hidden');

        const diff = index - currentIndex;

        if (diff === 0) {
          card.classList.add('active');
        } else if (diff === -1) {
          card.classList.add('prev-1');
        } else if (diff === -2 && halfVisible >= 2) {
          card.classList.add('prev-2');
        } else if (diff === -3 && halfVisible >= 3) {
          card.classList.add('prev-3');
        } else if (diff === 1) {
          card.classList.add('next-1');
        } else if (diff === 2 && halfVisible >= 2) {
          card.classList.add('next-2');
        } else if (diff === 3 && halfVisible >= 3) {
          card.classList.add('next-3');
        } else if (Math.abs(diff) > halfVisible) {
          card.classList.add('hidden');
        }
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

    // Click on side cards to navigate
    cards.forEach((card, index) => {
      card.addEventListener('click', function(e) {
        // Only navigate if clicking on a non-active card
        if (!card.classList.contains('active')) {
          e.preventDefault();
          goTo(index);
        }
        // If active card, let the link work normally
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

