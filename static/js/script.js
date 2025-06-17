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

    fetch(window.location.href, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          location.reload();
        } else {
          alert("Error submitting comment. Please try again.");
          submitButton.disabled = false;
          submitButton.textContent = "Submit";
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        submitButton.disabled = false;
        submitButton.textContent = "Submit";
      });
  });
}
