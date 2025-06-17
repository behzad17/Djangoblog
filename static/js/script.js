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
});
