// Function to show success messages
function showSuccessMessage(message) {
  // Create alert element
  const alertDiv = document.createElement('div');
  alertDiv.className = 'alert alert-success alert-dismissible fade show';
  alertDiv.setAttribute('role', 'alert');
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  // Insert at the top of the messages container
  const messagesContainer = document.querySelector('.container .row .col-md-8.offset-md-2');
  if (messagesContainer) {
    messagesContainer.insertBefore(alertDiv, messagesContainer.firstChild);
    console.log('Success message displayed:', message);
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        console.log('Auto-dismissing message after 10 seconds');
        alertDiv.remove();
      }
    }, 10000);
  } else {
    console.log('Messages container not found');
  }
}

// Favorite button functionality
document.addEventListener("DOMContentLoaded", function () {
  const favoriteButtons = document.querySelectorAll(".favorite-btn");

  favoriteButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const postId = this.dataset.postId;
      const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
      ).value;

      fetch(`/add_to_favorites/${postId}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.status === "success") {
            const icon = this.querySelector("i");
            const count = this.querySelector(".favorite-count");

            if (data.is_favorite) {
              icon.classList.remove("far");
              icon.classList.add("fas", "text-danger");
            } else {
              icon.classList.remove("fas", "text-danger");
              icon.classList.add("far");
            }

            count.textContent = data.favorite_count;
          }
        })
        .catch((error) => console.error("Error:", error));
    });
  });

  // Comment form submission
  const commentForm = document.getElementById("commentForm");
  if (commentForm) {
    // Ensure form is clean on page load
    commentForm.reset();
    commentForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const submitButton = document.getElementById("submitButton");
      submitButton.disabled = true;
      submitButton.textContent = "Submitting...";

      const formData = new FormData(this);
      const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
      ).value;

      fetch(window.location.href, {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.status === "success") {
            // Create new comment element - target the comments section specifically
            const commentsHeading = Array.from(document.querySelectorAll("h3")).find(h3 => h3.textContent.includes("Comments:"));
            const commentsContainer = commentsHeading ? commentsHeading.nextElementSibling : document.querySelector(".col-md-8 .card-body");
            
            // Debug logging
            console.log("Comments heading found:", commentsHeading);
            console.log("Comments container:", commentsContainer);
            const newComment = document.createElement("div");
            newComment.className = "comments";
            newComment.style.padding = "10px";

            newComment.innerHTML = `
            <p class="font-weight-bold">
              ${data.author}
              <span class="text-muted font-weight-normal">${data.created_on}</span>
              wrote:
            </p>
            <div id="comment${data.id}">
              ${data.body}
            </div>
            <div class="mt-2">
              <a href="/comment/delete/${data.post_slug}/${data.id}/" class="btn btn-sm btn-outline-danger">Delete</a>
              <button class="btn btn-sm btn-outline-secondary edit-comment" data-comment-id="${data.id}">Edit</button>
            </div>
          `;

            // Remove "No comments yet" message if it exists
            const noComments = commentsContainer.querySelector("p");
            if (noComments && noComments.textContent === "No comments yet.") {
              noComments.remove();
            }

            // Add new comment at the top
            commentsContainer.insertBefore(
              newComment,
              commentsContainer.firstChild
            );

            // Update comment count
            const commentCount = document.querySelector(
              ".text-secondary strong"
            );
            if (commentCount) {
              const currentCount = parseInt(commentCount.textContent) || 0;
              commentCount.textContent = currentCount + 1;
            }

            // Reset form
            commentForm.reset();
            
            // Clear any existing messages
            const existingAlerts = document.querySelectorAll('.alert');
            existingAlerts.forEach(alert => alert.remove());
            
            // Show success message
            showSuccessMessage("Your comment was added successfully!");
            
            // Redirect to clear POST data from browser history
            window.history.replaceState({}, document.title, window.location.pathname);
          } else {
            alert("Error submitting comment. Please try again.");
          }
          submitButton.disabled = false;
          submitButton.textContent = "Submit";
        })
        .catch((error) => {
          console.error("Error:", error);
          submitButton.disabled = false;
          submitButton.textContent = "Submit";
        });
    });
  }

  // Inline comment editing
  document.addEventListener("click", function (e) {
    if (e.target.classList.contains("edit-comment")) {
      const commentId = e.target.dataset.commentId;
      const commentDiv = document.getElementById(`comment${commentId}`);
      const currentText = commentDiv.textContent.trim();

      // Create edit form
      const editForm = document.createElement("form");
      editForm.className = "edit-comment-form";
      editForm.innerHTML = `
        <div class="form-group">
          <textarea class="form-control" name="body" rows="3">${currentText}</textarea>
        </div>
        <div class="mt-2">
          <button type="submit" class="btn btn-sm btn-primary">Save</button>
          <button type="button" class="btn btn-sm btn-secondary cancel-edit">Cancel</button>
        </div>
      `;

      // Replace comment text with edit form
      commentDiv.innerHTML = "";
      commentDiv.appendChild(editForm);

      // Handle form submission
      editForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const newText = this.querySelector("textarea").value;
        const csrfToken = document.querySelector(
          "[name=csrfmiddlewaretoken]"
        ).value;

        fetch(
          `/${
            window.location.pathname.split("/")[1]
          }/edit_comment/${commentId}/`,
          {
            method: "POST",
            headers: {
              "X-CSRFToken": csrfToken,
              "Content-Type": "application/json",
              "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({ body: newText }),
          }
        )
          .then((response) => response.json())
          .then((data) => {
            if (data.status === "success") {
              commentDiv.textContent = data.body;
              
              // Clear any existing messages
              const existingAlerts = document.querySelectorAll('.alert');
              existingAlerts.forEach(alert => alert.remove());
              
              // Show success message
              showSuccessMessage("Your comment was updated successfully!");
            } else {
              alert("Error updating comment. Please try again.");
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("Error updating comment. Please try again.");
          });
      });

      // Handle cancel button
      editForm
        .querySelector(".cancel-edit")
        .addEventListener("click", function () {
          commentDiv.textContent = currentText;
        });
    }
  });

  // Ask Me - Question Modal Functionality
  const questionModal = document.getElementById('questionModal');
  if (questionModal) {
    const askQuestionButtons = document.querySelectorAll('.ask-question-btn');
    const moderatorNameEl = document.getElementById('moderatorName');
    const moderatorTitleEl = document.getElementById('moderatorTitle');
    const moderatorIdEl = document.getElementById('moderatorId');
    const questionForm = document.getElementById('questionForm');

    // Handle modal open - populate moderator info
    askQuestionButtons.forEach(button => {
      button.addEventListener('click', function() {
        const moderatorId = this.dataset.moderatorId;
        const moderatorName = this.dataset.moderatorName;
        const moderatorTitle = this.dataset.moderatorTitle;

        if (moderatorNameEl) moderatorNameEl.textContent = moderatorName;
        if (moderatorTitleEl) moderatorTitleEl.textContent = moderatorTitle;
        if (moderatorIdEl) moderatorIdEl.value = moderatorId;
        
        // Reset form
        if (questionForm) {
          questionForm.reset();
        }
      });
    });

    // Handle form submission via AJAX
    if (questionForm) {
      questionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const submitButton = this.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';

        const formData = new FormData(this);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const moderatorId = moderatorIdEl.value;

        fetch(`/ask-me/moderator/${moderatorId}/ask/`, {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
          },
        })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            // Close modal
            const modalInstance = bootstrap.Modal.getInstance(questionModal);
            if (modalInstance) {
              modalInstance.hide();
            }

            // Show success message
            showSuccessMessage(data.message || 'Your question has been submitted successfully!');

            // Reset form
            questionForm.reset();

            // Optionally redirect or refresh
            setTimeout(() => {
              window.location.href = '/ask-me/my-questions/';
            }, 1500);
          } else {
            // Show errors
            let errorMsg = 'Error submitting question. ';
            if (data.errors) {
              const errorList = Object.values(data.errors).flat();
              errorMsg += errorList.join(' ');
            }
            alert(errorMsg);
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
          }
        })
        .catch(error => {
          console.error('Error:', error);
          alert('An error occurred. Please try again.');
          submitButton.disabled = false;
          submitButton.innerHTML = originalText;
        });
      });
    }
  }
});

// Ad Banner Dismissal Functionality
document.addEventListener('DOMContentLoaded', function() {
  const adBanner = document.getElementById('adBanner');
  const closeButton = document.getElementById('closeBanner');
  
  // Check if banner was previously dismissed
  try {
    if (localStorage.getItem('adBannerDismissed') === 'true') {
      // Banner already dismissed, don't show
      if (adBanner) {
        adBanner.style.display = 'none';
      }
      return;
    }
  } catch (e) {
    // localStorage not available (e.g., private browsing), continue to show banner
    console.log('localStorage not available, showing banner');
  }
  
  // Show the banner if it exists and wasn't dismissed
  if (adBanner) {
    adBanner.style.display = 'flex';
  }
  
  // Handle close button click
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      try {
        // Save dismissal state
        localStorage.setItem('adBannerDismissed', 'true');
      } catch (e) {
        // localStorage not available, but still hide banner for this session
        console.log('localStorage not available, hiding banner for this session only');
      }
      
      // Hide banner with smooth animation
      if (adBanner) {
        adBanner.style.transition = 'opacity 0.3s ease, height 0.3s ease';
        adBanner.style.opacity = '0';
        adBanner.style.height = '0';
        adBanner.style.overflow = 'hidden';
        
        // Remove from DOM after animation
        setTimeout(function() {
          if (adBanner && adBanner.parentNode) {
            adBanner.remove();
          }
        }, 300);
      }
    });
    
    // Handle keyboard navigation (Enter and Space keys)
    closeButton.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        closeButton.click();
      }
    });
  }
});
