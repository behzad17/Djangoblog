/**
 * Peyvand FAQ Accordion
 * Clean, mobile-first implementation for /about/member-guide/
 * 
 * Features:
 * - Mobile tap/click to toggle
 * - Only one item open at a time
 * - Proper aria-expanded management
 * - Keyboard accessible (Enter/Space)
 * - Optional hover enhancement for desktop
 */

(function() {
  'use strict';

  function initPeyvandFAQ() {
    const faq = document.querySelector('.peyvand-faq');
    if (!faq) {
      return; // FAQ not on this page
    }

    const items = faq.querySelectorAll('.peyvand-faq__item');
    const questions = faq.querySelectorAll('.peyvand-faq__q');
    const answers = faq.querySelectorAll('.peyvand-faq__a');

    if (questions.length === 0 || answers.length === 0) {
      return;
    }

    // Close all items except the specified one
    function closeAllExcept(exceptIndex) {
      items.forEach((item, index) => {
        if (index !== exceptIndex) {
          const q = questions[index];
          const a = answers[index];
          if (q && a) {
            q.setAttribute('aria-expanded', 'false');
            a.setAttribute('hidden', '');
            item.classList.remove('is-open');
          }
        }
      });
    }

    // Toggle a single FAQ item
    function toggleItem(index) {
      const question = questions[index];
      const answer = answers[index];
      const item = items[index];

      if (!question || !answer || !item) {
        return;
      }

      const isExpanded = question.getAttribute('aria-expanded') === 'true';

      if (isExpanded) {
        // Close
        question.setAttribute('aria-expanded', 'false');
        answer.setAttribute('hidden', '');
        item.classList.remove('is-open');
      } else {
        // Open (close others first)
        closeAllExcept(index);
        question.setAttribute('aria-expanded', 'true');
        answer.removeAttribute('hidden');
        item.classList.add('is-open');
      }
    }

    // Attach click handlers to each question button
    questions.forEach((question, index) => {
      if (!question) return;

      // Ensure button type
      if (question.tagName === 'BUTTON' && !question.type) {
        question.type = 'button';
      }

      // Click handler (works on mobile and desktop)
      question.addEventListener('click', function(e) {
        e.preventDefault();
        toggleItem(index);
      });

      // Keyboard support
      question.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          toggleItem(index);
        }
      });
    });

    // Optional: Hover enhancement for desktop (non-touch devices only)
    const supportsHover = window.matchMedia('(hover: hover)').matches;
    if (supportsHover) {
      items.forEach((item, index) => {
        const question = questions[index];
        const answer = answers[index];

        if (!question || !answer) return;

        question.addEventListener('mouseenter', function() {
          closeAllExcept(index);
          question.setAttribute('aria-expanded', 'true');
          answer.removeAttribute('hidden');
          item.classList.add('is-open');
        });

        item.addEventListener('mouseleave', function() {
          question.setAttribute('aria-expanded', 'false');
          answer.setAttribute('hidden', '');
          item.classList.remove('is-open');
        });
      });
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPeyvandFAQ);
  } else {
    initPeyvandFAQ();
  }
})();

