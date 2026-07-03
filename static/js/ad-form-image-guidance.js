(function () {
  var RECOMMENDED_RATIO = 1;
  var RATIO_TOLERANCE = 0.15;
  var WARNING_MESSAGE =
    'ابعاد این تصویر مربع نیست. برای بهترین نمایش در پیوند، تصاویر مربعی ۱۲۰۰×۱۲۰۰ پیکسل توصیه می‌شوند. می‌توانید همین تصویر را بارگذاری کنید.';

  function readImageDimensions(file) {
    return new Promise(function (resolve) {
      if (!file || typeof URL === 'undefined' || typeof URL.createObjectURL !== 'function') {
        resolve(null);
        return;
      }

      var objectUrl = URL.createObjectURL(file);
      var image = new Image();

      image.onload = function () {
        URL.revokeObjectURL(objectUrl);
        resolve({
          width: image.naturalWidth,
          height: image.naturalHeight,
        });
      };

      image.onerror = function () {
        URL.revokeObjectURL(objectUrl);
        resolve(null);
      };

      image.src = objectUrl;
    });
  }

  function isSquareEnough(width, height) {
    if (!width || !height) {
      return true;
    }
    var ratio = width / height;
    return Math.abs(ratio - RECOMMENDED_RATIO) <= RATIO_TOLERANCE;
  }

  function setWarning(node, visible, message) {
    if (!node) {
      return;
    }
    if (visible) {
      node.textContent = message || WARNING_MESSAGE;
      node.hidden = false;
      return;
    }
    node.textContent = '';
    node.hidden = true;
  }

  function initPrimaryImageGuidance() {
    var input = document.getElementById('id_image');
    var warning = document.getElementById('ad-primary-image-aspect-warning');
    if (!input) {
      return;
    }

    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (!file) {
        setWarning(warning, false);
        return;
      }

      readImageDimensions(file).then(function (dimensions) {
        if (!dimensions) {
          setWarning(warning, false);
          return;
        }
        setWarning(
          warning,
          !isSquareEnough(dimensions.width, dimensions.height)
        );
      });
    });
  }

  function checkGalleryFiles(files) {
    var warning = document.getElementById('ad-gallery-aspect-warning');
    if (!warning || !files || !files.length) {
      setWarning(warning, false);
      return Promise.resolve();
    }

    return Promise.all(
      Array.prototype.map.call(files, function (file) {
        return readImageDimensions(file).then(function (dimensions) {
          if (!dimensions) {
            return false;
          }
          return !isSquareEnough(dimensions.width, dimensions.height);
        });
      })
    ).then(function (results) {
      var nonSquareCount = results.filter(Boolean).length;
      if (!nonSquareCount) {
        setWarning(warning, false);
        return;
      }

      var message = nonSquareCount === 1
        ? WARNING_MESSAGE
        : nonSquareCount + ' تصویر انتخاب‌شده مربع نیست. برای بهترین نمایش در پیوند، تصاویر مربعی ۱۲۰۰×۱۲۰۰ پیکسل توصیه می‌شوند. می‌توانید همین تصاویر را بارگذاری کنید.';
      setWarning(warning, true, message);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initPrimaryImageGuidance();
  });

  window.AdFormImageGuidance = {
    checkGalleryFiles: checkGalleryFiles,
  };
})();
