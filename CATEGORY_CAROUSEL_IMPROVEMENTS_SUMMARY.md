# Category Carousel Improvements - Implementation Summary

**Date:** 2025-02-07  
**Status:** ✅ Complete

---

## Changes Implemented

### A) Unified Icons + Colors (Single Source of Truth)

**1. Template Tags Created:**
- **File:** `blog/templatetags/category_extras.py`
- **Filters:**
  - `category_icon(category)` - Returns Bootstrap Icons class based on slug
  - `category_color(category)` - Returns hex pastel color based on slug
  - Both use case-insensitive slug lookup
  - Fallbacks: `bi bi-grid-3x3-gap` for icons, `#F5F7FA` for colors

**2. Icon Mapping (13 categories):**
- `skills-learning` → `bi bi-mortarboard`
- `careers-economy` → `bi bi-briefcase`
- `stories-experiences` → `bi bi-journal-text`
- `photo-gallery` → `bi bi-images`
- `events-announcements` → `bi bi-calendar-event`
- `zbn-o-rtbt` → `bi bi-chat-dots`
- `slmt-ron-dr-mhgrt` → `bi bi-people-heart` ✅ (mental health icon confirmed)
- `platform-updates` → `bi bi-newspaper`
- `public-services` → `bi bi-compass`
- `law-integration` → `bi bi-shield-check`
- `life-in-social` → `bi bi-people`
- `guide-questions` → `bi bi-question-circle`
- `personalities` → `bi bi-person-badge`

**3. Color Mapping (13 categories):**
- `skills-learning` → `#E8F3FF`
- `careers-economy` → `#EAF7F1`
- `stories-experiences` → `#FFF4E8`
- `photo-gallery` → `#F3EEFF`
- `events-announcements` → `#FFF0E1`
- `zbn-o-rtbt` → `#E9F7FA`
- `slmt-ron-dr-mhgrt` → `#EFEAFF`
- `platform-updates` → `#F1F3F5`
- `public-services` → `#EEF7FA`
- `law-integration` → `#EAF0FF`
- `life-in-social` → `#ECF8F1`
- `guide-questions` → `#FFF9E6`
- `personalities` → `#FCEEF3`

**4. Applied Everywhere:**
- ✅ Carousel partial (`templates/includes/category_carousel.html`)
- ✅ Uses `{{ category|category_icon }}` and `{{ category|category_color }}`
- ✅ Colors applied via CSS variable: `style="--cat-bg: {{ category|category_color }}"`
- ✅ CSS uses `var(--cat-bg, var(--cat-bg-fallback))` for gradient backgrounds

---

### B) Layout Update: 7 Cards on Desktop + Wider Cards

**Desktop (≥992px):**
- ✅ **7 cards visible** (center + 3 on each side)
- ✅ Card width: 185px (increased from 168px, ~10% wider)
- ✅ Transform positions:
  - `prev-1`: -200px translateX, -100px translateZ, 20deg rotateY
  - `prev-2`: -380px translateX, -180px translateZ, 35deg rotateY
  - `prev-3`: -540px translateX, -240px translateZ, 45deg rotateY
  - `next-1/2/3`: Same but positive translateX and negative rotateY
- ✅ Perspective: 1000px (increased from 800px)

**Tablet (768px-991px):**
- ✅ **5 cards visible** (center + 2 on each side)
- ✅ Card width: 170px
- ✅ `prev-3` and `next-3` hidden (opacity: 0)
- ✅ Transform positions adjusted for 5-card layout

**Mobile (<768px):**
- ✅ **3 cards visible** (center + 1 on each side)
- ✅ Card width: 144px
- ✅ `prev-2`, `prev-3`, `next-2`, `next-3` hidden
- ✅ Optimized for swipe gestures

**JavaScript Updates:**
- ✅ `getVisibleCount()` function detects breakpoint (7/5/3)
- ✅ `updateCards()` dynamically applies classes based on visible count
- ✅ Window resize handler updates card positions
- ✅ RTL navigation still works correctly

---

### C) Carousel Consistency

**Already Implemented:**
- ✅ Reusable partial: `templates/includes/category_carousel.html`
- ✅ Used on homepage: `blog/templates/blog/index.html`
- ✅ Used on category listing pages: `blog/templates/blog/category_posts.html`
- ✅ JS loads on both pages via `{% block extras %}`

**No Additional Changes Needed:**
- Carousel already applied consistently across all category pages

---

## Files Changed

### **New Files:**
- None (template tags already existed, just updated)

### **Modified Files:**

1. **`blog/templatetags/category_extras.py`**
   - Added `CATEGORY_ICON_MAP` dictionary (13 mappings)
   - Added `CATEGORY_COLOR_MAP` dictionary (13 mappings)
   - Added `category_icon()` filter
   - Added `category_color()` filter
   - Kept `category_color_index()` for backward compatibility

2. **`templates/includes/category_carousel.html`**
   - Replaced hardcoded icon conditionals with `{{ category|category_icon }}`
   - Replaced `data-color-index` with `style="--cat-bg: {{ category|category_color }}"`
   - Updated noscript fallback to use template tag

3. **`static/css/style.css`**
   - Removed old 12-color palette CSS variables
   - Updated `.category-carousel-card` to use `var(--cat-bg)` CSS variable
   - Increased card width: 168px → 185px (desktop)
   - Added `prev-3` and `next-3` transform positions for 7-card layout
   - Updated responsive breakpoints:
     - Desktop (≥992px): 7 cards, 185px width
     - Tablet (768-991px): 5 cards, 170px width
     - Mobile (<768px): 3 cards, 144px width
   - Updated all transform values for new layout
   - Fixed duplicate `::before` rule

4. **`static/js/category-carousel.js`**
   - Added `getVisibleCount()` function for responsive breakpoint detection
   - Updated `updateCards()` to handle `prev-3` and `next-3` classes
   - Added window resize handler to update positions on breakpoint change
   - Dynamic class assignment based on visible count (7/5/3)

---

## Verification Checklist

### ✅ **Icons + Colors:**
- [x] Template tags created with all 13 category mappings
- [x] Icons use Bootstrap Icons only
- [x] Colors are soft pastels with good contrast
- [x] Case-insensitive slug lookup (handles `Guide-Questions` correctly)
- [x] Fallbacks defined (`bi bi-grid-3x3-gap`, `#F5F7FA`)
- [x] Applied in carousel partial
- [x] CSS uses `var(--cat-bg)` for gradient backgrounds
- [x] Mental health icon confirmed: `bi bi-people-heart` ✅

### ✅ **Layout:**
- [x] Desktop shows 7 visible cards (center + 3 each side)
- [x] Cards slightly wider (185px vs 168px, ~10% increase)
- [x] Tablet shows 5 visible cards (center + 2 each side)
- [x] Mobile shows 3 visible cards (center + 1 each side)
- [x] Transform positions adjusted for each breakpoint
- [x] No overflow on any screen size
- [x] Swipe gestures work on mobile
- [x] Navigation buttons work on all breakpoints

### ✅ **Consistency:**
- [x] Carousel appears on homepage
- [x] Carousel appears on category listing pages
- [x] Same carousel component used everywhere (partial)
- [x] JS loads on both pages
- [x] Active category highlighted on category pages

### ✅ **RTL + Accessibility:**
- [x] RTL transforms updated for all new positions
- [x] Navigation buttons swapped for RTL
- [x] ARIA labels maintained
- [x] Keyboard navigation works
- [x] Screen reader support maintained

---

## Icon + Color Mappings Reference

### Icon Mappings (Slug → Bootstrap Icons):
```python
'skills-learning': 'bi bi-mortarboard'
'careers-economy': 'bi bi-briefcase'
'stories-experiences': 'bi bi-journal-text'
'photo-gallery': 'bi bi-images'
'events-announcements': 'bi bi-calendar-event'
'zbn-o-rtbt': 'bi bi-chat-dots'
'slmt-ron-dr-mhgrt': 'bi bi-people-heart'  # Mental health
'platform-updates': 'bi bi-newspaper'
'public-services': 'bi bi-compass'
'law-integration': 'bi bi-shield-check'
'life-in-social': 'bi bi-people'
'guide-questions': 'bi bi-question-circle'
'personalities': 'bi bi-person-badge'
```

### Color Mappings (Slug → Hex Pastel):
```python
'skills-learning': '#E8F3FF'
'careers-economy': '#EAF7F1'
'stories-experiences': '#FFF4E8'
'photo-gallery': '#F3EEFF'
'events-announcements': '#FFF0E1'
'zbn-o-rtbt': '#E9F7FA'
'slmt-ron-dr-mhgrt': '#EFEAFF'
'platform-updates': '#F1F3F5'
'public-services': '#EEF7FA'
'law-integration': '#EAF0FF'
'life-in-social': '#ECF8F1'
'guide-questions': '#FFF9E6'
'personalities': '#FCEEF3'
```

---

## Implementation Details

### Color Application:
- Template sets: `style="--cat-bg: {{ category|category_color }}"`
- CSS uses: `background: linear-gradient(135deg, var(--cat-bg, var(--cat-bg-fallback)) 0%, rgba(255, 255, 255, 0.9) 100%);`
- Glass-morphism overlay maintained via `::before` pseudo-element

### Responsive Breakpoints:
- **Desktop (≥992px):** 7 cards, 185px width, full transforms
- **Tablet (768-991px):** 5 cards, 170px width, prev-3/next-3 hidden
- **Mobile (<768px):** 3 cards, 144px width, only prev-1/next-1 visible

### JavaScript Logic:
- `getVisibleCount()`: Returns 7, 5, or 3 based on window width
- `updateCards()`: Dynamically applies position classes based on visible count
- Resize handler: Updates positions when breakpoint changes
- All navigation methods (buttons, touch, wheel, keyboard) work with new layout

---

## Summary

**All requirements implemented:**
- ✅ Unified icon/color system with single source of truth
- ✅ 7 cards visible on desktop, 5 on tablet, 3 on mobile
- ✅ Cards slightly wider (185px desktop)
- ✅ Carousel consistent across all pages
- ✅ Mental health icon: `bi bi-people-heart` ✅
- ✅ RTL and accessibility maintained

**Files Changed:** 4 files modified  
**Complexity:** Medium  
**Risk:** Low (backward compatible)

---

**Implementation Complete** ✅

