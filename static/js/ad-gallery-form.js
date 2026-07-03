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
  var validationLabel = document.getElementById('ad-gallery-validation');
  var uploadRow = document.querySelector('.ad-gallery-upload-row');
  var previewPanel = document.getElementById('ad-gallery-preview-panel');
  var emptyState = document.getElementById('ad-gallery-empty');
  var deletedIds = [];
  var pendingFiles = [];
  var previewUrlByKey = Object.create(null);

  function fileKey(file) {
    return [
      file.name,
      file.size,
      file.lastModified,
      file.type || '',
    ].join('|');
  }

  function cloneFileForPending(file) {
    return new File([file], file.name, {
      type: file.type || 'application/octet-stream',
      lastModified: file.lastModified,
    });
  }

  function getPreviewUrl(file) {
    var key = fileKey(file);
    if (!previewUrlByKey[key]) {
      previewUrlByKey[key] = URL.createObjectURL(file);
    }
    return previewUrlByKey[key];
  }

  function revokePreviewUrl(file) {
    var key = fileKey(file);
    if (previewUrlByKey[key]) {
      URL.revokeObjectURL(previewUrlByKey[key]);
      delete previewUrlByKey[key];
    }
  }

  function pruneUnusedPreviewUrls() {
    var activeKeys = Object.create(null);
    pendingFiles.forEach(function (file) {
      activeKeys[fileKey(file)] = true;
    });
    Object.keys(previewUrlByKey).forEach(function (key) {
      if (!activeKeys[key]) {
        URL.revokeObjectURL(previewUrlByKey[key]);
        delete previewUrlByKey[key];
      }
    });
  }

  function isImageFile(file) {
    if (!file) {
      return false;
    }
    if (file.type && file.type.indexOf('image/') === 0) {
      return true;
    }
    return /\.(jpe?g|png|gif|webp|bmp|heic|heif|avif|svg)$/i.test(file.name || '');
  }

  function filesAreSame(a, b) {
    return (
      a.name === b.name &&
      a.size === b.size &&
      a.lastModified === b.lastModified
    );
  }

  function getExistingCount() {
    if (!existingList) {
      return 0;
    }
    return existingList.querySelectorAll('.ad-gallery-existing-item:not(.is-marked-delete)').length;
  }

  function getNewCount() {
    return pendingFiles.length;
  }

  function getTotalCount() {
    return getExistingCount() + getNewCount();
  }

  function getRemainingSlots() {
    return Math.max(0, maxImages - getExistingCount());
  }

  function syncFileInput() {
    if (!fileInput || typeof DataTransfer === 'undefined') {
      return;
    }
    var transfer = new DataTransfer();
    pendingFiles.forEach(function (file) {
      transfer.items.add(file);
    });
    fileInput.files = transfer.files;
  }

  function clearValidationMessage() {
    if (!validationLabel) {
      return;
    }
    validationLabel.textContent = '';
    validationLabel.hidden = true;
  }

  function showValidationMessage(message) {
    if (!validationLabel) {
      window.alert(message);
      return;
    }
    validationLabel.textContent = message;
    validationLabel.hidden = false;
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

  function updatePreviewPanelState() {
    var total = getTotalCount();
    if (previewPanel) {
      previewPanel.classList.toggle('has-items', total > 0);
    }
    if (emptyState) {
      emptyState.hidden = total > 0;
    }
  }

  function updateCountLabel() {
    if (!countLabel) {
      return;
    }
    var total = getTotalCount();
    countLabel.textContent = total + ' از ' + maxImages + ' تصویر انتخاب شده';
    if (fileInput) {
      fileInput.disabled = total >= maxImages;
    }
    updatePreviewPanelState();
  }

  function removePendingFile(file) {
    revokePreviewUrl(file);
    pendingFiles = pendingFiles.filter(function (pending) {
      return !filesAreSame(pending, file);
    });
    syncFileInput();
    renderNewPreview();
    updateCountLabel();
    clearValidationMessage();
  }

  function renderNewPreview() {
    if (!newPreview) {
      return;
    }

    newPreview.innerHTML = '';
    if (!pendingFiles.length) {
      newPreview.hidden = true;
      pruneUnusedPreviewUrls();
      return;
    }

    newPreview.hidden = false;
    pendingFiles.forEach(function (file) {
      var url = getPreviewUrl(file);

      var item = document.createElement('div');
      item.className = 'ad-gallery-card ad-gallery-new-card';

      var frame = document.createElement('div');
      frame.className = 'ad-gallery-card__frame';

      var img = document.createElement('img');
      img.src = url;
      img.alt = '';
      img.className = 'ad-gallery-card__media';
      img.decoding = 'async';

      var removeButton = document.createElement('button');
      removeButton.type = 'button';
      removeButton.className = 'ad-gallery-card__remove';
      removeButton.setAttribute('aria-label', 'حذف تصویر انتخاب‌شده');
      removeButton.innerHTML = '<i class="fas fa-times" aria-hidden="true"></i>';
      removeButton.addEventListener('click', function () {
        removePendingFile(file);
      });

      frame.appendChild(img);
      frame.appendChild(removeButton);
      item.appendChild(frame);
      newPreview.appendChild(item);
    });

    pruneUnusedPreviewUrls();
  }

  function addFiles(fileList) {
    if (!fileList || !fileList.length) {
      return;
    }

    clearValidationMessage();

    var remainingSlots = getRemainingSlots();
    if (remainingSlots <= 0) {
      showValidationMessage('حداکثر ' + maxImages + ' تصویر گالری مجاز است.');
      return;
    }

    var accepted = 0;
    var rejectedByLimit = 0;
    var rejectedByType = 0;
    var skippedDuplicates = 0;

    Array.prototype.forEach.call(fileList, function (file) {
      if (!isImageFile(file)) {
        rejectedByType += 1;
        return;
      }

      var isDuplicate = pendingFiles.some(function (pending) {
        return filesAreSame(pending, file);
      });
      if (isDuplicate) {
        skippedDuplicates += 1;
        return;
      }

      if (getExistingCount() + pendingFiles.length >= maxImages) {
        rejectedByLimit += 1;
        return;
      }

      pendingFiles.push(cloneFileForPending(file));
      accepted += 1;
    });

    syncFileInput();
    renderNewPreview();
    updateCountLabel();

    if (rejectedByLimit > 0) {
      showValidationMessage(
        rejectedByLimit + ' تصویر اضافی نادیده گرفته شد. حداکثر ' + maxImages + ' تصویر گالری مجاز است.'
      );
      return;
    }

    if (rejectedByType > 0) {
      showValidationMessage('فقط فایل‌های تصویری پذیرفته می‌شوند.');
      return;
    }

    if (!accepted && skippedDuplicates > 0) {
      showValidationMessage('این تصاویر قبلاً انتخاب شده‌اند.');
    }
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
        clearValidationMessage();
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

    existingList.addEventListener('touchstart', function (event) {
      var item = event.target.closest('.ad-gallery-existing-item');
      if (!item || item.classList.contains('is-marked-delete')) {
        return;
      }
      if (event.target.closest('.ad-gallery-card__toolbar')) {
        return;
      }
      touchDragItem = item;
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
      var selectedFiles = fileInput.files
        ? Array.prototype.slice.call(fileInput.files)
        : [];
      if (selectedFiles.length) {
        addFiles(selectedFiles);
      }
      fileInput.value = '';
      syncFileInput();
    });
  }

  if (uploadRow) {
    uploadRow.addEventListener('dragenter', function (event) {
      if (getTotalCount() >= maxImages) {
        return;
      }
      event.preventDefault();
      uploadRow.classList.add('is-drag-over');
    });

    uploadRow.addEventListener('dragover', function (event) {
      if (getTotalCount() >= maxImages) {
        return;
      }
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
      uploadRow.classList.add('is-drag-over');
    });

    uploadRow.addEventListener('dragleave', function (event) {
      if (event.relatedTarget && uploadRow.contains(event.relatedTarget)) {
        return;
      }
      uploadRow.classList.remove('is-drag-over');
    });

    uploadRow.addEventListener('drop', function (event) {
      event.preventDefault();
      uploadRow.classList.remove('is-drag-over');
      if (event.dataTransfer && event.dataTransfer.files) {
        addFiles(event.dataTransfer.files);
      }
    });
  }

  updateOrderInput();
  updateDeleteInput();
  updateCountLabel();
});
