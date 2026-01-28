# How Static Ad Images (ad-1.jpg to ad-5.jpg) Work

**Date:** 2025-01-XX  
**Status:** 📋 Documentation

---

## Overview

The project uses **static image files** (`ad-1.jpg` through `ad-5.jpg`) that are displayed in the **left sidebar** (on desktop) of various pages. These are **hardcoded static images**, not dynamic ads from the database.

---

## 1. Ad Image Files

**Location:** `static/images/`

**Files:**
- `ad-1.jpg`
- `ad-2.jpg`
- `ad-3.jpg`
- `ad-4.jpg`
- `ad-5.jpg`
- `ad-top.jpg` (main banner ad at top of sidebar)

**Note:** These are static image files that you manually upload/replace. They are **not** managed through the Django admin or database.

---

## 2. Where Ads Are Displayed

### 2.1 Homepage (`blog/templates/blog/index.html`)

**Desktop/Tablet (≥768px):**
- **Location:** Left sidebar (`col-lg-3`, `order-lg-2`)
- **Structure:**
  1. **Top Ad:** `ad-top.jpg` (above "مطالب تخصصی" section)
  2. **Popular Posts Section:** "مطالب تخصصی" (Expert Content)
  3. **Bottom Ads:** All 5 ads (`ad-1.jpg` through `ad-5.jpg`) in vertical column
     - Container: `.ads-container-bottom-static`
     - Class: `.ad-placeholder-bottom`
     - Display: `d-none d-md-block` (hidden on mobile, visible on desktop/tablet)

**Mobile (<768px):**
- Ads appear **between posts** in the main content area
- Pattern: After every 4 posts
  - Post 4 → `ad-1.jpg`
  - Post 8 → `ad-2.jpg`
  - Post 12 → `ad-3.jpg`
  - Post 16 → `ad-4.jpg`
  - Post 20 → `ad-5.jpg`
  - Post 24 → `ad-1.jpg` (repeats)
  - And so on...

**Code Location:**
- Desktop sidebar: Lines 434-511
- Mobile inline ads: Lines 282-343

### 2.2 Post Detail Page (`blog/templates/blog/post_detail.html`)

**Desktop/Tablet (≥768px):**
- **Location:** Left sidebar (`col-lg-3`)
- **Structure:**
  1. **Top Ad:** `ad-top.jpg` (above "مطالب تخصصی" section)
  2. **Popular Posts Section:** "مطالب تخصصی" (Expert Content)
  3. **Bottom Ads:** All 5 ads (`ad-1.jpg` through `ad-5.jpg`) in vertical column
     - Container: `.ads-container-bottom`
     - Class: `.ad-placeholder-bottom`

**Mobile:**
- Same sidebar structure (responsive)

**Code Location:** Lines 502-577

### 2.3 Other Pages

**Category Pages, Search Results, etc.:**
- Similar sidebar structure if they include the sidebar
- Uses the same ad pattern

---

## 3. How It Works Technically

### 3.1 Template Structure

**Each Ad Block:**
```html
<div class="ad-placeholder ad-placeholder-bottom">
  <a href="#" target="_blank" rel="noopener noreferrer" class="ad-link">
    <img
      src="{% static 'images/ad-1.jpg' %}"
      alt="تبلیغات"
      class="ad-image"
      loading="lazy"
      onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
    />
    <div class="ad-content" style="display: none">
      <i class="fas fa-ad"></i>
      <p class="ad-text">Your Ads Here!</p>
    </div>
  </a>
</div>
```

**Key Elements:**
- `ad-placeholder`: Container div
- `ad-link`: Clickable link (currently points to `#`)
- `ad-image`: The actual image
- `ad-content`: Fallback content if image fails to load
- `onerror`: JavaScript fallback if image doesn't exist

### 3.2 CSS Styling

**Ad Container (`.ad-placeholder-bottom`):**
- **Aspect Ratio:** `2:1` (width:height = 1:0.5)
- **Min Height:** 120px
- **Width:** 100% of sidebar
- **Display:** Flex column
- **Gap:** 15px between ads
- **Position:** Static (not sticky/fixed)

**Ad Image (`.ad-image`):**
- **Width:** 100%
- **Height:** 100%
- **Object-fit:** Cover (crops to fit)
- **Border-radius:** 8px

**Top Ad (`.ad-placeholder-top`):**
- **Aspect Ratio:** `5:6` (width:height = 1:1.2)
- **Min Height:** 240px
- **Position:** Above popular posts section

**Code Location:** `static/css/style.css`
- Lines 3640-3669: Base ad styles
- Lines 4172-4245: Ad positioning and sizing

### 3.3 Responsive Behavior

**Desktop/Tablet (≥768px):**
- Ads appear in **left sidebar**
- All 5 ads visible in vertical column
- Position: **Static** (scrolls with page)
- Container: `.ads-container-bottom-static`

**Mobile (<768px):**
- Ads appear **inline** between posts
- Pattern: Every 4 posts
- Position: In main content flow

---

## 4. Current Implementation Details

### 4.1 Ad Links

**Current Status:** All ads link to `#` (no-op link)

**To Make Ads Clickable:**
- Replace `href="#"` with actual URL
- Example: `href="https://example.com/ad-campaign"`

### 4.2 Image Loading

**Lazy Loading:** Enabled (`loading="lazy"`)

**Error Handling:**
- If image fails to load, shows fallback content
- Fallback: Icon + "Your Ads Here!" text

### 4.3 Ad Order

**Desktop Sidebar:**
1. `ad-top.jpg` (top)
2. Popular Posts section
3. `ad-1.jpg`
4. `ad-2.jpg`
5. `ad-3.jpg`
6. `ad-4.jpg`
7. `ad-5.jpg`

**Mobile Inline:**
- Rotates through ads: 1 → 2 → 3 → 4 → 5 → 1 (repeat)

---

## 5. How to Update Ads

### 5.1 Replace Image Files

**Steps:**
1. Go to `static/images/` directory
2. Replace the image file (e.g., `ad-1.jpg`)
3. Keep the same filename
4. Commit and push changes
5. Deploy to Heroku

**Image Requirements:**
- Format: JPG, PNG, or WebP
- Recommended aspect ratio: 2:1 (for bottom ads)
- Recommended size: Match sidebar width (typically ~300px wide)

### 5.2 Update Ad Links

**To make ads clickable:**

1. **Edit template file** (e.g., `blog/templates/blog/index.html`)
2. **Find the ad block:**
   ```html
   <a href="#" target="_blank" rel="noopener noreferrer" class="ad-link">
   ```
3. **Replace `#` with actual URL:**
   ```html
   <a href="https://your-ad-url.com" target="_blank" rel="noopener noreferrer" class="ad-link">
   ```

### 5.3 Add/Remove Ads

**To add a 6th ad:**
1. Add image file: `ad-6.jpg`
2. Add new ad block in template (copy existing block, change image path)
3. Update mobile pattern if needed

**To remove an ad:**
1. Remove the ad block from template
2. Optionally delete the image file

---

## 6. Technical Architecture

### 6.1 Static vs Dynamic Ads

**Current System:**
- ✅ **Static Images:** `ad-1.jpg` to `ad-5.jpg` (hardcoded in templates)
- ✅ **Dynamic Ads:** Database-driven ads (from `ads` app) - separate system

**Key Difference:**
- Static ads: Manual file replacement, hardcoded in templates
- Dynamic ads: Managed through Django admin, stored in database

### 6.2 Sidebar Layout

**Bootstrap Grid:**
- Main content: `col-lg-9` (75% width)
- Sidebar: `col-lg-3` (25% width)
- Order: `order-lg-1` (content), `order-lg-2` (sidebar)

**Sidebar Structure:**
```
┌─────────────────────┐
│   ad-top.jpg        │
├─────────────────────┤
│  Popular Posts       │
│  (مطالب تخصصی)      │
├─────────────────────┤
│   ad-1.jpg          │
│   ad-2.jpg          │
│   ad-3.jpg          │
│   ad-4.jpg          │
│   ad-5.jpg          │
└─────────────────────┘
```

### 6.3 CSS Classes

**Container Classes:**
- `.sidebar-wrapper`: Main sidebar container
- `.ads-container-bottom`: Ads container (post detail page)
- `.ads-container-bottom-static`: Ads container (homepage - static positioning)

**Ad Classes:**
- `.ad-placeholder`: Base ad container
- `.ad-placeholder-top`: Top ad (above popular posts)
- `.ad-placeholder-bottom`: Bottom ads (below popular posts)
- `.ad-image`: The image element
- `.ad-link`: Clickable link wrapper

---

## 7. Mobile Behavior

### 7.1 Inline Ads Pattern

**Homepage Mobile:**
- Ads appear **between posts** in main content
- Pattern: After every 4 posts
- Calculation: `forloop.counter|divisibleby:4`
- Ad selection: `((counter // 4) - 1) % 5`

**Example:**
- Posts 1-3: No ad
- Post 4: `ad-1.jpg`
- Posts 5-7: No ad
- Post 8: `ad-2.jpg`
- Posts 9-11: No ad
- Post 12: `ad-3.jpg`
- And so on...

**Code Logic:**
```django
{% if forloop.counter|divisibleby:4 %}
  <!-- Show ad based on counter -->
  {% if forloop.counter == 4 or forloop.counter == 24 ... %}
    <!-- ad-1 -->
  {% elif forloop.counter == 8 or forloop.counter == 28 ... %}
    <!-- ad-2 -->
  <!-- etc. -->
{% endif %}
```

### 7.2 Mobile Sidebar

**Post Detail Page:**
- Sidebar still visible on mobile
- Ads appear in sidebar (not inline)
- Same structure as desktop

---

## 8. Performance Considerations

### 8.1 Image Loading

**Lazy Loading:**
- ✅ Enabled for all ad images
- Images load only when visible in viewport
- Reduces initial page load time

**Error Handling:**
- Fallback content if image fails
- Prevents broken image icons

### 8.2 Caching

**Static Files:**
- Served by Django static files (or CDN in production)
- Browser caching applies
- Images cached after first load

### 8.3 File Size

**Recommendations:**
- Optimize images before uploading
- Use appropriate compression
- Target file size: < 200KB per image
- Format: JPG for photos, PNG for graphics

---

## 9. Summary

### How It Works:

1. **Static Image Files:** `ad-1.jpg` to `ad-5.jpg` stored in `static/images/`
2. **Template Inclusion:** Hardcoded in templates (`index.html`, `post_detail.html`)
3. **Display Location:** Left sidebar on desktop, inline on mobile (homepage)
4. **Styling:** CSS controls size, aspect ratio, and positioning
5. **Responsive:** Different behavior on mobile vs desktop

### Key Points:

- ✅ **Static System:** Images are files, not database records
- ✅ **Manual Updates:** Replace image files to update ads
- ✅ **Hardcoded:** Ad blocks are in templates (not dynamic)
- ✅ **Separate from Dynamic Ads:** This is different from the `ads` app system
- ✅ **Responsive:** Works on all screen sizes

### To Update Ads:

1. Replace image files in `static/images/`
2. (Optional) Update links in templates
3. Commit and push changes
4. Deploy to production

---

**Document Prepared By:** AI Assistant  
**Date:** 2025-01-XX  
**Status:** Complete Documentation

