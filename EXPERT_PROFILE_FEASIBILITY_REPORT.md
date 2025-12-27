# Expert Profile UI - Technical Feasibility Report

**Date:** 2025-02-07  
**Project:** Djangoblog PP4  
**Feature:** Expert Profile UI Template/Page  
**Reviewer:** AI Code Assistant

---

## Executive Summary

**Status:** ✅ **FEASIBLE**

The proposed Expert Profile UI feature is **technically feasible** and can be implemented with minimal risk. The codebase already has a `Moderator` model in the `askme` app that represents experts, with most required fields already present. The implementation requires adding a few missing fields, creating a detail view/template, and adding URL routing.

**Estimated Complexity:** Low-Medium  
**Estimated Development Time:** 1-2 days  
**Risk Level:** Low

---

## 1. Current Expert Representation Analysis

### 1.1 Expert Models in Codebase

The codebase has **TWO distinct "Expert" concepts**:

#### A) Blog Publishing Experts (`UserProfile` model - `blog/models.py`)
- **Purpose:** Users who can publish blog posts without admin approval
- **Model:** `UserProfile` (OneToOne with User)
- **Key Field:** `can_publish_without_approval` (Boolean)
- **Location:** `blog/models.py:11-62`
- **Usage:** Used in `blog/views.py` to filter expert posts for sidebar content

#### B) Q&A Moderators/Experts (`Moderator` model - `askme/models.py`)
- **Purpose:** Expert consultants who answer questions in the "Ask Me" Q&A system
- **Model:** `Moderator` (OneToOne with User)
- **Location:** `askme/models.py:11-77`
- **Current Fields:**
  - ✅ `user` (OneToOneField to User)
  - ✅ `expert_title` (CharField, max_length=100) - **Job title**
  - ✅ `complete_name` (CharField, max_length=200, blank=True) - **Name**
  - ✅ `profile_image` (CloudinaryField) - Profile image
  - ✅ `bio` (TextField, blank=True) - **Short description**
  - ✅ `is_active` (BooleanField)
  - ✅ `created_on`, `updated_on` (DateTimeFields)

### 1.2 Current Expert Display

**Where Experts Are Listed:**
- **Path:** `/ask-me/` (Ask Me page)
- **View:** `askme/views.py:17-45` (`ask_me` function)
- **Template:** `askme/templates/askme/ask_me.html`
- **What's Displayed:**
  - Moderator cards showing: name, expert_title, bio (truncated), profile image, question count
  - Grid layout with clickable cards to ask questions

**Current URLs:**
- `/ask-me/` - List all active moderators
- `/ask-me/moderator/<int:moderator_id>/ask/` - Ask question to moderator
- `/ask-me/moderator/dashboard/` - Moderator's own dashboard
- `/ask-me/my-questions/` - User's questions
- `/ask-me/question/<int:question_id>/answer/` - Answer question

**Individual Profile Pages:**
- ❌ **NO individual expert profile detail page exists**
- ❌ **NO slug-based URLs for experts**
- ❌ **NO `/experts/<slug>/` or `/experts/<username>/` routes**

### 1.3 Missing Fields for Requirements

Based on the requirements, the `Moderator` model is missing:
- ❌ **Field/Specialty** (domain) - Not present
- ❌ **Disclaimer** (custom text) - Not present
- ❌ **Slug field** - Not present (needed for clean URLs)

**Note:** The `Moderator` model already has:
- ✅ Name (`complete_name` or fallback to `user.get_full_name()` or `username`)
- ✅ Title (`expert_title`)
- ✅ Bio (`bio`)

---

## 2. Technical Approach Options

### Option A: Extend UserProfile Model (Blog App)

**Approach:** Add expert profile fields to existing `UserProfile` model + boolean flag.

**Pros:**
- Single profile model for all users
- Unified expert concept across blog and Q&A

**Cons:**
- ❌ **BLOCKER:** `UserProfile` is for blog publishing experts, not Q&A moderators
- ❌ **BLOCKER:** Two separate expert concepts exist (blog experts vs Q&A moderators)
- ❌ Would require merging two different expert systems
- ❌ High impact on existing code (views, templates, admin)
- ❌ Risk of breaking existing functionality

**Required Changes:**
- Add fields to `UserProfile`: `expert_title`, `field_specialty`, `expert_bio`, `expert_disclaimer`, `expert_slug`
- Add `is_expert` boolean (or use existing `can_publish_without_approval`)
- Create migration
- Update all views that reference experts
- Update admin interface

**Impact:** HIGH - Would require refactoring both blog and askme apps

**Recommendation:** ❌ **NOT RECOMMENDED** - Too disruptive, two separate expert concepts

---

### Option B: Extend Moderator Model (Ask Me App) - **RECOMMENDED**

**Approach:** Add missing fields to existing `Moderator` model and create profile detail page.

**Pros:**
- ✅ **Minimal changes** - Model already exists with most fields
- ✅ **Clear separation** - Q&A experts are already represented by Moderator
- ✅ **Low risk** - No impact on blog publishing experts
- ✅ **Natural fit** - Moderator model already has expert_title, bio, profile_image
- ✅ **Existing infrastructure** - Admin interface, views, templates already exist

**Cons:**
- Only covers Q&A moderators, not blog publishing experts
- If you want blog experts to also have profiles, would need separate implementation

**Required Changes:**
1. **Model Changes** (`askme/models.py`):
   ```python
   # Add to Moderator model:
   field_specialty = models.CharField(max_length=200, blank=True, help_text="Field/Specialty domain")
   disclaimer = models.TextField(blank=True, help_text="Custom disclaimer text for this expert")
   slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly identifier")
   ```

2. **Migration:**
   - Create migration: `python manage.py makemigrations askme`
   - Run migration: `python manage.py migrate`

3. **Model Methods:**
   - Add `get_absolute_url()` method
   - Add `save()` override to auto-generate slug from name/username

4. **View:**
   - Create `expert_profile(request, slug)` view in `askme/views.py`

5. **Template:**
   - Create `askme/templates/askme/expert_profile.html`

6. **URL:**
   - Add route: `path('expert/<slug:slug>/', views.expert_profile, name='expert_profile')`

7. **Admin:**
   - Update `ModeratorAdmin` to include new fields

**Impact:** LOW - Isolated to askme app, no breaking changes

**Recommendation:** ✅ **RECOMMENDED** - Best fit for current architecture

---

### Option C: Create Separate ExpertProfile Model

**Approach:** Create new `ExpertProfile` model linked to User (OneToOne/ForeignKey), separate from Moderator.

**Pros:**
- Clean separation of concerns
- Could unify blog and Q&A experts under one model

**Cons:**
- ❌ **BLOCKER:** Would create a THIRD expert concept (blog experts, Q&A moderators, now profile experts)
- ❌ Duplication - Moderator model already exists
- ❌ More complex - Need to sync Moderator and ExpertProfile
- ❌ Higher maintenance burden

**Required Changes:**
- Create new `ExpertProfile` model
- Create migration
- Create views, templates, URLs
- Handle synchronization with Moderator model (if needed)
- Update admin interface

**Impact:** MEDIUM - New model, but isolated

**Recommendation:** ❌ **NOT RECOMMENDED** - Unnecessary duplication, adds complexity

---

## 3. Detailed Analysis: Option B (Recommended)

### 3.1 Required Database Changes

**New Fields to Add to `Moderator` Model:**

| Field | Type | Required | Default | Purpose |
|-------|------|----------|---------|---------|
| `field_specialty` | CharField(200) | No | blank=True | Field/Specialty domain |
| `disclaimer` | TextField | No | blank=True | Custom disclaimer text |
| `slug` | SlugField(200) | Yes | unique=True | URL-friendly identifier |

**Migration Impact:**
- ✅ **Safe** - All new fields are optional (blank=True)
- ✅ **No data loss** - Existing Moderator records will have empty values
- ✅ **Backward compatible** - Existing code will continue to work

**Database Schema:**
```sql
ALTER TABLE askme_moderator 
ADD COLUMN field_specialty VARCHAR(200) DEFAULT '',
ADD COLUMN disclaimer TEXT DEFAULT '',
ADD COLUMN slug VARCHAR(200) UNIQUE DEFAULT '';
```

### 3.2 Impact on Existing Users/Content

**Existing Moderators:**
- ✅ **No breaking changes** - All existing fields remain
- ✅ **Graceful degradation** - New fields are optional
- ⚠️ **Action required:** Admin must populate `slug` field for existing moderators (or auto-generate via migration)

**Existing Views/Templates:**
- ✅ **No changes required** - Existing `/ask-me/` page continues to work
- ✅ **Additive only** - New profile page is additional feature

**Existing URLs:**
- ✅ **No conflicts** - New `/ask-me/expert/<slug>/` route doesn't conflict with existing routes

### 3.3 Editing Capabilities

**Current Admin Interface:**
- Location: `askme/admin.py:12-52` (`ModeratorAdmin`)
- Fields currently editable: `user`, `expert_title`, `complete_name`, `profile_image`, `bio`, `is_active`
- Access: Admin-only (Django admin)

**Recommended Approach:**
- **Admin-only editing** (current approach)
  - ✅ Simple - No new permissions needed
  - ✅ Consistent with current Moderator management
  - ✅ Secure - Only trusted admins can edit expert profiles

**Alternative: Expert Self-Edit**
- Would require:
  - New view: `edit_expert_profile(request)`
  - New form: `ExpertProfileForm`
  - Permission check: `if request.user.moderator_profile == expert`
  - URL: `/ask-me/expert/<slug>/edit/`
- **Recommendation:** Start with admin-only, add self-edit later if needed

### 3.4 Template & Rendering

**Template Location:**
- `askme/templates/askme/expert_profile.html`

**Template Structure:**
```django
{% extends "base.html" %}
{% block content %}
  <div class="expert-profile">
    <h1>{{ moderator.get_display_name }}</h1>
    <h2>{{ moderator.expert_title }}</h2>
    {% if moderator.field_specialty %}
      <p><strong>Field:</strong> {{ moderator.field_specialty }}</p>
    {% endif %}
    {% if moderator.bio %}
      <div class="bio">{{ moderator.bio|linebreaks }}</div>
    {% endif %}
    {% if moderator.disclaimer %}
      <div class="disclaimer">{{ moderator.disclaimer|linebreaks }}</div>
    {% elif default_disclaimer %}
      <div class="disclaimer">{{ default_disclaimer|linebreaks }}</div>
    {% endif %}
    <!-- Additional content: stats, posts, etc. -->
  </div>
{% endblock %}
```

**Context Data:**
```python
{
    'moderator': moderator,
    'default_disclaimer': settings.EXPERT_DEFAULT_DISCLAIMER,  # Optional
}
```

**View Implementation:**
```python
def expert_profile(request, slug):
    """Display individual expert profile page."""
    moderator = get_object_or_404(
        Moderator.objects.select_related('user'),
        slug=slug,
        is_active=True
    )
    return render(request, 'askme/expert_profile.html', {
        'moderator': moderator,
    })
```

### 3.5 URL Structure Recommendation

**Recommended URL Pattern:**
```
/ask-me/expert/<slug>/
```

**Rationale:**
- ✅ Consistent with existing `/ask-me/` namespace
- ✅ Clear semantic meaning
- ✅ Doesn't conflict with existing routes
- ✅ SEO-friendly (slug-based)

**Alternative Options:**
- `/experts/<slug>/` - Separate namespace (would require new app or URL include)
- `/ask-me/moderator/<slug>/` - More verbose, but clearer
- `/ask-me/<slug>/` - Too generic, might conflict with future routes

**URL Configuration:**
```python
# askme/urls.py
urlpatterns = [
    path('', views.ask_me, name='ask_me'),
    path('expert/<slug:slug>/', views.expert_profile, name='expert_profile'),  # NEW
    path('moderator/<int:moderator_id>/ask/', views.ask_question, name='ask_question'),
    # ... existing routes
]
```

**Slug Generation:**
- Auto-generate from `complete_name` or `user.username` on save
- Ensure uniqueness (handle duplicates with `-1`, `-2`, etc.)
- Make slug editable in admin for manual override

---

## 4. Disclaimer Behavior

### 4.1 Per-Expert Disclaimer

**Implementation:**
- Store in `Moderator.disclaimer` field (TextField)
- Display on profile page if present
- Allow admin to edit per-expert

**Pros:**
- ✅ Flexible - Each expert can have custom disclaimer
- ✅ Simple - Just a model field

**Cons:**
- None significant

### 4.2 Site-Wide Default Disclaimer

**Option 1: Django Settings**
```python
# codestar/settings.py
EXPERT_DEFAULT_DISCLAIMER = """
This expert provides advice in a consulting capacity only.
Their responses do not constitute legal, medical, or professional advice.
"""
```

**Option 2: Database Model (SiteSettings)**
- Create `SiteSettings` model with `default_expert_disclaimer` field
- More flexible, editable via admin without code changes

**Option 3: Template Variable**
- Hardcode in template (not recommended - not flexible)

**Recommended Approach:**
- **Option 1 (Settings)** for MVP - Simple, no DB changes
- **Option 2 (Model)** for production - More flexible, admin-editable

**Display Logic:**
```django
{% if moderator.disclaimer %}
  <div class="disclaimer">{{ moderator.disclaimer|linebreaks }}</div>
{% elif default_disclaimer %}
  <div class="disclaimer">{{ default_disclaimer|linebreaks }}</div>
{% endif %}
```

---

## 5. Files/Classes That Will Change

### 5.1 Model Changes

**File:** `askme/models.py`
- **Class:** `Moderator`
- **Changes:**
  - Add `field_specialty` field
  - Add `disclaimer` field
  - Add `slug` field
  - Add `get_absolute_url()` method
  - Override `save()` to auto-generate slug

### 5.2 View Changes

**File:** `askme/views.py`
- **New Function:** `expert_profile(request, slug)`

### 5.3 URL Changes

**File:** `askme/urls.py`
- **New Route:** `path('expert/<slug:slug>/', views.expert_profile, name='expert_profile')`

### 5.4 Template Changes

**New File:** `askme/templates/askme/expert_profile.html`
- Create new template for expert profile page

**Optional Update:** `askme/templates/askme/ask_me.html`
- Add links to expert profiles from moderator cards

### 5.5 Admin Changes

**File:** `askme/admin.py`
- **Class:** `ModeratorAdmin`
- **Changes:**
  - Add new fields to `fieldsets`
  - Add `slug` to `list_display` (optional)
  - Add `slug` to `search_fields` (optional)

### 5.6 Migration

**New File:** `askme/migrations/XXXX_add_expert_profile_fields.py`
- Generated automatically via `makemigrations`

### 5.7 Settings (Optional)

**File:** `codestar/settings.py`
- **Optional:** Add `EXPERT_DEFAULT_DISCLAIMER` setting

---

## 6. Potential Blockers & Considerations

### 6.1 No Blockers Identified

✅ **Expert concept exists** - `Moderator` model already represents experts  
✅ **Profile model exists** - `Moderator` has most required fields  
✅ **No slug conflicts** - No existing slug-based routes in askme app  
✅ **Backward compatible** - All changes are additive

### 6.2 Considerations

**1. Slug Uniqueness:**
- Need to handle duplicate slugs (e.g., two experts with same name)
- Solution: Auto-append `-1`, `-2`, etc., or use `user.username` as fallback

**2. Existing Moderators:**
- Need to populate `slug` for existing records
- Solution: Data migration or admin manual entry

**3. Blog Publishing Experts:**
- Current implementation only covers Q&A moderators
- If blog publishing experts (`UserProfile.can_publish_without_approval=True`) also need profiles, would need separate implementation
- **Recommendation:** Start with Q&A moderators, extend later if needed

**4. URL Naming:**
- Current route uses `moderator_id` (integer), new route uses `slug` (string)
- **No conflict** - Different parameter types

**5. Template Styling:**
- New template will need CSS/styling
- Can reuse existing moderator card styles from `ask_me.html`

---

## 7. Implementation Checklist

### Phase 1: Model & Database
- [ ] Add `field_specialty` field to `Moderator` model
- [ ] Add `disclaimer` field to `Moderator` model
- [ ] Add `slug` field to `Moderator` model
- [ ] Add `get_absolute_url()` method
- [ ] Override `save()` to auto-generate slug
- [ ] Create and run migration
- [ ] Populate slugs for existing moderators (data migration or manual)

### Phase 2: View & URL
- [ ] Create `expert_profile(request, slug)` view
- [ ] Add URL route to `askme/urls.py`
- [ ] Test URL routing

### Phase 3: Template
- [ ] Create `expert_profile.html` template
- [ ] Add styling/CSS
- [ ] Test template rendering

### Phase 4: Admin
- [ ] Update `ModeratorAdmin` to include new fields
- [ ] Test admin interface

### Phase 5: Integration
- [ ] Add links to expert profiles from moderator cards (optional)
- [ ] Add site-wide disclaimer setting (optional)
- [ ] Test end-to-end flow

### Phase 6: Testing
- [ ] Test with existing moderators
- [ ] Test with new moderators
- [ ] Test slug generation/uniqueness
- [ ] Test disclaimer display (per-expert and default)

---

## 8. Summary & Recommendation

### Status: ✅ **FEASIBLE**

### Recommended Approach: **Option B - Extend Moderator Model**

**Rationale:**
1. ✅ **Minimal changes** - Model already exists with most fields
2. ✅ **Low risk** - Isolated to askme app, no breaking changes
3. ✅ **Natural fit** - Moderator model already represents Q&A experts
4. ✅ **Quick implementation** - Estimated 1-2 days

### Implementation Summary:

**Required Fields:**
- ✅ Name - Already exists (`complete_name` or fallback)
- ✅ Title - Already exists (`expert_title`)
- ⚠️ Field/Specialty - **Need to add** (`field_specialty`)
- ✅ Bio - Already exists (`bio`)
- ⚠️ Disclaimer - **Need to add** (`disclaimer`)
- ⚠️ Slug - **Need to add** (`slug`)

**Required Components:**
- ✅ Model - Exists, needs 3 new fields
- ⚠️ View - **Need to create** (`expert_profile`)
- ⚠️ Template - **Need to create** (`expert_profile.html`)
- ⚠️ URL - **Need to add** (`/ask-me/expert/<slug>/`)
- ✅ Admin - Exists, needs field updates

### Next Steps:

1. **Confirm scope:** Are we only implementing profiles for Q&A moderators, or also for blog publishing experts?
2. **Design approval:** Review template design/mockup
3. **Disclaimer strategy:** Decide on site-wide default disclaimer approach
4. **Slug strategy:** Confirm auto-generation approach for existing moderators

---

## 9. Alternative: Unified Expert Profile System

If the goal is to have **one unified expert profile system** that covers both:
- Blog publishing experts (`UserProfile.can_publish_without_approval=True`)
- Q&A moderators (`Moderator`)

Then a **hybrid approach** would be needed:

1. Create `ExpertProfile` model (OneToOne with User)
2. Link both `UserProfile` experts and `Moderator` experts to `ExpertProfile`
3. Create unified profile page that works for both types

**Complexity:** Medium-High  
**Time:** 3-5 days  
**Recommendation:** Start with Option B (Moderator-only), extend later if needed

---

**End of Report**

