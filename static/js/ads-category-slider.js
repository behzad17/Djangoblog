/**
 * Ads Category Slider - Center-Mode Navigation
 * 
 * Scoped JavaScript for center-mode category slider.
 * Uses data attributes, supports RTL, accessible, performant.
 */

(function() {
  'use strict';

  /**
   * Initialize all slider instances on the page
   */
  function initAdsCategorySliders() {
    const sliders = document.querySelectorAll('[data-ads-slider]');
    sliders.forEach(slider => {
      new AdsCategorySlider(slider);
    });
  }

  /**
   * AdsCategorySlider Class
   */
  class AdsCategorySlider {
    constructor(root) {
      this.root = root;
      this.track = root.querySelector('[data-ads-track]');
      this.cards = Array.from(root.querySelectorAll('[data-ads-card]'));
      this.prevBtn = root.querySelector('[data-ads-prev]');
      this.nextBtn = root.querySelector('[data-ads-next]');
      
      if (!this.track || this.cards.length === 0) {
        return; // Invalid slider structure
      }

      // Detect RTL
      this.isRTL = document.documentElement.dir === 'rtl' || 
                   document.documentElement.getAttribute('dir') === 'rtl';

      // Current center index
      this.currentIndex = 0;

      // Check if active category exists
      const activeCard = this.cards.find(card => card.getAttribute('aria-current') === 'page');
      if (activeCard) {
        this.currentIndex = this.cards.indexOf(activeCard);
      }

      // Mark JS as enabled
      this.root.classList.add('js-enabled');

      // Initialize
      this.init();
    }

    init() {
      // Center the active card on load
      this.centerCard(this.currentIndex, false); // No animation on initial load

      // Attach event listeners
      this.attachEvents();

      // Update button states
      this.updateButtons();
    }

    /**
     * Attach event listeners
     */
    attachEvents() {
      // Navigation buttons
      if (this.prevBtn) {
        this.prevBtn.addEventListener('click', () => this.prev());
        this.prevBtn.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.prev();
          }
        });
      }

      if (this.nextBtn) {
        this.nextBtn.addEventListener('click', () => this.next());
        this.nextBtn.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.next();
          }
        });
      }

      // Scroll event (for manual scrolling)
      let scrollTimeout;
      this.track.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          this.updateCenterFromScroll();
        }, 100);
      }, { passive: true });

      // Card click (allow navigation, but also update center if needed)
      this.cards.forEach((card, index) => {
        card.addEventListener('click', (e) => {
          // Allow link navigation, but update center state
          this.currentIndex = index;
          this.updateCenter();
        });
      });

      // Keyboard navigation (arrow keys)
      this.root.addEventListener('keydown', (e) => {
        if (e.target.closest('[data-ads-card]')) {
          if (e.key === 'ArrowLeft') {
            e.preventDefault();
            if (this.isRTL) {
              this.next();
            } else {
              this.prev();
            }
          } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            if (this.isRTL) {
              this.prev();
            } else {
              this.next();
            }
          } else if (e.key === 'Home') {
            e.preventDefault();
            this.goTo(0);
          } else if (e.key === 'End') {
            e.preventDefault();
            this.goTo(this.cards.length - 1);
          }
        }
      });

      // Resize handler (recenter on resize)
      let resizeTimeout;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
          this.centerCard(this.currentIndex, false);
        }, 250);
      }, { passive: true });
    }

    /**
     * Navigate to previous card
     */
    prev() {
      if (this.currentIndex > 0) {
        this.goTo(this.currentIndex - 1);
      }
    }

    /**
     * Navigate to next card
     */
    next() {
      if (this.currentIndex < this.cards.length - 1) {
        this.goTo(this.currentIndex + 1);
      }
    }

    /**
     * Navigate to specific card index
     */
    goTo(index) {
      if (index >= 0 && index < this.cards.length) {
        this.currentIndex = index;
        this.centerCard(index, true);
        this.updateButtons();
        this.announceCard(index);
      }
    }

    /**
     * Center a specific card
     */
    centerCard(index, animate = true) {
      if (index < 0 || index >= this.cards.length) {
        return;
      }

      const card = this.cards[index];
      const cardRect = card.getBoundingClientRect();
      const trackRect = this.track.getBoundingClientRect();
      
      // Calculate scroll position to center the card
      const cardLeft = card.offsetLeft;
      const cardWidth = card.offsetWidth;
      const trackWidth = this.track.offsetWidth;
      const scrollLeft = cardLeft - (trackWidth / 2) + (cardWidth / 2);

      // Scroll to center
      if (animate) {
        this.track.scrollTo({
          left: scrollLeft,
          behavior: 'smooth'
        });
      } else {
        this.track.scrollLeft = scrollLeft;
      }

      // Update center state
      this.updateCenter();
    }

    /**
     * Update center state classes
     */
    updateCenter() {
      this.cards.forEach((card, index) => {
        if (index === this.currentIndex) {
          card.classList.add('is-center');
        } else {
          card.classList.remove('is-center');
        }
      });
    }

    /**
     * Update center from scroll position (for manual scrolling)
     */
    updateCenterFromScroll() {
      const trackRect = this.track.getBoundingClientRect();
      const trackCenter = trackRect.left + trackRect.width / 2;

      let closestIndex = 0;
      let closestDistance = Infinity;

      this.cards.forEach((card, index) => {
        const cardRect = card.getBoundingClientRect();
        const cardCenter = cardRect.left + cardRect.width / 2;
        const distance = Math.abs(cardCenter - trackCenter);

        if (distance < closestDistance) {
          closestDistance = distance;
          closestIndex = index;
        }
      });

      if (closestIndex !== this.currentIndex) {
        this.currentIndex = closestIndex;
        this.updateCenter();
        this.updateButtons();
        this.announceCard(closestIndex);
      }
    }

    /**
     * Update prev/next button states
     */
    updateButtons() {
      if (this.prevBtn) {
        this.prevBtn.disabled = this.currentIndex === 0;
      }
      if (this.nextBtn) {
        this.nextBtn.disabled = this.currentIndex === this.cards.length - 1;
      }
    }

    /**
     * Announce current card to screen readers
     */
    announceCard(index) {
      const card = this.cards[index];
      const cardName = card.querySelector('.slider-card-name')?.textContent || '';
      const liveRegion = this.root.querySelector('[aria-live]');
      
      if (liveRegion && cardName) {
        liveRegion.textContent = `Category ${index + 1} of ${this.cards.length}: ${cardName}`;
      }
    }
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAdsCategorySliders);
  } else {
    initAdsCategorySliders();
  }

})();

