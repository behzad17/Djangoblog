/**
 * Ads Category Slider - Image-Based Center-Mode Navigation
 * 
 * Based on the example pattern with [active] attribute and flex-basis expansion.
 * Scoped JavaScript, RTL support, accessible, performant.
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
      this.wrap = this.track?.parentElement; // slider wrapper
      this.cards = Array.from(root.querySelectorAll('[data-ads-card]'));
      this.prevBtn = root.querySelector('[data-ads-prev]');
      this.nextBtn = root.querySelector('[data-ads-next]');
      this.dotsBox = root.querySelector('[data-ads-dots]');
      
      if (!this.track || this.cards.length === 0) {
        return; // Invalid slider structure
      }

      // Detect RTL
      this.isRTL = document.documentElement.dir === 'rtl' || 
                   document.documentElement.getAttribute('dir') === 'rtl';

      // Detect mobile
      this.isMobile = () => window.matchMedia('(max-width: 767px)').matches;

      // Current active index
      this.current = 0;

      // Check if active category exists
      const activeCard = this.cards.find(card => card.hasAttribute('active'));
      if (activeCard) {
        this.current = this.cards.indexOf(activeCard);
      }

      // Create dots
      this.createDots();

      // Mark JS as enabled
      this.root.classList.add('js-enabled');

      // Initialize
      this.init();
    }

    /**
     * Create dot indicators
     */
    createDots() {
      if (!this.dotsBox) return;
      
      this.cards.forEach((_, i) => {
        const dot = document.createElement('button');
        dot.className = 'ads-slider-dot';
        dot.type = 'button';
        dot.setAttribute('aria-label', `Go to category ${i + 1}`);
        dot.onclick = () => this.activate(i, true);
        this.dotsBox.appendChild(dot);
      });
      
      this.dots = Array.from(this.dotsBox.children);
      
      // Hide dots on mobile
      if (this.isMobile()) {
        this.dotsBox.hidden = true;
      }
    }

    init() {
      // Center the active card on load
      this.center(this.current);
      this.toggleUI(this.current);

      // Attach event listeners
      this.attachEvents();
    }

    /**
     * Center a card in the viewport
     */
    center(i) {
      if (i < 0 || i >= this.cards.length) return;
      
      const card = this.cards[i];
      const axis = this.isMobile() ? 'top' : 'left';
      const size = this.isMobile() ? 'clientHeight' : 'clientWidth';
      const start = this.isMobile() ? card.offsetTop : card.offsetLeft;
      
      const scrollTarget = start - (this.wrap[size] / 2 - card[size] / 2);
      
      this.wrap.scrollTo({
        [axis]: scrollTarget,
        behavior: 'smooth'
      });
    }

    /**
     * Toggle UI state (active attribute, dots, buttons)
     */
    toggleUI(i) {
      this.cards.forEach((c, k) => {
        if (k === i) {
          c.setAttribute('active', '');
        } else {
          c.removeAttribute('active');
        }
      });
      
      if (this.dots) {
        this.dots.forEach((d, k) => {
          d.classList.toggle('active', k === i);
        });
      }
      
      if (this.prevBtn) {
        this.prevBtn.disabled = i === 0;
      }
      
      if (this.nextBtn) {
        this.nextBtn.disabled = i === this.cards.length - 1;
      }
    }

    /**
     * Activate a specific card
     */
    activate(i, scroll) {
      if (i === this.current) return;
      if (i < 0 || i >= this.cards.length) return;
      
      this.current = i;
      this.toggleUI(i);
      
      if (scroll) {
        this.center(i);
      }
      
      // Announce to screen readers
      this.announceCard(i);
    }

    /**
     * Navigate by step
     */
    go(step) {
      const newIndex = Math.min(Math.max(this.current + step, 0), this.cards.length - 1);
      this.activate(newIndex, true);
    }

    /**
     * Announce current card to screen readers
     */
    announceCard(index) {
      const card = this.cards[index];
      const cardName = card.querySelector('.ads-project-card__title')?.textContent || '';
      const liveRegion = this.root.querySelector('[aria-live]');
      
      if (liveRegion && cardName) {
        liveRegion.textContent = `Category ${index + 1} of ${this.cards.length}: ${cardName}`;
      }
    }

    /**
     * Attach event listeners
     */
    attachEvents() {
      // Navigation buttons
      if (this.prevBtn) {
        this.prevBtn.addEventListener('click', () => {
          if (this.isRTL) {
            this.go(1);
          } else {
            this.go(-1);
          }
        });
      }

      if (this.nextBtn) {
        this.nextBtn.addEventListener('click', () => {
          if (this.isRTL) {
            this.go(-1);
          } else {
            this.go(1);
          }
        });
      }

      // Keyboard navigation
      this.root.addEventListener('keydown', (e) => {
        if (e.target.closest('[data-ads-card]')) {
          if (['ArrowRight', 'ArrowDown'].includes(e.key)) {
            e.preventDefault();
            this.go(1);
          }
          if (['ArrowLeft', 'ArrowUp'].includes(e.key)) {
            e.preventDefault();
            this.go(-1);
          }
          if (e.key === 'Home') {
            e.preventDefault();
            this.activate(0, true);
          }
          if (e.key === 'End') {
            e.preventDefault();
            this.activate(this.cards.length - 1, true);
          }
        }
      }, { passive: true });

      // Card hover (desktop only)
      this.cards.forEach((card, i) => {
        card.addEventListener('mouseenter', () => {
          if (window.matchMedia('(hover: hover)').matches) {
            this.activate(i, true);
          }
        });
        
        // Card click - allow link navigation but also update active state
        card.addEventListener('click', (e) => {
          // If clicking the button, let it navigate
          if (e.target.closest('.ads-project-card__btn')) {
            return; // Allow navigation
          }
          // Otherwise, activate this card
          this.activate(i, true);
        });
      });

      // Touch swipe
      let sx = 0, sy = 0;
      this.track.addEventListener('touchstart', (e) => {
        sx = e.touches[0].clientX;
        sy = e.touches[0].clientY;
      }, { passive: true });

      this.track.addEventListener('touchend', (e) => {
        const dx = e.changedTouches[0].clientX - sx;
        const dy = e.changedTouches[0].clientY - sy;
        
        if (this.isMobile() ? Math.abs(dy) > 60 : Math.abs(dx) > 60) {
          const direction = this.isMobile() ? dy : dx;
          this.go(direction > 0 ? -1 : 1);
        }
      }, { passive: true });

      // Resize handler
      window.addEventListener('resize', () => {
        this.center(this.current);
        // Hide/show dots based on mobile state
        if (this.dotsBox) {
          this.dotsBox.hidden = this.isMobile();
        }
      }, { passive: true });

      // Scroll handler (for manual scrolling)
      let scrollTimeout;
      this.track.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          this.updateActiveFromScroll();
        }, 100);
      }, { passive: true });
    }

    /**
     * Update active card from scroll position
     */
    updateActiveFromScroll() {
      const trackRect = this.wrap.getBoundingClientRect();
      const trackCenter = this.isMobile() 
        ? trackRect.top + trackRect.height / 2
        : trackRect.left + trackRect.width / 2;

      let closestIndex = 0;
      let closestDistance = Infinity;

      this.cards.forEach((card, index) => {
        const cardRect = card.getBoundingClientRect();
        const cardCenter = this.isMobile()
          ? cardRect.top + cardRect.height / 2
          : cardRect.left + cardRect.width / 2;
        const distance = Math.abs(cardCenter - trackCenter);

        if (distance < closestDistance) {
          closestDistance = distance;
          closestIndex = index;
        }
      });

      if (closestIndex !== this.current) {
        this.activate(closestIndex, false); // Don't scroll, just update UI
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
