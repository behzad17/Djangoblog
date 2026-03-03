document.addEventListener('DOMContentLoaded', function () {
  var lightbox = document.getElementById('photo-lightbox');
  if (!lightbox) {
    return;
  }

  var lightboxImage = document.getElementById('photo-lightbox-image');
  var closeButton = lightbox.querySelector('.photo-lightbox-close');
  var backdrop = lightbox.querySelector('.photo-lightbox-backdrop');

  function openLightbox(src, alt) {
    if (!lightboxImage) {
      return;
    }
    lightboxImage.src = src;
    lightboxImage.alt = alt || '';
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
  }

  function closeLightbox() {
    if (!lightboxImage) {
      return;
    }
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
    lightboxImage.src = '';
    lightboxImage.alt = '';
  }

  // Attach click handlers to hero and extra images
  var triggers = document.querySelectorAll('.js-photo-lightbox-trigger');
  triggers.forEach(function (img) {
    img.addEventListener('click', function () {
      if (!img.src) {
        return;
      }
      openLightbox(img.src, img.alt);
    });
  });

  if (closeButton) {
    closeButton.addEventListener('click', function () {
      closeLightbox();
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', function () {
      closeLightbox();
    });
  }

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      closeLightbox();
    }
  });
});

