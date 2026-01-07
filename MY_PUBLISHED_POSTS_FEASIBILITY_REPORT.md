# Feasibility Report: "My Published Posts" Section on Settings Page

**Date:** 2025-01-XX  
**Status:** ✅ **FEASIBLE**  
**Scope:** POSTS only (blog/experiences). Ads are NOT modified.

---

## Executive Summary

**Feasibility:** ✅ **FEASIBLE**

Adding a "My Published Posts" section to the existing `accounts/settings/` page is **technically feasible** with **low risk** and **minimal complexity**. The implementation requires:
- Modifying 1 view (`accounts/views.py`)
- Modifying 1 template (`templates/account/settings.html`)
- No URL changes needed
- No model changes needed
- No security risks if implemented correctly

**Estimated Implementation Complexity:** Low to Medium  
**Estimated Development Time:** 1-2 hours  
**Risk Level:** Low (with proper authorization checks)

---

## A) Current Settings Page Implementation

### View Location
- **File:** `accounts/views.py`
- **Function:** `account_settings(request)`
- **Decorator:** `@login_required` (already protected)
- **Current Implementation:**
  ```python
  @login_required
  def account_settings(request):
      """Account settings page that provides links to change password and email."""
      return render(request, 'account/settings.html')
  ```

### Template Location
- **File:** `templates/account/settings.html`
- **Structure:** Extends `base.html`, uses Bootstrap 5 cards
- **Current Content:** Two cards (Change Password, Change Email) + info alert
- **Layout:** Centered container (`col-md-8 col-lg-6`), responsive

### URL Configuration
- **Route:** `/accounts/settings/`
- **URL Name:** `account_settings`
- **File:** `accounts/urls.py` (already configured)
- **No changes needed** to URLs

### Best Insertion Point
**Recommended:** Add the "My Published Posts" section **below the existing settings cards** and **above the info alert**, or as a **separate section** after the info alert. This maintains visual hierarchy and keeps account settings (password/email) at the top.

**Alternative:** Add as a **new card** in the same row (if using grid), but this may make the page too long. Better to use a separate section with its own heading.

---

## B) Data Query Analysis

### Post Model Structure
**Location:** `blog/models.py`

**Relevant Fields:**
- `author` (ForeignKey to `User`, `related_name="blog_posts"`)
- `status` (IntegerField, choices: `((0, "Draft"), (1, "Published"))`)
- `is_deleted` (BooleanField, default=False)
- `title` (CharField, max_length=200)
- `slug` (SlugField, unique=True) - for URL generation
- `created_on` (DateTimeField, auto_now_add=True)
- `category` (ForeignKey to `Category`, `related_name='posts'`)
- `excerpt` (TextField, blank=True)

**Status Values:**
- `0` = Draft (also used for PENDING_REVIEW after edits)
- `1` = Published

**"Published" Definition:**
- `status=1` (Published)
- `is_deleted=False` (not soft-deleted)

### Required Query
```python
from blog.models import Post
from django.core.paginator import Paginator

# In account_settings view:
user_published_posts = Post.objects.filter(
    author=request.user,
    status=1,  # Published
    is_deleted=False  # Not soft-deleted
).select_related('category').order_by('-created_on')
```

**Query Safety:**
- ✅ Uses `author=request.user` (ensures only current user's posts)
- ✅ Filters `status=1` (only published)
- ✅ Filters `is_deleted=False` (excludes soft-deleted)
- ✅ Uses `select_related('category')` to prevent N+1 queries

**Pagination:**
- Recommended: 10-20 items per page (settings page should be fast)
- Project pattern: Uses `Paginator` from `django.core.paginator`
- Example: `paginator = Paginator(user_published_posts, 15)`

---

## C) UI/UX Approach Options

### Recommended Approach: Simple List with Pagination

**Option A: Simple List (Recommended)**
- **Layout:** Clean list of post titles with metadata
- **Each Item Shows:**
  - Post title (clickable link to `post_detail`)
  - Category badge/name
  - Publication date (formatted in Persian)
  - Optional: Small excerpt or "View" button
- **Styling:** Bootstrap list-group or card-based list
- **Pagination:** Bottom of list (if > 15 items)
- **Empty State:** Friendly message: "شما هنوز پستی منتشر نکرده‌اید" (You haven't published any posts yet)

**Option B: Small Card List**
- Similar to existing settings cards but smaller
- More visual but may be too heavy for settings page
- **Not recommended** (settings page should be lightweight)

**Option C: Search/Sort (Optional, Future Enhancement)**
- Add search box to filter posts by title
- Add sort options (newest/oldest)
- **Not required for initial implementation** (can be added later)

### RTL Compatibility
- ✅ Project already uses RTL (Persian language)
- ✅ Template uses Bootstrap 5 (RTL-friendly)
- ✅ Existing settings page is RTL-compatible
- ✅ No additional RTL work needed

### Recommended Template Structure
```html
<!-- My Published Posts Section -->
<div class="mt-5">
    <h2 class="h4 mb-3">
        <i class="fas fa-file-alt me-2"></i>پست‌های منتشر شده من
    </h2>
    
    {% if user_posts %}
        <div class="list-group">
            {% for post in user_posts %}
                <a href="{% url 'post_detail' post.slug %}" class="list-group-item list-group-item-action">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">{{ post.title }}</h5>
                        <small>{{ post.created_on|date:"Y/m/d" }}</small>
                    </div>
                    <p class="mb-1 text-muted small">{{ post.category.name }}</p>
                </a>
            {% endfor %}
        </div>
        
        <!-- Pagination -->
        {% if is_paginated %}
            <!-- Pagination controls -->
        {% endif %}
    {% else %}
        <div class="alert alert-info">
            <i class="fas fa-info-circle me-2"></i>
            شما هنوز پستی منتشر نکرده‌اید.
        </div>
    {% endif %}
</div>
```

---

## D) Performance Considerations

### N+1 Query Prevention
**Current Query (Optimized):**
```python
user_published_posts = Post.objects.filter(
    author=request.user,
    status=1,
    is_deleted=False
).select_related('category').order_by('-created_on')
```

**Optimization:**
- ✅ `select_related('category')` - Fetches category in same query (1 query instead of N+1)
- ✅ `select_related('author')` - Not needed (already filtered by `request.user`)
- ✅ No `prefetch_related` needed (no reverse relations accessed)

**Query Count:**
- Base query: 1 query for posts + categories
- With pagination: 1 query for posts, 1 query for count (if using `Paginator`)
- **Total: 2 queries** (acceptable)

### Pagination Impact
- **Without pagination:** If user has 100+ posts, page load may be slow
- **With pagination (15 items/page):** Fast load, minimal database impact
- **Recommendation:** Always use pagination (even if user has < 15 posts, for consistency)

### Database Indexes
**Current Indexes on Post Model:**
- ❌ **No composite index** on `(author, status, is_deleted)`
- ✅ `author` is ForeignKey (has index)
- ✅ `status` may have index (check database)
- ✅ `is_deleted` may have index (check database)

**Index Recommendation (Optional, Low Priority):**
```python
# In blog/models.py Post.Meta:
indexes = [
    models.Index(fields=['author', 'status', 'is_deleted', '-created_on']),
]
```

**Why Optional:**
- Most users will have < 50 published posts
- Query with `author=request.user` is already fast (FK index)
- Only needed if performance issues arise with users who have 100+ posts
- Can be added later via migration if needed

**Performance Risk:** **LOW** (most users have few posts)

---

## E) Security / Privacy Risks

### Risk 1: IDOR (Insecure Direct Object Reference)
**Risk:** User could potentially access other users' draft/unpublished posts by guessing URLs.

**Mitigation:**
- ✅ **Query filtering:** `author=request.user` ensures only current user's posts are queried
- ✅ **View-level check:** `@login_required` ensures user is authenticated
- ✅ **Post detail access:** `post_detail` view already filters `status=1` for public, but allows author/staff to see own posts
- ✅ **Edit/Delete routes:** Already enforce `request.user == post.author or request.user.is_staff` in views (not just templates)

**Verdict:** **LOW RISK** (properly mitigated by queryset filtering)

### Risk 2: Exposing Draft/Unpublished Posts
**Risk:** Accidentally showing drafts or pending review posts in the list.

**Mitigation:**
- ✅ **Query filter:** `status=1` ensures only published posts
- ✅ **Query filter:** `is_deleted=False` ensures soft-deleted posts are hidden
- ✅ **Double-check:** Test with user who has drafts (should not appear)

**Verdict:** **LOW RISK** (properly mitigated by query filters)

### Risk 3: Template-Level Authorization Only
**Risk:** If authorization is only checked in template (e.g., `{% if user == post.author %}`), it's insecure.

**Mitigation:**
- ✅ **View-level filtering:** Queryset uses `author=request.user` (enforced in view, not template)
- ✅ **Existing pattern:** `edit_post` and `delete_post` views already check authorization in views (lines 712, 809 in `blog/views.py`)
- ✅ **No template-only checks:** Template only displays what view provides

**Verdict:** **LOW RISK** (follows existing secure patterns)

### Security Checklist
- ✅ Only `request.user`'s posts are queried (view-level)
- ✅ Only published posts (`status=1`) are shown
- ✅ Soft-deleted posts are excluded (`is_deleted=False`)
- ✅ Edit/Delete routes already enforce owner/staff checks (existing implementation)
- ✅ Post detail access rules remain unchanged (existing implementation)

---

## F) Functional Risks / Edge Cases

### Edge Case 1: Soft-Deleted Posts
**Scenario:** User soft-deletes a post, then visits settings page.

**Expected Behavior:**
- ✅ Soft-deleted post should **NOT** appear in "My Published Posts" list
- ✅ Query already filters `is_deleted=False`

**Verdict:** **HANDLED** (query filter prevents this)

### Edge Case 2: Edited Published Posts Become Draft
**Scenario:** User edits a published post → status changes to `0` (Draft/Pending Review) → post disappears from "Published" list.

**Expected Behavior:**
- ✅ Post should **disappear** from "My Published Posts" list immediately after edit
- ✅ This is **expected and correct** behavior (only published posts should show)
- ✅ User can see it again after admin re-approves and publishes it

**User Communication:**
- ⚠️ **Important:** User should be informed that editing a published post will remove it from the "Published" list until re-approved
- ✅ **Existing message:** `edit_post` view already shows: "Your changes were saved and sent for review. The post will be reviewed before being published again." (line 774)

**Verdict:** **EXPECTED BEHAVIOR** (not a bug, but should be documented)

### Edge Case 3: Very Old Posts
**Scenario:** User has 100+ published posts.

**Expected Behavior:**
- ✅ Pagination handles this (15 items per page)
- ✅ User can navigate through pages
- ⚠️ **Optional:** Add search/filter for users with many posts (future enhancement)

**Verdict:** **HANDLED** (pagination prevents performance issues)

### Edge Case 4: User Has 0 Published Posts
**Scenario:** New user or user who only has drafts.

**Expected Behavior:**
- ✅ Show friendly empty state message
- ✅ Do not show empty list or error
- ✅ Message: "شما هنوز پستی منتشر نکرده‌اید" (You haven't published any posts yet)

**Verdict:** **HANDLED** (template handles empty queryset)

### Edge Case 5: Post Category Deleted
**Scenario:** Post's category is deleted (shouldn't happen due to `on_delete=models.PROTECT`, but edge case).

**Expected Behavior:**
- ✅ `select_related('category')` will still work (category exists)
- ✅ If category is somehow None, template should handle gracefully

**Verdict:** **LOW RISK** (protected by `on_delete=models.PROTECT`)

---

## G) Files to Change

### 1. `accounts/views.py`
**Changes:**
- Import `Post` model and `Paginator`
- Modify `account_settings` view to:
  - Query user's published posts
  - Apply pagination
  - Pass posts and pagination context to template

**Estimated Lines:** +15-20 lines

### 2. `templates/account/settings.html`
**Changes:**
- Add "My Published Posts" section
- Add list/card display for posts
- Add pagination controls
- Add empty state message

**Estimated Lines:** +30-50 lines

### 3. No Changes Needed
- ❌ `accounts/urls.py` (no URL changes)
- ❌ `blog/models.py` (no model changes)
- ❌ `blog/views.py` (edit/delete already work)
- ❌ `blog/urls.py` (post_detail route already exists)

---

## H) Recommended Implementation Approach

### Step 1: Update View
```python
# accounts/views.py
from django.core.paginator import Paginator
from blog.models import Post

@login_required
def account_settings(request):
    """Account settings page with user's published posts."""
    # Get user's published posts
    user_posts = Post.objects.filter(
        author=request.user,
        status=1,  # Published
        is_deleted=False
    ).select_related('category').order_by('-created_on')
    
    # Paginate (15 items per page)
    paginator = Paginator(user_posts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'account/settings.html', {
        'user_posts': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    })
```

### Step 2: Update Template
- Add section after existing cards (or after info alert)
- Use Bootstrap list-group or cards
- Add pagination controls
- Add empty state

### Step 3: Test
- Test with user who has 0 posts
- Test with user who has 1-15 posts (no pagination)
- Test with user who has 20+ posts (pagination)
- Test with user who has drafts (should not appear)
- Test with user who soft-deleted a post (should not appear)
- Test edit flow (published → draft → disappears from list)

---

## I) Risk Summary

| Risk | Severity | Likelihood | Mitigation | Status |
|------|----------|------------|------------|--------|
| IDOR (accessing others' posts) | High | Low | Query filters by `author=request.user` | ✅ Mitigated |
| Exposing drafts/unpublished | Medium | Low | Query filters `status=1` | ✅ Mitigated |
| Performance (many posts) | Medium | Medium | Pagination (15 items/page) | ✅ Mitigated |
| N+1 queries | Low | Medium | `select_related('category')` | ✅ Mitigated |
| Empty state UX | Low | High | Template handles empty queryset | ✅ Mitigated |
| Edited posts disappearing | Low | High | Expected behavior, documented | ⚠️ Documented |

**Overall Risk Level:** **LOW**

---

## J) Deliverables Summary

### ✅ Feasibility: **FEASIBLE**
- Low complexity
- Minimal code changes (2 files)
- No model/URL changes needed
- Follows existing patterns

### Files to Change:
1. `accounts/views.py` (+15-20 lines)
2. `templates/account/settings.html` (+30-50 lines)

### Recommended Approach:
- Simple list with pagination (15 items/page)
- Bootstrap list-group or cards
- Empty state message
- RTL-compatible (already supported)

### Security:
- ✅ View-level authorization (queryset filtering)
- ✅ Only published posts (`status=1`)
- ✅ Excludes soft-deleted (`is_deleted=False`)
- ✅ Edit/Delete routes already secure (existing)

### Performance:
- ✅ Optimized query (`select_related('category')`)
- ✅ Pagination prevents slow loads
- ⚠️ Optional index on `(author, status, is_deleted)` if needed later

### Edge Cases:
- ✅ Soft-deleted posts: Hidden (query filter)
- ⚠️ Edited published posts: Disappear from list (expected, documented)
- ✅ Many posts: Pagination handles it
- ✅ Zero posts: Empty state message
- ✅ Category deleted: Protected by `on_delete=models.PROTECT`

---

## K) Confirmation

**✅ No code changes were made; this is a read-only analysis.**

**✅ Ads were not modified or analyzed (out of scope).**

**✅ Only POSTS (blog/experiences) were analyzed.**

---

## L) Next Steps (If Approved)

1. Implement view changes (`accounts/views.py`)
2. Implement template changes (`templates/account/settings.html`)
3. Test all edge cases
4. Optional: Add database index if performance issues arise
5. Optional: Add search/filter for future enhancement

---

**Report Complete.** ✅

