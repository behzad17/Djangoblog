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
      const originalButtonText = submitButton.textContent;
      submitButton.disabled = true;
      submitButton.textContent = "در حال ارسال...";

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
        .then((response) => {
          // Check if response is ok (status 200-299)
          if (!response.ok) {
            // Try to parse error response
            return response.json().then(data => {
              throw new Error(data.message || 'An error occurred');
            }).catch(() => {
              throw new Error('Server error: ' + response.status);
            });
          }
          return response.json();
        })
        .then((data) => {
          if (data.status === "success") {
            // Find the comments container - use the comments-card class
            const commentsContainer = document.querySelector(".comments-card .card-body");
            
            if (!commentsContainer) {
              console.error("Comments container not found");
              alert("خطا در نمایش نظر. صفحه را رفرش کنید.");
              submitButton.disabled = false;
              submitButton.textContent = originalButtonText;
              return;
            }

            // Create new comment element matching the template structure
            const newComment = document.createElement("div");
            newComment.className = "comments p-3 rounded mb-3 bg-light border";

            newComment.innerHTML = `
            <div class="d-flex align-items-center justify-content-between mb-1">
              <p class="mb-0 fw-semibold">${data.author}</p>
              <span class="text-muted small">${data.created_on}</span>
            </div>
            <div id="comment${data.id}" class="mb-2">
              ${data.body}
            </div>
            <div class="d-flex gap-2 mt-2">
              <a href="/${data.post_slug}/delete_comment/${data.id}" class="btn btn-sm btn-outline-danger">حذف</a>
              <button class="btn btn-sm btn-outline-secondary edit-comment" data-comment-id="${data.id}">ویرایش</button>
            </div>
          `;

            // Remove "No comments yet" message if it exists (Persian text)
            const noComments = commentsContainer.querySelector("p.text-muted");
            if (noComments && (noComments.textContent.includes("هنوز نظری ثبت نشده") || noComments.textContent.includes("No comments yet"))) {
              noComments.remove();
            }

            // Find where to insert - after the heading/badge, before existing comments
            const commentsList = commentsContainer.querySelectorAll(".comments");
            if (commentsList.length > 0) {
              // Insert before first existing comment
              commentsContainer.insertBefore(newComment, commentsList[0]);
            } else {
              // No existing comments, insert after heading section
              const headingSection = commentsContainer.querySelector(".d-flex.align-items-center");
              if (headingSection && headingSection.nextSibling) {
                commentsContainer.insertBefore(newComment, headingSection.nextSibling);
              } else {
                commentsContainer.appendChild(newComment);
              }
            }

            // Update comment count badge
            const commentCountBadge = commentsContainer.querySelector(".badge.bg-secondary");
            if (commentCountBadge) {
              const currentCount = parseInt(commentCountBadge.textContent) || 0;
              commentCountBadge.textContent = currentCount + 1;
            }

            // Reset form
            commentForm.reset();
            
            // Clear any existing messages
            const existingAlerts = document.querySelectorAll('.alert');
            existingAlerts.forEach(alert => alert.remove());
            
            // Show success message
            showSuccessMessage("نظر شما با موفقیت اضافه شد!");
            
            // Scroll to new comment
            newComment.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Redirect to clear POST data from browser history
            window.history.replaceState({}, document.title, window.location.pathname);
          } else if (data.status === "error") {
            // Show error message from server
            alert(data.message || "خطا در ارسال نظر. لطفاً دوباره تلاش کنید.");
          } else {
            alert("خطا در ارسال نظر. لطفاً دوباره تلاش کنید.");
          }
          submitButton.disabled = false;
          submitButton.textContent = originalButtonText;
        })
        .catch((error) => {
          console.error("Error:", error);
          // Show user-friendly error message
          alert(error.message || "خطایی رخ داد. لطفاً دوباره تلاش کنید.");
          submitButton.disabled = false;
          submitButton.textContent = originalButtonText;
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

  // Ask Me - Question Modal Functionality removed
  // Questions are now submitted directly on the expert profile page
});

// Ad Banner Dismissal Functionality
// Banner only shows to unauthenticated users (controlled by template)
// Close button hides banner for current session only (no localStorage persistence)
// Function to initialize banner
function initAdBanner() {
  const adBanner = document.getElementById('adBanner');
  const closeButton = document.getElementById('closeBanner');
  
  if (!adBanner) {
    // Banner not found - either user is authenticated (banner not rendered) or DOM not ready
    return;
  }
  
  // Ensure banner is visible (for unauthenticated users)
  adBanner.classList.remove('is-hidden');
  
  // Handle close button click - hide only for current session/page
  if (closeButton) {
    closeButton.addEventListener('click', function(e) {
      // Prevent event from bubbling to ad link
      e.preventDefault();
      e.stopPropagation();
      
      // Hide banner with smooth animation (session-only, no localStorage)
      if (adBanner) {
        // Add smooth transition
        adBanner.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        adBanner.style.opacity = '0';
        adBanner.style.transform = 'translateX(-50%) translateY(-10px)';
        
        // Add is-hidden class after animation completes
        setTimeout(function() {
          if (adBanner) {
            adBanner.classList.add('is-hidden');
          }
        }, 300);
      }
    });
    
    // Handle keyboard navigation (Enter and Space keys)
    closeButton.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        e.stopPropagation();
        closeButton.click();
      }
    });
  }
}

// Run on DOMContentLoaded
document.addEventListener('DOMContentLoaded', initAdBanner);

// Also try immediately in case DOM is already ready
if (document.readyState === 'loading') {
  // DOM is still loading, wait for DOMContentLoaded
  document.addEventListener('DOMContentLoaded', initAdBanner);
} else {
  // DOM is already ready, run immediately
  initAdBanner();
}

// FAQ Accordion functionality moved to static/js/peyvand_faq.js
// This keeps the code clean and scoped to the member-guide page only
