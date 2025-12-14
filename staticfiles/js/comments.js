const editButtons = document.getElementsByClassName("edit-comment");
const commentText = document.getElementById("id_body");
const commentForm = document.getElementById("commentForm");
const submitButton = document.getElementById("submitButton");
const deleteModal = new bootstrap.Modal(document.getElementById("deleteModal"));
const deleteButtons = document.querySelectorAll("a[href*='comment_delete']");
const deleteConfirm = document.getElementById("deleteConfirm");

/**
 * Initializes edit functionality for the provided edit buttons.
 *
 * For each button in the `editButtons` collection:
 * - Retrieves the associated comment's ID upon click.
 * - Retrieves the associated post's slug from the URL or data attribute.
 * - Fetches the content of the corresponding comment.
 * - Populates the `commentText` input/textarea with the comment's content for editing.
 * - Updates the submit button's text to "Update".
 * - Sets the form's action attribute to the `comment_edit/{postSlug}/{commentId}` endpoint.
 */
for (let button of editButtons) {
  button.addEventListener("click", (e) => {
    e.preventDefault();
    let commentId = e.target.getAttribute("data-comment-id");
    // Get post slug from the current URL path
    let postSlug = window.location.pathname.split('/')[1];
    let commentContent = document.getElementById(
      `comment${commentId}`
    ).innerText;
    commentText.value = commentContent;
    submitButton.innerText = "Update";
    commentForm.setAttribute("action", `${postSlug}/edit_comment/${commentId}/`);
    
    // Scroll to comment form
    commentForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
}

/**
 * Initializes deletion functionality for the provided delete buttons.
 *
 * For each button in the `deleteButtons` collection:
 * - Retrieves the associated comment's ID from the href.
 * - Updates the `deleteConfirm` link's href to point to the
 * deletion endpoint for the specific comment.
 * - Displays a confirmation modal (`deleteModal`) to prompt
 * the user for confirmation before deletion.
 */
for (let button of deleteButtons) {
  button.addEventListener("click", (e) => {
    e.preventDefault();
    // Extract comment ID and post slug from the href
    let href = e.target.getAttribute("href");
    deleteConfirm.href = href;
    deleteModal.show();
  });
}
