document.addEventListener('DOMContentLoaded', () => {
  const rotators = document.querySelectorAll('[data-discussions-rotator]');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  rotators.forEach((rotator) => {
    const titles = Array.from(rotator.querySelectorAll('[data-discussion-title]'));
    if (titles.length < 2 || reduceMotion) return;

    let currentIndex = 0;
    let intervalId = null;

    const showTitle = (nextIndex) => {
      titles[currentIndex].classList.remove('is-active');
      titles[currentIndex].setAttribute('aria-hidden', 'true');

      currentIndex = nextIndex;
      titles[currentIndex].classList.add('is-active');
      titles[currentIndex].removeAttribute('aria-hidden');
    };

    const start = () => {
      if (intervalId !== null) return;
      intervalId = window.setInterval(() => {
        showTitle((currentIndex + 1) % titles.length);
      }, 3000);
    };

    const stop = () => {
      if (intervalId === null) return;
      window.clearInterval(intervalId);
      intervalId = null;
    };

    const link = rotator.closest('.hero-discussions-cta');
    if (link) {
      link.addEventListener('mouseenter', stop);
      link.addEventListener('mouseleave', start);
      link.addEventListener('focusin', stop);
      link.addEventListener('focusout', start);
    }

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stop();
      else start();
    });

    start();
  });
});
