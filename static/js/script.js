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
    commentForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const submitButton = document.getElementById("submitButton");
      submitButton.disabled = true;
      submitButton.textContent = "Submitting...";

      const formData = new FormData(this);
      const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
      ).value;

      // Check if we're editing an existing comment
      const isEditing = this.dataset.commentId !== undefined;
      const url = isEditing
        ? `/comment/edit/${formData.get("post_slug")}/${
            this.dataset.commentId
          }/`
        : window.location.href;

      fetch(url, {
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
            if (isEditing) {
              // Update existing comment
              const commentElement = document.getElementById(
                `comment${data.id}`
              );
              if (commentElement) {
                commentElement.innerHTML = data.body;
                // Update the comment container to show it's no longer in edit mode
                const commentContainer = commentElement.closest(".comments");
                commentContainer.classList.remove("editing");
                // Reset the form to its original state
                commentForm.reset();
                submitButton.textContent = "Submit";
                // Remove the comment ID from the form
                delete commentForm.dataset.commentId;
              }
            } else {
              // Create new comment element
              const commentsContainer = document.querySelector(".card-body");
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
                  <a href="/comment/edit/${data.post_slug}/${data.id}/" class="btn btn-sm btn-outline-secondary">Edit</a>
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
            }
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

  // Handle edit comment links
  document.querySelectorAll(".edit-comment").forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const commentId = this.dataset.commentId;
      const postSlug = this.dataset.postSlug;

      fetch(`/comment/edit/${postSlug}/${commentId}/`, {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.status === "success") {
            const commentForm = document.getElementById("commentForm");
            const submitButton = document.getElementById("submitButton");

            // Update form for editing
            commentForm.querySelector("textarea").value = data.body;
            commentForm.dataset.commentId = commentId;
            submitButton.textContent = "Update Comment";

            // Mark the comment being edited
            const commentElement = document.getElementById(
              `comment${commentId}`
            );
            if (commentElement) {
              commentElement.closest(".comments").classList.add("editing");
            }

            // Scroll to the form
            commentForm.scrollIntoView({ behavior: "smooth" });
          }
        })
        .catch((error) => console.error("Error:", error));
    });
  });
});
