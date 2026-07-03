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
  var layerA = document.getElementById('ad-gallery-lightbox-image-a');
  var layerB = document.getElementById('ad-gallery-lightbox-image-b');
  var lightboxCounter = document.getElementById('ad-gallery-lightbox-counter');
  var captionNode = document.getElementById('ad-gallery-lightbox-caption');
  var thumbStrip = root.querySelector('.ad-detail-gallery__thumbs');
  var currentIndex = 0;
  var lastFocusedElement = null;
  var activeLayer = layerA;
  var inactiveLayer = layerB;
  var slideRequestId = 0;
  var loadedUrls = Object.create(null);
  var hideTimeouts = Object.create(null);
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fadeDurationMs = prefersReducedMotion ? 0 : 200;

  function loadSlideImage(url) {
    if (!url) {
      return Promise.reject(new Error('missing url'));
    }
    if (loadedUrls[url]) {
      return Promise.resolve(url);
    }
    return new Promise(function (resolve, reject) {
      var image = new Image();
      image.decoding = 'async';
      image.onload = function () {
        loadedUrls[url] = true;
        resolve(url);
      };
      image.onerror = function () {
        reject(new Error('failed to load ' + url));
      };
      image.src = url;
    });
  }

  function preloadAdjacentSlides(index) {
    if (!slides.length) {
      return;
    }
    loadSlideImage(slides[index].url).catch(function () {});
    loadSlideImage(slides[(index + 1) % slides.length].url).catch(function () {});
    loadSlideImage(slides[(index - 1 + slides.length) % slides.length].url).catch(function () {});
  }

  function syncActiveThumb(index) {
    var thumbs = root.querySelectorAll('.ad-detail-gallery__thumb');
    thumbs.forEach(function (thumb, thumbIndex) {
      var isActive = thumbIndex === index;
      thumb.classList.toggle('is-active', isActive);
      thumb.setAttribute('aria-selected', isActive ? 'true' : 'false');
      thumb.setAttribute('tabindex', isActive ? '0' : '-1');
      if (isActive) {
        thumb.scrollIntoView({
          behavior: prefersReducedMotion ? 'auto' : 'smooth',
          block: 'nearest',
          inline: 'center',
        });
      }
    });
  }

  function updateSlideMeta(index, slide) {
    if (captionNode) {
      var caption = slide.alt || '';
      captionNode.textContent = caption;
      captionNode.setAttribute('aria-hidden', caption ? 'false' : 'true');
    }
    if (lightboxCounter) {
      lightboxCounter.textContent = (index + 1) + ' / ' + slides.length;
    }
    syncActiveThumb(index);
  }

  function showLayer(layer, slide) {
    if (!layer) {
      return;
    }
    layer.hidden = false;
    layer.removeAttribute('hidden');
    layer.src = slide.url;
    layer.alt = slide.alt || '';
    layer.classList.add('is-visible');
  }

  function hideLayer(layer) {
    if (!layer) {
      return;
    }
    var timeoutKey = layer.id || String(layer);
    if (hideTimeouts[timeoutKey]) {
      window.clearTimeout(hideTimeouts[timeoutKey]);
    }
    layer.classList.remove('is-visible');
    hideTimeouts[timeoutKey] = window.setTimeout(function () {
      if (!layer.classList.contains('is-visible')) {
        layer.hidden = true;
        layer.setAttribute('hidden', 'hidden');
      }
      hideTimeouts[timeoutKey] = null;
    }, fadeDurationMs);
  }

  function swapToLayer(layer, slide) {
    if (!layer || !activeLayer) {
      return;
    }
    if (layer === activeLayer && activeLayer.src === slide.url && activeLayer.classList.contains('is-visible')) {
      updateSlideMeta(currentIndex, slide);
      return;
    }

    inactiveLayer = activeLayer;
    activeLayer = layer;
    showLayer(activeLayer, slide);
    hideLayer(inactiveLayer);
    updateSlideMeta(currentIndex, slide);
  }

  function renderSlide(index, options) {
    options = options || {};
    if (!activeLayer || index < 0 || index >= slides.length) {
      return Promise.resolve();
    }

    var requestId = ++slideRequestId;
    currentIndex = index;
    var slide = slides[index];
    preloadAdjacentSlides(index);

    return loadSlideImage(slide.url).then(function () {
      if (requestId !== slideRequestId) {
        return;
      }

      var targetLayer = options.forceLayer || (
        activeLayer && activeLayer.classList.contains('is-visible') ? inactiveLayer : activeLayer
      );

      if (!activeLayer.classList.contains('is-visible') && !inactiveLayer.classList.contains('is-visible')) {
        targetLayer = activeLayer;
      }

      if (fadeDurationMs === 0 || !activeLayer.classList.contains('is-visible')) {
        if (inactiveLayer) {
          inactiveLayer.classList.remove('is-visible');
          inactiveLayer.hidden = true;
          inactiveLayer.setAttribute('hidden', 'hidden');
        }
        activeLayer = targetLayer;
        inactiveLayer = targetLayer === layerA ? layerB : layerA;
        showLayer(activeLayer, slide);
        updateSlideMeta(index, slide);
        return;
      }

      swapToLayer(targetLayer, slide);
    }).catch(function () {
      if (requestId !== slideRequestId) {
        return;
      }
      var fallbackLayer = options.forceLayer || activeLayer || layerA;
      if (activeLayer && activeLayer.classList.contains('is-visible')) {
        fallbackLayer = inactiveLayer || layerB;
      }
      activeLayer = fallbackLayer;
      inactiveLayer = fallbackLayer === layerA ? layerB : layerA;
      showLayer(activeLayer, slide);
      updateSlideMeta(index, slide);
    });
  }

  function openLightbox(index) {
    if (!lightbox) {
      return;
    }
    lastFocusedElement = document.activeElement;
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.classList.add('ad-gallery-lightbox-open');

    if (layerA) {
      layerA.classList.remove('is-visible');
      layerA.removeAttribute('src');
      layerA.hidden = true;
      layerA.setAttribute('hidden', 'hidden');
    }
    if (layerB) {
      layerB.classList.remove('is-visible');
      layerB.removeAttribute('src');
      layerB.hidden = true;
      layerB.setAttribute('hidden', 'hidden');
    }
    activeLayer = layerA;
    inactiveLayer = layerB;

    renderSlide(index, { forceLayer: layerA }).then(function () {
      var closeButton = lightbox.querySelector('.ad-gallery-lightbox__close');
      if (closeButton) {
        closeButton.focus();
      }
    });
  }

  function closeLightbox() {
    if (!lightbox) {
      return;
    }
    slideRequestId += 1;
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('ad-gallery-lightbox-open');

    [layerA, layerB].forEach(function (layer) {
      if (!layer) {
        return;
      }
      layer.classList.remove('is-visible');
      layer.removeAttribute('src');
      layer.alt = '';
      layer.hidden = true;
      layer.setAttribute('hidden', 'hidden');
    });
    activeLayer = layerA;
    inactiveLayer = layerB;

    if (captionNode) {
      captionNode.textContent = '';
      captionNode.setAttribute('aria-hidden', 'true');
    }
    if (lightboxCounter) {
      lightboxCounter.textContent = '';
    }
    currentIndex = 0;
    syncActiveThumb(0);
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

  if (thumbStrip) {
    thumbStrip.addEventListener('keydown', function (event) {
      var tabs = Array.prototype.slice.call(
        thumbStrip.querySelectorAll('.ad-detail-gallery__thumb')
      );
      if (!tabs.length) {
        return;
      }
      var currentTab = document.activeElement;
      var currentTabIndex = tabs.indexOf(currentTab);
      if (currentTabIndex === -1) {
        return;
      }

      var nextTabIndex = currentTabIndex;
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
        event.preventDefault();
        var step = event.key === 'ArrowRight' ? -1 : 1;
        nextTabIndex = (currentTabIndex + step + tabs.length) % tabs.length;
        tabs[nextTabIndex].focus();
      }
      if (event.key === 'Home') {
        event.preventDefault();
        tabs[0].focus();
      }
      if (event.key === 'End') {
        event.preventDefault();
        tabs[tabs.length - 1].focus();
      }
    });
  }

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
  var touchStartY = 0;
  if (lightbox) {
    lightbox.addEventListener('touchstart', function (event) {
      if (!event.touches || !event.touches.length) {
        return;
      }
      touchStartX = event.touches[0].screenX;
      touchStartY = event.touches[0].screenY;
    }, { passive: true });

    lightbox.addEventListener('touchend', function (event) {
      if (!event.changedTouches || !event.changedTouches.length) {
        return;
      }
      var touchEndX = event.changedTouches[0].screenX;
      var touchEndY = event.changedTouches[0].screenY;
      var deltaX = touchEndX - touchStartX;
      var deltaY = touchEndY - touchStartY;
      if (Math.abs(deltaX) < 40 || Math.abs(deltaX) < Math.abs(deltaY)) {
        return;
      }
      if (deltaX > 0) {
        showPrevious();
      } else {
        showNext();
      }
    }, { passive: true });

    lightbox.addEventListener('touchcancel', function () {
      touchStartX = 0;
      touchStartY = 0;
    }, { passive: true });
  }
});
