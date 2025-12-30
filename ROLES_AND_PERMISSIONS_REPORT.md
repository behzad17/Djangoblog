# Roles & Capabilities - Technical Report

**Date:** 2025-12-29  
**Project:** Djangoblog PP4  
**Scope:** User Roles, Permissions, and Access Control Analysis  
**Status:** Read-Only Analysis (No Code Changes)

---

## A) Executive Summary

- **Role System:** The platform uses a **hybrid permission model** combining Django's built-in `is_staff`/`is_superuser` flags with custom profile-based permissions (`UserProfile.can_publish_without_approval`, `Moderator` model for Q&A experts)
- **Authentication:** Django Allauth with email/password and Google SSO; **site verification** (`is_site_verified`) required for all write actions (posts, comments, ads, questions)
- **Content Moderation:** **Admin-only** approval workflow for posts (regular users create drafts, experts auto-publish); comments auto-approved but can be moderated; **no user-level moderation tools** (no hide/delete by non-authors)
- **Expert System:** **Two separate expert concepts**: (1) Blog publishing experts (`UserProfile.can_publish_without_approval`) for auto-publishing posts, (2) Q&A moderators (`Moderator` model) for answering questions with private Q&A threads
- **Privacy Controls:** **Strong privacy** for Q&A system (admin sees metadata only, not content); posts/comments are public; ads require login to view details
- **Rate Limiting:** Comprehensive rate limiting on all write actions (posts: 5/h per user, 10/h per IP; comments: 20/m per IP; questions: 10/h per user, 20/h per IP; ads: 5/h per user, 10/h per IP)
- **Access Control:** **Template-level checks** minimal (mostly view-level); authorization enforced via decorators (`@login_required`, `@site_verified_required`) and view-level ownership checks
- **Missing Features:** No Django Groups/Permissions system in use; no user ban/suspend functionality; no content reporting system; no audit logs; no spam detection beyond rate limiting

---

## B) Roles Matrix

| Capability | Anonymous | Authenticated (Not Verified) | Authenticated (Verified) | Post Author | Expert Publisher | Moderator | Admin |
|------------|-----------|---------------------------|-------------------------|-------------|------------------|-----------|-------|
| **View Posts** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **View Comments** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **View Categories** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **View Expert Profiles** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **View Ads List** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **View Ad Details** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Create Post** | ❌ No | ❌ No | ✅ Yes (Draft) | ✅ Yes (Draft) | ✅ Yes (Published) | ✅ Yes (Draft) | ✅ Yes (Published) |
| **Edit Own Post** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Delete Own Post** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Publish Post** | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes (Auto) | ❌ No | ✅ Yes (Admin Panel) |
| **Add Comment** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Edit Own Comment** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Delete Own Comment** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Like Post** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Favorite Post** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Ask Question** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **View Own Questions** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Answer Questions** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes (Assigned) | ❌ No |
| **Create Ad** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Edit Own Ad** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Delete Own Ad** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Approve Post** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Pin Post** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Approve External URL** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Assign Moderator** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Grant Expert Access** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **View Q&A Metadata** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes (Metadata Only) |
| **View Q&A Content** | ❌ No | ❌ No | ✅ Yes (Own Only) | ✅ Yes (Own Only) | ✅ Yes (Own Only) | ✅ Yes (Assigned) | ❌ No (Content Hidden) |
| **Delete Any Post** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Delete Any Comment** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Ban/Suspend User** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No (Not Implemented) |
| **Report Content** | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No (Not Implemented) |

**Legend:**
- ✅ = Allowed
- ❌ = Not Allowed
- **Expert Publisher** = User with `UserProfile.can_publish_without_approval=True`
- **Moderator** = User with `Moderator` profile (Q&A expert)
- **Verified** = User with `UserProfile.is_site_verified=True`

---

## C) Permission Implementation Notes

### C.1 Authentication & Authorization Decorators

**Location:** `blog/decorators.py`, `blog/views.py`, `askme/views.py`, `ads/views.py`

**Key Decorators:**
1. **`@login_required`** (Django built-in)
   - **Usage:** 24+ views across `blog/views.py`, `askme/views.py`, `ads/views.py`
   - **Enforcement:** Redirects to login if not authenticated
   - **Examples:** `post_detail`, `create_post`, `edit_post`, `comment_edit`, `ask_question`, `ad_detail`

2. **`@site_verified_required`** (Custom decorator)
   - **Location:** `blog/decorators.py:7-38`
   - **Purpose:** Requires `UserProfile.is_site_verified=True` for write actions
   - **Enforcement:** Redirects to `complete_setup` if not verified
   - **Usage:** All post/comment/ad/question creation/editing views
   - **Code Pattern:**
     ```python
     if not request.user.profile.is_site_verified:
         return redirect('complete_setup')
     ```

3. **`@ratelimit`** (django-ratelimit)
   - **Usage:** Rate limiting on write actions
   - **Examples:**
     - Posts: `@ratelimit(key='user', rate='5/h')` + `@ratelimit(key='ip', rate='10/h')`
     - Comments: `@ratelimit(key='ip', rate='20/m')`
     - Questions: `@ratelimit(key='user', rate='10/h')` + `@ratelimit(key='ip', rate='20/h')`
     - Ads: `@ratelimit(key='user', rate='5/h')` + `@ratelimit(key='ip', rate='10/h')`

### C.2 Ownership-Based Authorization

**Location:** `blog/views.py`, `ads/views.py`

**Pattern:** View-level checks comparing `request.user` with object owner

**Examples:**
1. **Post Edit/Delete** (`blog/views.py:600-616, 667-680`)
   ```python
   if request.user != post.author:
       messages.error(request, 'You can only edit your own posts!')
       return redirect('post_detail', slug=slug)
   ```

2. **Comment Edit/Delete** (`blog/views.py:340-379, 382-406`)
   ```python
   if request.user == comment.author:
       # Allow edit/delete
   else:
       messages.error(request, 'You can only edit your own comments!')
   ```

3. **Ad Edit/Delete** (`ads/views.py:153, 187`)
   ```python
   if request.user != ad.user:
       messages.error(request, 'You can only edit your own ads!')
   ```

### C.3 Role-Based Checks

**Location:** `blog/views.py`, `askme/views.py`

**Expert Publishing Check:**
- **Location:** `blog/views.py:546-556`
- **Pattern:**
  ```python
  is_expert = (
      hasattr(request.user, 'profile') and
      request.user.profile.can_publish_without_approval
  )
  if is_expert:
      post.status = 1  # Published
  else:
      post.status = 0  # Draft
  ```

**Moderator Check:**
- **Location:** `askme/views.py:185-193`
- **Pattern:**
  ```python
  if not hasattr(request.user, 'moderator_profile'):
      messages.error(request, 'You are not a moderator.')
      return redirect('ask_me')
  moderator = request.user.moderator_profile
  questions = Question.objects.filter(moderator=moderator)
  ```

### C.4 Django Groups/Permissions

**Status:** ❌ **NOT IMPLEMENTED**

- No Django Groups are used
- No custom permissions defined in model `Meta.permissions`
- Role assignment is done via:
  - `User.is_staff` / `User.is_superuser` (Django admin access)
  - `UserProfile.can_publish_without_approval` (expert publishing)
  - `Moderator` model existence (Q&A expert)

### C.5 Template-Level Permission Checks

**Status:** ⚠️ **MINIMAL**

- **Finding:** No template-level permission checks found in templates
- **Implication:** All access control is enforced at view level
- **Recommendation:** Add template guards for better UX (hide buttons/links if user lacks permission)

---

## D) Moderation & Safety Controls

### D.1 Current Moderation Features

**Post Moderation:**
- ✅ **Draft/Published Status:** Regular users create drafts (`status=0`), experts auto-publish (`status=1`)
- ✅ **Admin Approval:** Admin must approve drafts via Django admin panel (`blog/admin.py:20-53`)
- ✅ **External URL Approval:** Admin must approve external URLs (`url_approved` field, `blog/admin.py:45-52`)
- ✅ **Pin Control:** Admin can pin posts to homepage (`pinned`, `pinned_row` fields)
- ❌ **No User-Level Moderation:** Users cannot hide/delete others' posts
- ❌ **No Reporting System:** No way for users to report inappropriate posts

**Comment Moderation:**
- ✅ **Auto-Approval:** Comments are auto-approved (`approved=True` by default, `blog/models.py:200`)
- ✅ **Author Control:** Comment authors can edit/delete their own comments
- ❌ **No Admin Moderation UI:** Comments registered in admin but no dedicated moderation interface
- ❌ **No Hide/Delete by Others:** Only authors can delete comments
- ❌ **No Reporting System:** No way to report inappropriate comments

**Q&A Moderation:**
- ✅ **Private Threads:** Questions/answers are private (only user and moderator see content)
- ✅ **Admin Metadata Access:** Admin sees metadata only (timestamps, status, user info) but NOT content (`askme/admin.py:61-192`)
- ✅ **Moderator Assignment:** Admin assigns moderators via admin panel
- ❌ **No Content Moderation:** No way to moderate question/answer content (relies on privacy)

**User Moderation:**
- ❌ **No Ban/Suspend:** No functionality to ban or suspend users
- ❌ **No Account Lockout:** No automatic lockout after failed login attempts (rate limiting only)
- ✅ **Site Verification:** Users must complete site verification for write actions

### D.2 Spam Prevention

**Rate Limiting:**
- ✅ **Post Creation:** 5/hour per user, 10/hour per IP
- ✅ **Comment Creation:** 20/minute per IP
- ✅ **Question Creation:** 10/hour per user, 20/hour per IP
- ✅ **Ad Creation:** 5/hour per user, 10/hour per IP
- ✅ **Login/Signup:** 5/minute per IP

**CAPTCHA:**
- ✅ **Registration:** CAPTCHA on signup form (`accounts/forms.py`)

**Honeypot:**
- ✅ **Comments:** Honeypot field in comment form (`blog/forms.py`)

**Missing:**
- ❌ **No Spam Detection:** No automated spam detection (e.g., Akismet, custom ML)
- ❌ **No Content Filtering:** No profanity/blacklist filtering
- ❌ **No IP Blocking:** No IP-based blocking system

### D.3 Audit & Logging

**Status:** ❌ **NOT IMPLEMENTED**

- No audit logs for user actions
- No logging of permission changes
- No tracking of admin actions
- No content modification history

**Recommendation:** Implement Django's `LogEntry` model or custom audit logging

---

## E) Expert/Specialist System

### E.1 Two Separate Expert Concepts

**1. Blog Publishing Experts (`UserProfile.can_publish_without_approval`)**
- **Model:** `blog/models.py:11-62`
- **Purpose:** Users who can publish posts without admin approval
- **Assignment:** Admin grants via `UserProfileAdmin` (`blog/admin.py:56-111`)
- **Behavior:** Posts auto-publish (`status=1`) on creation
- **Display:** Expert posts shown in "Expert Content" sidebar (`blog/views.py:129, 248-253`)

**2. Q&A Moderators (`Moderator` model)**
- **Model:** `askme/models.py:13-116`
- **Purpose:** Expert consultants who answer questions
- **Fields:**
  - `expert_title` (e.g., "Lawyer", "Doctor")
  - `field_specialty` (e.g., "Legal", "Medical")
  - `bio`, `disclaimer`, `profile_image`
  - `slug` (for expert profile pages)
- **Assignment:** Admin creates `Moderator` record linked to User
- **Behavior:** Can answer questions assigned to them
- **Display:** Listed on `/ask-me/` page, have dedicated profile pages (`/expert/<slug>/`)

### E.2 Expert Profile Pages

**Implementation:**
- **View:** `askme/views.py:48-73` (`expert_profile`)
- **URL:** `/expert/<slug>/`
- **Template:** `askme/templates/askme/expert_profile.html`
- **Features:**
  - Display expert name, title, field, bio
  - Show custom disclaimer
  - Link to ask question
  - Profile image

### E.3 Expert Publishing Workflow

**Regular User:**
1. Creates post → `status=0` (Draft)
2. Admin reviews in admin panel
3. Admin changes `status=1` (Published)
4. Post appears on site

**Expert User:**
1. Creates post → `status=1` (Published) automatically
2. Post appears immediately (no admin approval needed)
3. Admin can still edit/delete if needed

**Code Location:** `blog/views.py:546-556`

### E.4 Q&A Expert Workflow

**User:**
1. Views expert list on `/ask-me/`
2. Clicks expert → redirected to expert profile or question form
3. Submits question → private thread created
4. Views own questions on `/my-questions/`

**Moderator:**
1. Accesses moderator dashboard (`/moderator-dashboard/`)
2. Sees all questions assigned to them
3. Answers questions (private, only user sees answer)
4. Marks as answered

**Admin:**
1. Sees Q&A metadata in admin (timestamps, status, user info)
2. **Cannot see question/answer content** (privacy protection)
3. Can assign moderators, view statistics

**Code Locations:**
- Question creation: `askme/views.py:79-122`
- Moderator dashboard: `askme/views.py:185-222`
- Admin interface: `askme/admin.py:61-192`

---

## F) Community Impact Features

### F.1 Individual User Capabilities (افراد)

**Content Creation:**
- ✅ **Posts:** Create, edit, delete own posts (drafts require approval, experts auto-publish)
- ✅ **Comments:** Add, edit, delete own comments on any post
- ✅ **Questions:** Ask questions to experts (private Q&A)
- ✅ **Ads:** Create, edit, delete own ads (classifieds)

**Content Interaction:**
- ✅ **Likes:** Like posts (tracked but not prominently displayed)
- ✅ **Favorites:** Bookmark posts for later
- ✅ **Search:** Search posts by keyword
- ✅ **Categories:** Filter posts by category

**Profile & Settings:**
- ✅ **Profile:** User profile with expert status tracking
- ✅ **Site Verification:** Required for write actions (terms acceptance, profile completion)
- ✅ **Account Management:** Login, logout, password reset, Google SSO

**Privacy:**
- ✅ **Own Questions:** View own Q&A threads with experts
- ✅ **Own Content:** Full control over own posts/comments/ads

### F.2 Community Capabilities (جامعه)

**Knowledge Sharing:**
- ✅ **Public Posts:** All published posts visible to community
- ✅ **Expert Content:** Dedicated sidebar showing expert posts
- ✅ **Categories:** Organized content by topic (Economy, Education, Events, etc.)
- ✅ **Comments:** Community discussion on posts

**Expert Consultation:**
- ✅ **Ask Me System:** Community members can ask questions to experts
- ✅ **Expert Profiles:** Public expert profiles with bios, specialties, disclaimers
- ✅ **Private Q&A:** Secure private communication between users and experts

**Classifieds:**
- ✅ **Ads System:** Community members can post classified ads
- ✅ **Ad Categories:** Organized ads by category
- ✅ **Favorites:** Save favorite ads

**Content Discovery:**
- ✅ **Homepage:** 24 posts per page (4 columns × 6 rows)
- ✅ **Pinned Posts:** Admin can pin important posts
- ✅ **Related Posts:** Related posts shown on detail pages
- ✅ **Search:** Full-text search across posts

**Missing Community Features:**
- ❌ **No User Profiles:** No public user profile pages
- ❌ **No Follow System:** Cannot follow other users
- ❌ **No Notifications:** No notification system for replies, answers, etc.
- ❌ **No Tags:** No tag system (only categories)
- ❌ **No Trending:** No trending/popular content algorithm
- ❌ **No Community Guidelines:** No visible community guidelines/rules
- ❌ **No Moderation Tools:** Community cannot report or flag content

---

## G) Recommendations

### G.1 High Priority (Security & Moderation)

1. **Implement Content Reporting System**
   - **Priority:** 🔴 **CRITICAL**
   - **Impact:** Allows community to report inappropriate content
   - **Implementation:** Add `Report` model with fields: `reporter`, `content_type`, `object_id`, `reason`, `status`
   - **Location:** New `reports` app or add to `blog` app
   - **Admin:** Admin dashboard to review reports

2. **Add User Ban/Suspend Functionality**
   - **Priority:** 🔴 **CRITICAL**
   - **Impact:** Ability to ban/suspend abusive users
   - **Implementation:** Add `is_banned`, `banned_until`, `ban_reason` to `UserProfile`
   - **Middleware:** Check ban status on each request
   - **Admin:** Admin interface to ban/unban users

3. **Implement Audit Logging**
   - **Priority:** 🟡 **HIGH**
   - **Impact:** Track admin actions, content modifications, permission changes
   - **Implementation:** Use Django's `LogEntry` or custom `AuditLog` model
   - **Fields:** `user`, `action`, `content_type`, `object_id`, `timestamp`, `ip_address`
   - **Admin:** View audit logs in admin panel

4. **Add Comment Moderation UI**
   - **Priority:** 🟡 **HIGH**
   - **Impact:** Better comment moderation workflow
   - **Implementation:** Admin interface to approve/reject/hide comments
   - **Features:** Bulk actions, filter by status, search

### G.2 Medium Priority (User Experience)

5. **Implement Django Groups/Permissions**
   - **Priority:** 🟡 **MEDIUM**
   - **Impact:** More flexible role management
   - **Implementation:** Create Groups: "Moderators", "Expert Publishers", "Trusted Users"
   - **Migration:** Migrate existing role assignments to Groups
   - **Benefits:** Easier to manage permissions, can assign multiple roles

6. **Add Template-Level Permission Checks**
   - **Priority:** 🟡 **MEDIUM**
   - **Impact:** Better UX (hide buttons/links user can't use)
   - **Implementation:** Add `{% if user.is_authenticated %}`, `{% if user.profile.can_publish_without_approval %}` checks
   - **Templates:** `post_detail.html`, `index.html`, etc.

7. **Implement User Profile Pages**
   - **Priority:** 🟡 **MEDIUM**
   - **Impact:** Community members can see each other's profiles
   - **Implementation:** Create `user_profile` view, template
   - **Features:** Display user's posts, comments, join date, expert status

8. **Add Notification System**
   - **Priority:** 🟡 **MEDIUM**
   - **Impact:** Users notified of replies, answers, mentions
   - **Implementation:** Create `Notification` model, middleware to show notifications
   - **Features:** Email notifications (optional), in-app notifications

### G.3 Low Priority (Enhancements)

9. **Add Spam Detection**
   - **Priority:** 🟢 **LOW**
   - **Impact:** Automated spam detection
   - **Implementation:** Integrate Akismet or custom ML model
   - **Features:** Auto-flag suspicious content, admin review queue

10. **Implement Content Filtering**
    - **Priority:** 🟢 **LOW**
    - **Impact:** Filter profanity, blacklisted words
    - **Implementation:** Add `clean_content()` method to forms
    - **Features:** Configurable word list, replacement with asterisks

11. **Add Account Lockout Policy**
    - **Priority:** 🟢 **LOW**
    - **Impact:** Prevent brute-force attacks
    - **Implementation:** Track failed login attempts, lock account after N attempts
    - **Features:** Configurable lockout duration, admin unlock

12. **Implement Trending/Popular Content Algorithm**
    - **Priority:** 🟢 **LOW**
    - **Impact:** Surface popular content to community
    - **Implementation:** Calculate popularity score based on views, likes, comments, recency
    - **Features:** "Trending" section on homepage, "Popular This Week" widget

---

## Appendix: Key Files Reference

### Models
- **User Roles:** `blog/models.py` (UserProfile), `askme/models.py` (Moderator, Question)
- **Content:** `blog/models.py` (Post, Comment, Category), `ads/models.py` (Ad, AdCategory)

### Views & Authorization
- **Blog:** `blog/views.py` (24+ views with `@login_required`, `@site_verified_required`)
- **Q&A:** `askme/views.py` (4 views with authentication checks)
- **Ads:** `ads/views.py` (7 views with `@login_required`)
- **Decorators:** `blog/decorators.py` (`site_verified_required`)

### Admin
- **Blog Admin:** `blog/admin.py` (PostAdmin, UserProfileAdmin, CategoryAdmin)
- **Q&A Admin:** `askme/admin.py` (ModeratorAdmin, QuestionAdmin with privacy protection)
- **Ads Admin:** `ads/admin.py` (AdAdmin, AdCategoryAdmin)

### Settings
- **Authentication:** `codestar/settings.py` (Django Allauth, Google SSO)
- **Rate Limiting:** `codestar/urls.py` (rate limits on auth endpoints)

---

**Report Generated:** 2025-12-29  
**Analysis Method:** Codebase inspection, pattern matching, documentation review  
**Confidence Level:** High (based on comprehensive code analysis)

