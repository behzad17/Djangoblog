# Technical Plan: Center-Mode Category Slider for Ads Page

**Date:** 2025-01-XX  
**Status:** 📋 **READ-ONLY PLAN** (Implementation to follow)  
**Scope:** Replace/enhance current Ads category UI with center-mode slider

---

## 1) Current Implementation Analysis

### 1.1 Files Involved

**Templates:**
- `ads/templates/ads/ads_home.html` (lines 31-74)
  - Current category section: `.ads-categories` → `.ads-categories-track` → `.ads-category-item`
  - Uses Django template loop: `{% for category in categories %}`
  - Links: `{% url 'ads:ads_by_category' category.slug %}`
  - Active state: `{% if active_category_slug == category.slug %}is-active{% endif %}`

**CSS:**
- `static/css/style.css` (lines 3690-3900)
  - Current styles: `.ads-categories`, `.ads-categories-track`, `.ads-category-item`, `.ads-category-circle`
  - Responsive: Horizontal scroll (mobile), Grid 4 cols (tablet), Grid 6 cols (desktop)
  - Uses CSS custom properties: `--accent`, `--pv-*` tokens
  - RTL-aware: Uses `left`/`right` appropriately

**Views:**
- `ads/views.py` - `ad_category_list()` function
  - Provides: `categories` (queryset), `ad_counts` (dict), `active_category_slug` (str)
  - No changes needed to view

**Template Tags:**
- `ads/templatetags/ads_extras.py`
  - `get_item` filter: Used for `{{ ad_counts|get_item:category.id }}`
  - Icon mapping exists but not used in current template

**Base Template:**
- `templates/base.html`
  - Has `{% block extra_css %}` (line 87) for page-specific CSS
  - Has `{% block extras %}` (likely exists) for page-specific JS

### 1.2 Current Category Data Structure

**Model:** `ads.models.AdCategory`
- Fields: `name` (CharField), `slug` (SlugField), `description` (TextField)
- Method: `ad_count()` returns count of approved/active ads

**View Context:**
- `categories`: Queryset of all `AdCategory` objects (ordered by name)
- `ad_counts`: Dictionary `{category_id: count}` for efficient count display
- `active_category_slug`: String from query params (optional)

**Icon Logic:**
- Currently uses inline template conditionals based on slug/name
- Maps to FontAwesome icons: `fa-calendar-alt`, `fa-gavel`, `fa-heart`, `fa-utensils`, `fa-home`, `fa-couch`, `fa-car`, `fa-briefcase`, `fa-tag`

**Color Logic:**
- Uses inline `style="--accent: #HEX;"` based on category slug/name
- Color mapping: leisure (#5E9CA0), legal/finance (#7B6DAA), health (#7AAE7A), food (#C28C5C), housing (#6C8FBF), home-items (#9A8F7A), vehicles (#7A7F8C), default (#7C9AA6)

---

## 2) New Component Architecture

### 2.1 File Structure

**New Files to Create:**
1. **Template Partial:** `ads/templates/ads/includes/_category_slider.html`
   - Reusable partial for category slider
   - Can be included in `ads_home.html` and potentially `ads_by_category.html`

2. **CSS File:** `static/css/ads-category-slider.css`
   - All slider-specific styles
   - Scoped under `.ads-category-slider` wrapper class
   - No global selectors (`body`, `*`, `:root`)

3. **JavaScript File:** `static/js/ads-category-slider.js`
   - Slider initialization and interaction logic
   - Uses data attributes for element selection
   - Scoped to component root (no global `getElementById`)

**Files to Modify:**
1. **Template:** `ads/templates/ads/ads_home.html`
   - Replace lines 31-74 (current category section) with `{% include 'ads/includes/_category_slider.html' %}`
   - Add `{% block extra_css %}` to load new CSS
   - Add `{% block extras %}` to load new JS

### 2.2 Component Wrapper & Scoping Strategy

**Wrapper Class:** `.ads-category-slider`
- All CSS selectors will be prefixed: `.ads-category-slider .slider-track`, `.ads-category-slider .slider-card`, etc.
- JavaScript will query within wrapper: `slider.querySelector('[data-ads-track]')`
- Prevents conflicts with existing `.ads-categories` styles

**Data Attributes (No Fixed IDs):**
- `[data-ads-slider]` - Root wrapper
- `[data-ads-track]` - Scrollable track container
- `[data-ads-prev]` - Previous button
- `[data-ads-next]` - Next button
- `[data-ads-dot]` - Dot indicators (if used)
- `[data-ads-card]` - Individual category cards
- `[data-ads-card-index]` - Card index for JS reference

**Benefits:**
- ✅ Supports multiple instances (if needed in future)
- ✅ No ID collisions with existing code
- ✅ Clear semantic naming
- ✅ Easy to debug

---

## 3) Integration Plan

### 3.1 Template Integration

**Option A: Replace Current Section (Recommended)**
```django
<!-- In ads/templates/ads/ads_home.html -->
<div class="container py-4">
  {% include 'ads/includes/_category_slider.html' with categories=categories ad_counts=ad_counts active_category_slug=active_category_slug %}
</div>
```

**Option B: Add as Alternative (Toggle)**
- Keep current implementation
- Add toggle/option to switch between views
- **Not recommended** - adds complexity

**Template Partial Structure:**
```django
{% load static %}
{% load ads_extras %}

<div class="ads-category-slider" data-ads-slider role="region" aria-label="Ads category navigation slider">
  <!-- Navigation buttons -->
  <!-- Track container with cards -->
  <!-- Fallback for no-JS -->
</div>
```

### 3.2 CSS Integration

**Loading:**
```django
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/ads-category-slider.css' %}?v={% now 'U' %}">
{% endblock extra_css %}
```

**Scoping Rules:**
- ✅ All selectors start with `.ads-category-slider`
- ✅ No `body`, `*`, `:root` selectors
- ✅ Use CSS custom properties for theming (map to existing `--pv-*` tokens)
- ✅ Responsive breakpoints: Mobile (<768px), Tablet (768-991px), Desktop (≥992px)

**Example:**
```css
/* ✅ GOOD - Scoped */
.ads-category-slider {
  /* Component root styles */
}

.ads-category-slider .slider-track {
  /* Track styles */
}

/* ❌ BAD - Global */
body {
  /* Never do this */
}
```

### 3.3 JavaScript Integration

**Loading:**
```django
{% block extras %}
<script src="{% static 'js/ads-category-slider.js' %}" defer></script>
{% endblock extras %}
```

**Initialization Pattern:**
```javascript
(function() {
  'use strict';
  
  function initAdsCategorySlider() {
    const sliders = document.querySelectorAll('[data-ads-slider]');
    sliders.forEach(slider => {
      // Initialize each slider instance
      // Use data attributes for element selection
    });
  }
  
  document.addEventListener('DOMContentLoaded', initAdsCategorySlider);
})();
```

**No Global Pollution:**
- ✅ IIFE wrapper
- ✅ Strict mode
- ✅ Query within component root
- ✅ No global variables/functions

---

## 4) Accessibility Plan

### 4.1 ARIA Attributes

**Root Container:**
```html
<div class="ads-category-slider" 
     data-ads-slider
     role="region"
     aria-label="Ads category navigation slider"
     aria-live="polite">
```

**Navigation Buttons:**
```html
<button type="button"
        data-ads-prev
        aria-label="Previous category"
        aria-controls="ads-slider-track">
  ‹
</button>
```

**Category Cards:**
```html
<a href="{% url 'ads:ads_by_category' category.slug %}"
   data-ads-card
   data-ads-card-index="{{ forloop.counter0 }}"
   aria-label="Browse {{ category.name }} category ({{ ad_counts|get_item:category.id|default:0 }} ads)"
   {% if active_category_slug == category.slug %}aria-current="page"{% endif %}>
  <!-- Card content -->
</a>
```

**Track Container:**
```html
<div data-ads-track
     id="ads-slider-track"
     role="list"
     aria-label="Category list">
  <!-- Cards as listitems -->
</div>
```

### 4.2 Keyboard Navigation

**Required Support:**
- ✅ **Tab:** Focus on cards and buttons
- ✅ **Enter/Space:** Activate focused card/button
- ✅ **Arrow Left/Right:** Navigate slider (optional, for carousel navigation)
- ✅ **Home/End:** Jump to first/last card (optional)
- ✅ **Escape:** Return focus to slider container (optional)

**Implementation:**
```javascript
// Cards are <a> tags - native keyboard support works
// Add arrow key navigation for slider control
slider.addEventListener('keydown', (e) => {
  if (e.target.closest('[data-ads-card]')) {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      // Navigate slider
    }
  }
});
```

### 4.3 Focus Management

**Requirements:**
- ✅ Visible focus indicators (Bootstrap default + custom if needed)
- ✅ Focus doesn't jump unexpectedly during animation
- ✅ Focus returns to active card after navigation
- ✅ Focus trap within slider (optional, for modal-like behavior)

**Focus Styles:**
```css
.ads-category-slider [data-ads-card]:focus-visible {
  outline: 3px solid var(--pv-cta-ask, #3498DB);
  outline-offset: 4px;
  border-radius: 8px;
}
```

### 4.4 Screen Reader Support

**Announcements:**
- Use `aria-live="polite"` on root container
- Update live region when active card changes: "Category 3 of 10: [Category Name]"

**Descriptive Text:**
- Each card has `aria-label` with category name and ad count
- Active card has `aria-current="page"`

### 4.5 Reduced Motion

**Respect User Preference:**
```css
@media (prefers-reduced-motion: reduce) {
  .ads-category-slider * {
    animation: none !important;
    transition: none !important;
  }
}
```

---

## 5) Performance Plan

### 5.1 Image Strategy

**No External Images:**
- ✅ Use FontAwesome icons (already loaded via CDN)
- ✅ Use CSS gradients/colors for backgrounds
- ✅ No image files needed for categories

**If Future Images Needed:**
- Self-host in `static/images/ads-categories/`
- Use `loading="lazy"` attribute
- Optimize (WebP, compression)
- Use `srcset` for responsive images

### 5.2 JavaScript Performance

**Optimizations:**
- ✅ Defer script loading: `<script defer>`
- ✅ Use `requestAnimationFrame` for smooth animations
- ✅ Debounce scroll/resize events
- ✅ Cache DOM queries
- ✅ Use event delegation where possible

**Example:**
```javascript
let rafId;
function smoothScrollTo(target) {
  cancelAnimationFrame(rafId);
  rafId = requestAnimationFrame(() => {
    track.scrollTo({ left: target, behavior: 'smooth' });
  });
}
```

### 5.3 CSS Performance

**Optimizations:**
- ✅ Use `transform` and `opacity` for animations (GPU-accelerated)
- ✅ Avoid animating `width`, `height`, `top`, `left`
- ✅ Use `will-change` sparingly (only on animated elements)
- ✅ Minimize repaints/reflows

**Example:**
```css
/* ✅ GOOD - GPU-accelerated */
.ads-category-slider .slider-card {
  transform: translateX(0);
  transition: transform 0.3s ease;
}

/* ❌ BAD - Causes reflow */
.ads-category-slider .slider-card {
  left: 0;
  transition: left 0.3s ease;
}
```

### 5.4 Initial Load

**Strategies:**
- ✅ CSS loaded in `<head>` (blocking, but small file)
- ✅ JS loaded with `defer` (non-blocking)
- ✅ No blocking external resources
- ✅ Fallback layout works without JS

---

## 6) RTL Support Plan

### 6.1 Layout Adjustments

**CSS Logical Properties:**
- Use `margin-inline-start` instead of `margin-left`
- Use `padding-inline-end` instead of `padding-right`
- Use `text-align: start` instead of `text-align: left`

**Transform Directions:**
- Flip `translateX` for RTL: `transform: translateX(calc(var(--offset) * -1))` in RTL
- Or use CSS logical: `transform: translate(calc(var(--offset) * -1), 0)` with `direction: rtl`

**Scroll Direction:**
- RTL browsers automatically reverse scroll direction
- Test `scrollLeft` behavior (may be negative in RTL)

### 6.2 JavaScript RTL Detection

**Detection:**
```javascript
const isRTL = document.documentElement.dir === 'rtl' || 
              document.documentElement.getAttribute('dir') === 'rtl';
```

**Navigation Logic:**
```javascript
function next() {
  if (isRTL) {
    // In RTL, "next" means scroll left (negative)
    scrollTo(currentIndex - 1);
  } else {
    // In LTR, "next" means scroll right (positive)
    scrollTo(currentIndex + 1);
  }
}
```

### 6.3 Testing RTL

**Test Cases:**
- ✅ Cards scroll in correct direction
- ✅ Center card calculation works
- ✅ Prev/Next buttons work correctly
- ✅ Text alignment is correct
- ✅ Icons align properly
- ✅ Focus indicators appear on correct side

---

## 7) Center-Mode Behavior Specification

### 7.1 Desktop/Tablet (≥768px)

**Layout:**
- Horizontal row of cards
- Center card is expanded (shows more details: description, larger icon, ad count)
- Side cards are collapsed (icon + name only)
- Smooth scroll to center active card on load/interaction

**Expanded Card (Center):**
- Larger size (e.g., 200px width vs 120px for collapsed)
- Shows: Icon (larger), Name (bold), Description (if available), Ad count badge
- Elevated shadow, accent border
- Smooth transition when card becomes center

**Collapsed Cards (Sides):**
- Smaller size (e.g., 120px width)
- Shows: Icon (smaller), Name only
- Reduced opacity (e.g., 0.7)
- Smooth transition when card moves to side

**Navigation:**
- Click card → Navigate to category page (if not already active)
- Click prev/next → Scroll to center next/previous card
- Arrow keys → Navigate slider (optional)
- Auto-center on scroll (snap to center)

### 7.2 Mobile (<768px)

**Layout Options:**

**Option A: Stacked/Vertical (Recommended)**
- Cards stack vertically
- Each card shows full details (no collapsed state)
- Scrollable list
- Simpler, faster, more touch-friendly

**Option B: Horizontal Scroll (Simplified)**
- Keep horizontal layout
- All cards same size (no center expansion)
- Simple horizontal scroll
- Touch swipe support

**Recommendation:** **Option A (Stacked)** - Better UX on mobile, simpler implementation

### 7.3 Active Category Detection

**On Page Load:**
- If `active_category_slug` is provided, center that category
- Otherwise, center first category

**After Navigation:**
- When user clicks a category and returns, that category should be centered
- Use URL hash or query param to detect active category

---

## 8) Graceful Fallback (No-JS)

### 8.1 Fallback Layout

**Strategy:**
- Use `<noscript>` tag to show alternative layout
- Or: Make default CSS work without JS (progressive enhancement)

**Recommended: Progressive Enhancement**
- Default CSS: Responsive grid (like current implementation)
- JS enhances: Adds slider behavior, center-mode, smooth scrolling
- If JS fails: Grid still works, all categories visible

**Implementation:**
```html
<div class="ads-category-slider" data-ads-slider>
  <!-- Default: Grid layout (works without JS) -->
  <div data-ads-track class="slider-track slider-track-fallback">
    {% for category in categories %}
      <a href="..." class="slider-card">
        <!-- Card content -->
      </a>
    {% endfor %}
  </div>
</div>
```

**CSS Fallback:**
```css
/* Default: Grid layout */
.ads-category-slider .slider-track-fallback {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1.5rem;
}

/* JS enhances to slider */
.ads-category-slider.js-enabled .slider-track-fallback {
  display: flex;
  overflow-x: auto;
  /* Slider styles */
}
```

---

## 9) Risk Assessment

### 9.1 CSS Conflicts

**Risk Level:** 🟢 **LOW**

**Mitigation:**
- ✅ All CSS scoped under `.ads-category-slider`
- ✅ No global selectors
- ✅ Unique class names (`.slider-track`, `.slider-card` vs existing `.ads-categories-track`)
- ✅ Existing `.ads-categories` styles remain untouched (can coexist)

### 9.2 JavaScript Conflicts

**Risk Level:** 🟢 **LOW**

**Mitigation:**
- ✅ Uses data attributes (no ID collisions)
- ✅ Scoped to component root
- ✅ IIFE wrapper (no global pollution)
- ✅ No conflicts with existing carousel (`#categoryCarousel` is different)

### 9.3 Accessibility Risks

**Risk Level:** 🟡 **MEDIUM**

**Mitigation:**
- ✅ ARIA attributes planned
- ✅ Keyboard navigation implemented
- ✅ Focus management considered
- ✅ Screen reader support included
- ⚠️ Requires testing with actual screen readers

### 9.4 Performance Risks

**Risk Level:** 🟢 **LOW**

**Mitigation:**
- ✅ No external images
- ✅ Deferred JS loading
- ✅ GPU-accelerated animations
- ✅ Fallback works without JS
- ⚠️ Smooth scrolling may cause jank on low-end devices (use `prefers-reduced-motion`)

### 9.5 RTL Compatibility

**Risk Level:** 🟡 **MEDIUM**

**Mitigation:**
- ✅ RTL detection in JS
- ✅ CSS logical properties
- ✅ Transform direction flipping
- ⚠️ Requires thorough RTL testing

### 9.6 Maintainability

**Risk Level:** 🟢 **LOW**

**Mitigation:**
- ✅ Clear file structure
- ✅ Well-documented code
- ✅ Reusable template partial
- ✅ Scoped styles (easy to modify)
- ✅ Data attributes (easy to debug)

---

## 10) Testing Checklist

### 10.1 Desktop Center Behavior
- [ ] Center card expands correctly
- [ ] Side cards collapse correctly
- [ ] Smooth scroll to center works
- [ ] Prev/Next buttons work
- [ ] Click on card navigates to category page
- [ ] Active category is centered on load
- [ ] All 10 categories display correctly

### 10.2 Mobile Behavior
- [ ] Cards stack vertically (or horizontal scroll works)
- [ ] Touch swipe works (if horizontal)
- [ ] All categories visible/accessible
- [ ] No horizontal overflow
- [ ] Touch targets are adequate (≥44px)

### 10.3 RTL Behavior
- [ ] Cards scroll in correct direction
- [ ] Center calculation works in RTL
- [ ] Prev/Next buttons work correctly
- [ ] Text alignment is correct
- [ ] Icons align properly
- [ ] Focus indicators appear on correct side

### 10.4 Keyboard Navigation
- [ ] Tab focuses cards and buttons
- [ ] Enter/Space activates focused element
- [ ] Arrow keys navigate slider (if implemented)
- [ ] Focus indicators are visible
- [ ] Focus doesn't jump unexpectedly

### 10.5 Links Working
- [ ] All category links navigate correctly
- [ ] Right-click "Open in new tab" works
- [ ] Browser back button works
- [ ] Active category highlighted correctly
- [ ] URL matches category slug

### 10.6 Accessibility
- [ ] Screen reader announces correctly
- [ ] ARIA labels are descriptive
- [ ] Focus management works
- [ ] Reduced motion respected
- [ ] Color contrast meets WCAG AA

### 10.7 Performance
- [ ] Page loads quickly
- [ ] Animations are smooth (60fps)
- [ ] No layout thrashing
- [ ] No memory leaks
- [ ] Works on low-end devices

---

## 11) Implementation Order

1. **Create CSS file** (`static/css/ads-category-slider.css`)
   - Base styles, scoped under `.ads-category-slider`
   - Responsive breakpoints
   - RTL support
   - Fallback grid layout

2. **Create JavaScript file** (`static/js/ads-category-slider.js`)
   - Initialization logic
   - Center-mode calculation
   - Scroll handling
   - Keyboard navigation
   - RTL detection

3. **Create template partial** (`ads/templates/ads/includes/_category_slider.html`)
   - HTML structure
   - Django template loop
   - ARIA attributes
   - Fallback layout

4. **Update main template** (`ads/templates/ads/ads_home.html`)
   - Include partial
   - Load CSS/JS
   - Remove old category section (or keep as fallback)

5. **Test thoroughly**
   - Desktop, tablet, mobile
   - RTL layout
   - Keyboard navigation
   - Screen readers
   - Performance

---

## 12) Deliverables Summary

**New Files:**
1. `ads/templates/ads/includes/_category_slider.html` - Template partial
2. `static/css/ads-category-slider.css` - Scoped CSS
3. `static/js/ads-category-slider.js` - Scoped JavaScript

**Modified Files:**
1. `ads/templates/ads/ads_home.html` - Include partial, load CSS/JS

**No Changes Needed:**
- `ads/views.py` - View provides correct data
- `ads/models.py` - Model structure is fine
- `static/css/style.css` - Existing styles remain (coexist)

---

## 13) Confirmation

**✅ This is a READ-ONLY technical plan.**

**✅ No code changes have been made yet.**

**✅ Implementation will follow this plan.**

---

**Plan Complete.** ✅

