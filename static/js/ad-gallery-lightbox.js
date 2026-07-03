document.addEventListener('DOMContentLoaded', function () {
  var root = document.querySelector('[data-ad-gallery]');
  var slidesNode = document.getElementById('ad-gallery-slides-json');
  if (!root || !slidesNode) {
    return;
  }

  var slides = [];
  try {
    slides = JSON.parse(slidesNode.textContent);
  } catch (error) {
    return;
  }

  if (!slides.length) {
    return;
  }

  var lightbox = document.getElementById('ad-gallery-lightbox');
  var lightboxImage = document.getElementById('ad-gallery-lightbox-image');
  var lightboxCounter = document.getElementById('ad-gallery-lightbox-counter');
  var captionNode = document.getElementById('ad-gallery-lightbox-caption');
  var currentIndex = 0;
  var lastFocusedElement = null;

    function renderSlide(index) {
    if (!lightboxImage || index < 0 || index >= slides.length) {
      return;
    }
    currentIndex = index;
    var slide = slides[index];
    if (!lightboxImage.getAttribute('src')) {
      lightboxImage.loading = 'eager';
    } else {
      lightboxImage.loading = 'lazy';
    }
    lightboxImage.src = slide.url;
    lightboxImage.alt = slide.alt || '';
    if (captionNode) {
      captionNode.textContent = slide.alt || '';
    }
    if (lightboxCounter) {
      lightboxCounter.textContent = (index + 1) + ' / ' + slides.length;
    }
    root.querySelectorAll('.ad-detail-gallery__thumb').forEach(function (thumb, thumbIndex) {
      thumb.classList.toggle('is-active', thumbIndex === index);
    });
  }

  function openLightbox(index) {
    if (!lightbox) {
      return;
    }
    lastFocusedElement = document.activeElement;
    renderSlide(index);
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.classList.add('ad-gallery-lightbox-open');
    var closeButton = lightbox.querySelector('.ad-gallery-lightbox__close');
    if (closeButton) {
      closeButton.focus();
    }
  }

  function closeLightbox() {
    if (!lightbox || !lightboxImage) {
      return;
    }
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('ad-gallery-lightbox-open');
    lightboxImage.src = '';
    lightboxImage.alt = '';
    if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
      lastFocusedElement.focus();
    }
  }

  function showPrevious() {
    var nextIndex = currentIndex - 1;
    if (nextIndex < 0) {
      nextIndex = slides.length - 1;
    }
    renderSlide(nextIndex);
  }

  function showNext() {
    var nextIndex = currentIndex + 1;
    if (nextIndex >= slides.length) {
      nextIndex = 0;
    }
    renderSlide(nextIndex);
  }

  root.querySelectorAll('.js-ad-gallery-open').forEach(function (trigger) {
    trigger.addEventListener('click', function () {
      var index = parseInt(trigger.getAttribute('data-gallery-index') || '0', 10);
      openLightbox(index);
    });
  });

  if (lightbox) {
    lightbox.querySelectorAll('.js-ad-gallery-close').forEach(function (button) {
      button.addEventListener('click', closeLightbox);
    });
    var prevButton = lightbox.querySelector('.js-ad-gallery-prev');
    var nextButton = lightbox.querySelector('.js-ad-gallery-next');
    if (prevButton) {
      prevButton.addEventListener('click', showPrevious);
    }
    if (nextButton) {
      nextButton.addEventListener('click', showNext);
    }
  }

  document.addEventListener('keydown', function (event) {
    if (!lightbox || !lightbox.classList.contains('is-open')) {
      return;
    }
    if (event.key === 'Escape') {
      closeLightbox();
    }
    if (event.key === 'ArrowRight') {
      showPrevious();
    }
    if (event.key === 'ArrowLeft') {
      showNext();
    }
  });

  var touchStartX = 0;
  if (lightbox) {
    lightbox.addEventListener('touchstart', function (event) {
      touchStartX = event.changedTouches[0].screenX;
    }, { passive: true });
    lightbox.addEventListener('touchend', function (event) {
      var touchEndX = event.changedTouches[0].screenX;
      var delta = touchEndX - touchStartX;
      if (Math.abs(delta) < 40) {
        return;
      }
      if (delta > 0) {
        showPrevious();
      } else {
        showNext();
      }
    }, { passive: true });
  }
});
