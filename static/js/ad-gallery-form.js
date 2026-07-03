document.addEventListener('DOMContentLoaded', function () {
  var manager = document.getElementById('ad-gallery-manager');
  if (!manager) {
    return;
  }

  var maxImages = parseInt(manager.getAttribute('data-max-images') || '10', 10);
  var existingList = document.getElementById('ad-gallery-existing');
  var orderInput = document.getElementById('gallery-order-input');
  var deleteInput = document.getElementById('gallery-delete-input');
  var fileInput = document.getElementById('gallery-images-input');
  var newPreview = document.getElementById('ad-gallery-new-preview');
  var countLabel = document.getElementById('ad-gallery-count');
  var deletedIds = [];
  var newPreviewUrls = [];

  function getExistingCount() {
    if (!existingList) {
      return 0;
    }
    return existingList.querySelectorAll('.ad-gallery-existing-item:not(.is-marked-delete)').length;
  }

  function getNewCount() {
    return fileInput && fileInput.files ? fileInput.files.length : 0;
  }

  function updateOrderInput() {
    if (!existingList || !orderInput) {
      return;
    }
    var ids = [];
    existingList.querySelectorAll('.ad-gallery-existing-item:not(.is-marked-delete)').forEach(function (item) {
      ids.push(item.getAttribute('data-image-id'));
    });
    orderInput.value = ids.join(',');
  }

  function updateDeleteInput() {
    if (!deleteInput) {
      return;
    }
    deleteInput.value = deletedIds.join(',');
  }

  function updateCountLabel() {
    if (!countLabel) {
      return;
    }
    var total = getExistingCount() + getNewCount();
    countLabel.textContent = total + ' از ' + maxImages + ' تصویر گالری';
    if (fileInput) {
      fileInput.disabled = total >= maxImages;
    }
  }

  function clearNewPreview() {
    newPreviewUrls.forEach(function (url) {
      URL.revokeObjectURL(url);
    });
    newPreviewUrls = [];
    if (newPreview) {
      newPreview.innerHTML = '';
      newPreview.hidden = true;
    }
  }

  function renderNewPreview() {
    if (!newPreview || !fileInput) {
      return;
    }
    clearNewPreview();
    if (!fileInput.files || !fileInput.files.length) {
      return;
    }
    newPreview.hidden = false;
    Array.prototype.forEach.call(fileInput.files, function (file) {
      var url = URL.createObjectURL(file);
      newPreviewUrls.push(url);
      var img = document.createElement('img');
      img.src = url;
      img.alt = file.name;
      img.className = 'ad-gallery-new-preview-item';
      newPreview.appendChild(img);
    });
  }

  function moveItem(item, direction) {
    if (!existingList || !item) {
      return;
    }
    if (direction < 0 && item.previousElementSibling) {
      existingList.insertBefore(item, item.previousElementSibling);
    }
    if (direction > 0 && item.nextElementSibling) {
      existingList.insertBefore(item.nextElementSibling, item);
    }
    updateOrderInput();
  }

  if (existingList) {
    existingList.addEventListener('click', function (event) {
      var item = event.target.closest('.ad-gallery-existing-item');
      if (!item) {
        return;
      }
      if (event.target.closest('.ad-gallery-remove-existing')) {
        var imageId = item.getAttribute('data-image-id');
        if (imageId) {
          deletedIds.push(imageId);
        }
        item.classList.add('is-marked-delete');
        item.hidden = true;
        updateDeleteInput();
        updateOrderInput();
        updateCountLabel();
        return;
      }
      if (event.target.closest('.ad-gallery-move-up')) {
        moveItem(item, -1);
        return;
      }
      if (event.target.closest('.ad-gallery-move-down')) {
        moveItem(item, 1);
      }
    });

    existingList.addEventListener('dragstart', function (event) {
      var item = event.target.closest('.ad-gallery-existing-item');
      if (!item || item.classList.contains('is-marked-delete')) {
        return;
      }
      event.dataTransfer.effectAllowed = 'move';
      item.classList.add('is-dragging');
    });

    existingList.addEventListener('dragend', function (event) {
      var item = event.target.closest('.ad-gallery-existing-item');
      if (item) {
        item.classList.remove('is-dragging');
      }
      updateOrderInput();
    });

    existingList.addEventListener('dragover', function (event) {
      event.preventDefault();
      var dragging = existingList.querySelector('.is-dragging');
      var target = event.target.closest('.ad-gallery-existing-item');
      if (!dragging || !target || dragging === target || target.classList.contains('is-marked-delete')) {
        return;
      }
      var rect = target.getBoundingClientRect();
      var after = event.clientY > rect.top + rect.height / 2;
      if (after) {
        target.after(dragging);
      } else {
        target.before(dragging);
      }
    });

    var touchDragItem = null;
    var touchStartY = 0;

    existingList.addEventListener('touchstart', function (event) {
      var item = event.target.closest('.ad-gallery-existing-item');
      if (!item || item.classList.contains('is-marked-delete')) {
        return;
      }
      if (event.target.closest('.ad-gallery-existing-actions')) {
        return;
      }
      touchDragItem = item;
      touchStartY = event.touches[0].clientY;
      item.classList.add('is-dragging');
    }, { passive: true });

    existingList.addEventListener('touchmove', function (event) {
      if (!touchDragItem) {
        return;
      }
      event.preventDefault();
      var touch = event.touches[0];
      var target = document.elementFromPoint(touch.clientX, touch.clientY);
      if (!target) {
        return;
      }
      var dropItem = target.closest('.ad-gallery-existing-item');
      if (!dropItem || dropItem === touchDragItem || dropItem.classList.contains('is-marked-delete')) {
        return;
      }
      var rect = dropItem.getBoundingClientRect();
      var after = touch.clientY > rect.top + rect.height / 2;
      if (after) {
        dropItem.after(touchDragItem);
      } else {
        dropItem.before(touchDragItem);
      }
    }, { passive: false });

    existingList.addEventListener('touchend', function () {
      if (touchDragItem) {
        touchDragItem.classList.remove('is-dragging');
        touchDragItem = null;
        updateOrderInput();
      }
    }, { passive: true });

    existingList.addEventListener('touchcancel', function () {
      if (touchDragItem) {
        touchDragItem.classList.remove('is-dragging');
        touchDragItem = null;
      }
    }, { passive: true });
  }

  if (fileInput) {
    fileInput.addEventListener('change', function () {
      var total = getExistingCount() + getNewCount();
      if (total > maxImages) {
        alert('حداکثر ' + maxImages + ' تصویر گالری مجاز است.');
        fileInput.value = '';
        clearNewPreview();
        updateCountLabel();
        return;
      }
      renderNewPreview();
      updateCountLabel();
    });
  }

  updateOrderInput();
  updateDeleteInput();
  updateCountLabel();
});
