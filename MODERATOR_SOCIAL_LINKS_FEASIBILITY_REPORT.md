# Moderator Social/Contact Links - Feasibility Report

**Date:** 2025-01-XX  
**Status:** READ-ONLY Analysis (No Changes Applied)  
**Goal:** Assess adding website/instagram/linkedin fields to Moderator model

---

## 1. Model Analysis

### Model Name & Location
- **Model:** `Moderator`
- **File:** `askme/models.py` (lines 13-116)
- **App:** `askme`

### Current Fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `user` | OneToOneField(User) | Yes | User account |
| `expert_title` | CharField(100) | Yes | Expert title |
| `complete_name` | CharField(200) | No | Display name |
| `profile_image` | CloudinaryField | No | Profile photo |
| `bio` | TextField | No | Biography |
| `field_specialty` | CharField(200) | No | Specialty domain |
| `disclaimer` | TextField | No | Custom disclaimer |
| `slug` | SlugField(200) | No | URL-friendly ID |
| `is_active` | BooleanField | Yes | Active status |
| `created_on` | DateTimeField | Auto | Creation timestamp |
| `updated_on` | DateTimeField | Auto | Update timestamp |

### Missing Fields
❌ **NO contact/social link fields exist:**
- No `website` field
- No `instagram` field
- No `linkedin` field
- No other social media fields

---

## 2. Admin Configuration Analysis

### File: `askme/admin.py`

**ModeratorAdmin Class (lines 12-58):**
- **Uses fieldsets:** Yes (3 fieldsets)
- **Excludes fields:** No (no `exclude` attribute)
- **List display:** Shows user, expert_title, field_specialty, slug, is_active, stats
- **Search fields:** user, expert_title, complete_name, bio, field_specialty, slug

**Fieldsets Structure:**
1. **"Moderator Information"** (line 33):
   - Fields: `user`, `expert_title`, `complete_name`, `field_specialty`, `profile_image`, `bio`, `is_active`

2. **"Expert Profile"** (line 36):
   - Fields: `slug`, `disclaimer`

3. **"Timestamps"** (line 40):
   - Fields: `created_on`, `updated_on` (readonly, collapsed)

**Impact of Adding Fields:**
- ✅ New fields will automatically appear in admin (no `exclude` blocking them)
- ✅ Can add to existing fieldset or create new "Contact/Social Links" fieldset
- ✅ No changes needed to list_display or search_fields (optional enhancement)

---

## 3. Expert Profile Template Analysis

### File: `askme/templates/askme/expert_profile.html`

**Current Structure:**
- **Hero Section:** Name and title
- **Profile Card (Left):** Image, name, title, specialty, stats, ask question button
- **Details Section (Right):**
  - About section (bio)
  - Disclaimer section (if exists)
  - Additional Info section (name, title, specialty, join date, status)

**Missing Elements:**
- ❌ No social/contact links section
- ❌ No website link
- ❌ No social media icons/links

**Best Placement for New Links:**
- **Option A:** Add to "Additional Info" card (lines 148-176) - Simple, consistent
- **Option B:** Create new "Contact & Social Links" card - More prominent, dedicated section
- **Recommendation:** Option B (dedicated section) for better visibility

---

## 4. View Analysis

### File: `askme/views.py`

**expert_profile View (lines 48-73):**
- Simple view: fetches moderator, calculates stats, renders template
- **No special handling needed** for new fields
- New fields will be automatically available in template context via `moderator` object

**No Changes Required:** View will work with new fields automatically.

---

## 5. Risk Assessment

### Risk Level: 🟢 **LOW**

**Rationale:**
1. ✅ **Isolated Changes:** Only affects Moderator model and expert_profile template
2. ✅ **No Breaking Changes:** New optional fields (blank=True) won't break existing data
3. ✅ **Admin Compatible:** Fieldsets allow easy addition without breaking admin
4. ✅ **Template Safe:** Adding new section doesn't affect existing sections
5. ✅ **No Dependencies:** No other models or views depend on Moderator fields
6. ✅ **Backward Compatible:** Existing moderators will work fine (fields optional)

### Potential Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Migration conflicts** | 🟢 LOW | New fields only, no existing data to migrate |
| **Admin display issues** | 🟢 LOW | Add to fieldset, test in development first |
| **Template layout breaks** | 🟢 LOW | Add new section, doesn't modify existing sections |
| **URL validation** | 🟡 MEDIUM | Use URLField with validation, add help_text for format |
| **External link security** | 🟡 MEDIUM | Use `target="_blank" rel="noopener noreferrer"` |
| **Empty fields display** | 🟢 LOW | Use `{% if %}` conditionals in template |

**Security Considerations:**
- ✅ Use `URLField` (validates URL format)
- ✅ Use `target="_blank" rel="noopener noreferrer"` for external links
- ✅ Optional fields (blank=True) - no required data entry
- ✅ Admin-only editing (no user input)

---

## 6. Exact Change Plan

### Files to Modify

#### 1. `askme/models.py`
**Location:** After `disclaimer` field (around line 50)

**Add:**
```python
website = models.URLField(
    blank=True,
    null=True,
    help_text="Personal or professional website URL",
    verbose_name="وب‌سایت"
)
instagram = models.URLField(
    blank=True,
    null=True,
    help_text="Instagram profile URL",
    verbose_name="اینستاگرام"
)
linkedin = models.URLField(
    blank=True,
    null=True,
    help_text="LinkedIn profile URL",
    verbose_name="لینکدین"
)
```

**Placement:** Add after `disclaimer` field, before `slug` field (logical grouping)

---

#### 2. `askme/admin.py`
**Location:** In `ModeratorAdmin.fieldsets` (around line 35)

**Modify:**
Add new fieldset or add to existing "Expert Profile" fieldset:

**Option A - New Fieldset (Recommended):**
```python
fieldsets = (
    ('Moderator Information', {
        'fields': ('user', 'expert_title', 'complete_name', 'field_specialty', 'profile_image', 'bio', 'is_active')
    }),
    ('Expert Profile', {
        'fields': ('slug', 'disclaimer'),
        'description': 'Profile page settings. Slug is auto-generated if left blank. Disclaimer is shown on the expert profile page.'
    }),
    ('Contact & Social Links', {
        'fields': ('website', 'instagram', 'linkedin'),
        'description': 'Optional contact and social media links (displayed on expert profile page)'
    }),
    ('Timestamps', {
        'fields': ('created_on', 'updated_on'),
        'classes': ('collapse',)
    }),
)
```

**Option B - Add to Existing Fieldset:**
Add to "Expert Profile" fieldset:
```python
('Expert Profile', {
    'fields': ('slug', 'disclaimer', 'website', 'instagram', 'linkedin'),
    ...
})
```

**Recommendation:** Option A (dedicated fieldset) for better organization

---

#### 3. `askme/templates/askme/expert_profile.html`
**Location:** After "Additional Info" card (around line 177, before closing `</div>`)

**Add New Section:**
```django
<!-- Contact & Social Links -->
{% if moderator.website or moderator.instagram or moderator.linkedin %}
<div class="card shadow-sm mt-4">
  <div class="card-header bg-light">
    <h4 class="mb-0">
      <i class="fas fa-link ms-2"></i>لینک‌های ارتباطی
    </h4>
  </div>
  <div class="card-body">
    <div class="expert-social-links">
      {% if moderator.website %}
      <a 
        href="{{ moderator.website }}" 
        target="_blank" 
        rel="noopener noreferrer"
        class="btn btn-outline-primary mb-2 w-100"
      >
        <i class="fas fa-globe ms-2"></i>وب‌سایت
      </a>
      {% endif %}
      {% if moderator.instagram %}
      <a 
        href="{{ moderator.instagram }}" 
        target="_blank" 
        rel="noopener noreferrer"
        class="btn btn-outline-danger mb-2 w-100"
      >
        <i class="fab fa-instagram ms-2"></i>اینستاگرام
      </a>
      {% endif %}
      {% if moderator.linkedin %}
      <a 
        href="{{ moderator.linkedin }}" 
        target="_blank" 
        rel="noopener noreferrer"
        class="btn btn-outline-primary mb-2 w-100"
      >
        <i class="fab fa-linkedin ms-2"></i>لینکدین
      </a>
      {% endif %}
    </div>
  </div>
</div>
{% endif %}
```

**Placement:** After line 176 (after "Additional Info" card closes), before line 177 (`</div>` closing the col-lg-8)

---

#### 4. Migration File
**File to Create:** `askme/migrations/XXXX_add_social_links_to_moderator.py`

**Migration Content:**
```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('askme', '0004_...'),  # Replace with latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='moderator',
            name='website',
            field=models.URLField(blank=True, null=True, verbose_name='وب‌سایت'),
        ),
        migrations.AddField(
            model_name='moderator',
            name='instagram',
            field=models.URLField(blank=True, null=True, verbose_name='اینستاگرام'),
        ),
        migrations.AddField(
            model_name='moderator',
            name='linkedin',
            field=models.URLField(blank=True, null=True, verbose_name='لینکدین'),
        ),
    ]
```

**Command:**
```bash
python manage.py makemigrations askme
python manage.py migrate askme
```

---

## 7. Files Summary

### Files to Modify (3 files)
1. ✅ `askme/models.py` - Add 3 URLField fields
2. ✅ `askme/admin.py` - Add new fieldset or extend existing
3. ✅ `askme/templates/askme/expert_profile.html` - Add social links section

### Files to Create (1 file)
1. ✅ `askme/migrations/XXXX_add_social_links_to_moderator.py` - Migration (auto-generated)

### Files NOT Modified
- ❌ No changes to views (automatic template context)
- ❌ No changes to URLs
- ❌ No changes to other templates
- ❌ No changes to other models
- ❌ No changes to settings

---

## 8. Implementation Checklist

- [ ] Add fields to `Moderator` model (website, instagram, linkedin)
- [ ] Update `ModeratorAdmin` fieldsets
- [ ] Create migration: `makemigrations askme`
- [ ] Apply migration: `migrate askme`
- [ ] Add social links section to `expert_profile.html`
- [ ] Test admin: Add links to existing moderator
- [ ] Test template: Verify links display correctly
- [ ] Test external links: Verify `target="_blank" rel="noopener noreferrer"` works
- [ ] Test empty fields: Verify section doesn't show if all fields empty
- [ ] Verify RTL layout: Check Persian text alignment

---

## 9. GO / NO-GO Decision

### ✅ **GO - Safe to Implement**

**Confidence Level:** 🟢 **HIGH** (95%)

**Rationale:**
1. ✅ Fields don't exist - safe to add
2. ✅ Optional fields (blank=True, null=True) - no breaking changes
3. ✅ Admin fieldsets allow easy addition
4. ✅ Template changes are additive (new section, doesn't modify existing)
5. ✅ View requires no changes
6. ✅ Low risk of conflicts or breaking changes
7. ✅ Follows existing patterns (URLField like other models)

**Estimated Implementation Time:** 30-45 minutes

**Risk Level:** 🟢 **LOW** - Isolated changes, optional fields, additive template updates

---

## 10. Additional Recommendations

### Optional Enhancements (Out of Scope)
- Add more social platforms (Twitter/X, Facebook, YouTube)
- Add email contact field (with privacy consideration)
- Add phone number field (with privacy consideration)
- Add social link icons with hover effects
- Add link validation/formatting helpers

### Testing Checklist
- [ ] Add website link to moderator in admin
- [ ] Add instagram link to moderator in admin
- [ ] Add linkedin link to moderator in admin
- [ ] Verify links appear on expert profile page
- [ ] Verify links open in new tab
- [ ] Verify section doesn't show if all fields empty
- [ ] Verify section shows if at least one field has value
- [ ] Test with Persian text in URLs
- [ ] Verify RTL layout
- [ ] Test responsive design (mobile, tablet, desktop)

---

## End of Report

**Report Status:** ✅ Complete  
**Next Step:** Implementation (when approved)  
**Report Generated:** READ-ONLY Analysis (No Changes Applied)

