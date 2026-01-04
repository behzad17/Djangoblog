# Related Links Feature - Implementation Summary

**Status:** ✅ Implementation Complete  
**Date:** 2025-01-XX

---

## Files Created

### Django App Structure
```
related_links/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── views.py
├── urls.py
├── migrations/
│   └── __init__.py
└── templates/
    └── related_links/
        └── links_list.html
```

### Static Files
```
static/css/related_links.css
```

---

## Files Modified

1. **`codestar/settings.py`**
   - Added `'related_links'` to `INSTALLED_APPS` (line ~89)

2. **`codestar/urls.py`**
   - Added `path("related-links/", include("related_links.urls", namespace="related_links"))` (line ~87)

3. **`templates/base.html`**
   - Added `{% url 'related_links:links_list' as related_links_url %}` at top (line ~8)
   - Added `{% block extra_css %}{% endblock extra_css %}` in `<head>` (line ~85)
   - Added navigation link "لینک‌های مرتبط" in navbar (line ~176-181)

---

## Final URL and Route Name

- **URL Path:** `/related-links/`
- **Route Name:** `related_links:links_list`
- **Full URL Pattern:** `/related-links/` → `related_links.views.links_list`
- **Filter URL:** `/related-links/?type=podcast` (or video, radio, website, file, social)

---

## Model Structure

**RelatedLink Model:**
- `title` (CharField, max_length=200)
- `slug` (SlugField, auto-generated, unique)
- `link_type` (CharField with choices: PODCAST, VIDEO, RADIO, WEBSITE, FILE, SOCIAL)
- `description` (TextField, optional)
- `source_name` (CharField, optional)
- `url` (URLField)
- `cover_image` (CloudinaryField, optional - follows Ads/Experts pattern)
- `is_active` (BooleanField, default=True)
- `order` (PositiveIntegerField, default=0)
- `created_on` / `updated_on` (DateTimeField, auto)

**LinkType Choices:**
- 🎧 پادکست (podcast)
- 🎬 فیلم / ویدئو (video)
- 📻 رادیو (radio)
- 🌐 وب‌سایت (website)
- 📂 فایل آموزشی (file)
- 📱 شبکه‌های اجتماعی (social)

---

## Admin Instructions

### Accessing Admin
1. Log in to Django admin: `/admin/`
2. Navigate to "لینک‌های مرتبط" section
3. Click "لینک‌های مرتبط" to view/add links

### Adding a New Link
1. Click "Add لینک مرتبط"
2. Fill in required fields:
   - **عنوان (Title):** Link title (slug auto-generates)
   - **نوع لینک (Link Type):** Select from dropdown
   - **لینک (URL):** External URL (required)
3. Optional fields:
   - **توضیحات (Description):** Short description (2-3 lines)
   - **نام منبع (Source Name):** Name of the source/organization
   - **تصویر کاور (Cover Image):** Upload optional cover image
4. Display settings:
   - **فعال (Is Active):** Check to show on site
   - **ترتیب نمایش (Order):** Number for sorting (lower = first)
5. Click "Save"

### Managing Links
- **List View:** Shows title, type, active status, order, created date
- **Filtering:** Filter by link type or active status
- **Search:** Search by title, source name, description, or URL
- **Bulk Edit:** Can edit `is_active` and `order` directly in list view
- **Ordering:** Links sorted by `order` field, then by creation date (newest first)

---

## Explicit Confirmations

### ✅ No Media Embedded
- **Confirmed:** Template uses only external links with `target="_blank" rel="noopener noreferrer"`
- **No iframe, audio, or video tags** in template
- **No embedded players** - all content opens in new tab

### ✅ No Existing Pages Changed
- **Only changes:**
  1. Added ONE navigation link in `base.html` navbar
  2. Added harmless `{% block extra_css %}` block in `base.html` `<head>` (does not affect other pages)
- **No changes to:**
  - Existing models (blog, ads, askme, about)
  - Existing URLs or views
  - Existing templates (except base.html navigation)
  - Global CSS (dedicated `related_links.css` file, loaded only on this page)

### ✅ Safety Measures
- **Isolated app:** New Django app with no dependencies on other apps
- **Scoped CSS:** All styles scoped under `.related-links-page` wrapper
- **No global changes:** CSS file loaded only on related links page via `{% block extra_css %}`
- **Independent migrations:** Only creates `related_links_relatedlink` table
- **Server-side filtering:** Uses querystring (`?type=...`), no JavaScript

---

## Next Steps (After Implementation)

1. **Create Migration:**
   ```bash
   python manage.py makemigrations related_links
   python manage.py migrate
   ```

2. **Test Admin Interface:**
   - Create test links for each type
   - Verify image upload works
   - Test filtering and ordering

3. **Test Frontend:**
   - Visit `/related-links/`
   - Test filter tabs
   - Verify cards display correctly
   - Test external links open in new tab
   - Test responsive design (mobile, tablet, desktop)
   - Verify RTL layout

4. **Smoke Tests (Verify No Breaking Changes):**
   - ✅ Homepage loads
   - ✅ Ads page works
   - ✅ Ask Me page works
   - ✅ Expert profile works
   - ✅ Create Post works
   - ✅ Login works
   - ✅ All existing navigation links work

---

## CSS File Details

**File:** `static/css/related_links.css`

**Features:**
- Scoped under `.related-links-page` wrapper
- Uses design tokens from `tokens.css` (CSS variables)
- Responsive design (mobile, tablet, desktop)
- Hover effects with `prefers-reduced-motion` support
- RTL compatible
- Filter tabs with active state
- Card grid layout (3 columns desktop, 2 tablet, 1 mobile)

**No Global Impact:** File loaded only on related links page via `{% block extra_css %}`

---

## Template Structure

**File:** `related_links/templates/related_links/links_list.html`

**Blocks Used:**
- `{% block title %}` - Page title
- `{% block meta_description %}` - SEO description
- `{% block extra_css %}` - Loads dedicated CSS file
- `{% block content %}` - Main page content

**Features:**
- Hero section (consistent with other pages)
- Filter tabs (all types + "همه")
- Card grid with Bootstrap responsive columns
- External links with `target="_blank" rel="noopener noreferrer"`
- Optional cover images
- Type badges
- CTA buttons with dynamic labels based on type

---

## Button Labels by Type

- **Podcast/Radio:** "گوش دادن"
- **Video:** "تماشا"
- **Website/File/Social:** "مشاهده"

Implemented via `get_button_label()` method in model.

---

## Implementation Complete ✅

All files created and configured. Ready for migration and testing.

