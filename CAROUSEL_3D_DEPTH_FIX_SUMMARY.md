# Desktop 3D Carousel Fix - Implementation Summary

**Date:** 2025-02-07  
**Status:** ✅ Complete

---

## Problem Solved

**Issues Fixed:**
1. ✅ Cards had almost the same size/height, reducing 3D depth
2. ✅ Cards didn't expand/arrange smoothly ("نامنظم باز میشن")
3. ✅ Uneven spacing and jittery layout

**Solution:**
- Replaced class-based system with dynamic transform calculation
- Implemented non-linear scaling curves for stronger depth perception
- Consistent spacing based on card width
- Stable z-index ordering
- Smooth GPU-accelerated transitions

---

## Changes Implemented

### A) Non-Linear Scaling Algorithm (JavaScript)

**New System:**
- Replaced static CSS classes with dynamic inline transform calculation
- Uses configuration objects per breakpoint with curves for:
  - **Scale**: Non-linear reduction (1.0 → 0.88 → 0.78 → 0.70)
  - **TranslateZ**: Depth progression (0 → -80 → -150 → -200)
  - **RotateY**: Rotation angles (0 → 18° → 32° → 42°)
  - **Opacity**: Fade progression (1.0 → 0.9 → 0.75 → 0.6)

**Desktop Configuration:**
```javascript
{
  visibleCount: 7,
  halfVisible: 3,
  cardWidth: 185,
  spacingFactor: 1.15,  // Consistent spacing: cardWidth * spacingFactor
  scaleCurve: [1.0, 0.88, 0.78, 0.70],      // Non-linear scaling
  translateZCurve: [0, -80, -150, -200],     // Depth progression
  rotateYCurve: [0, 18, 32, 42],             // Rotation angles
  opacityCurve: [1.0, 0.9, 0.75, 0.6]       // Opacity fade
}
```

**Tablet Configuration:**
```javascript
{
  visibleCount: 5,
  halfVisible: 2,
  cardWidth: 170,
  spacingFactor: 1.1,
  scaleCurve: [1.0, 0.85, 0.72],
  translateZCurve: [0, -70, -130],
  rotateYCurve: [0, 20, 38],
  opacityCurve: [1.0, 0.85, 0.65]
}
```

**Mobile Configuration:**
```javascript
{
  visibleCount: 3,
  halfVisible: 1,
  cardWidth: 144,
  spacingFactor: 1.0,
  scaleCurve: [1.0, 0.82],
  translateZCurve: [0, -60],
  rotateYCurve: [0, 25],
  opacityCurve: [1.0, 0.8]
}
```

### B) Consistent Spacing Formula

**Spacing Calculation:**
```javascript
const baseSpacing = config.cardWidth * config.spacingFactor;
const translateX = diff * baseSpacing;
```

**Benefits:**
- ✅ No overlap or gaps
- ✅ Predictable positioning
- ✅ Responsive to card width changes
- ✅ Clean 7-card layout on desktop

### C) Stable Z-Index Ordering

**Formula:**
```javascript
const zIndex = 10 - absOffset;
```

**Result:**
- Center card (offset 0): z-index 10 (highest)
- First neighbors (offset 1): z-index 9
- Second neighbors (offset 2): z-index 8
- Third neighbors (offset 3): z-index 7
- Hidden cards: z-index 1

**Benefits:**
- ✅ Deterministic ordering
- ✅ No z-index conflicts
- ✅ Stable during navigation

### D) Smooth Transitions (CSS)

**Updates:**
- Added `will-change: transform, opacity` for GPU acceleration
- Removed `z-index` from transition (causes jitter)
- Removed height animations
- Increased perspective: 1000px → 1200px
- Smooth cubic-bezier easing: `cubic-bezier(0.4, 0, 0.2, 1)`

**Transform Origin:**
- Set `transform-origin: center center` for proper scaling

### E) Hover Effect Enhancement

**Implementation:**
- Store base transform in CSS variable: `--card-transform`
- Hover enhances transform: `var(--card-transform) translateZ(30px) scale(1.05)`
- Maintains 3D position while adding hover lift

---

## Scaling/Spacing Formula

### Non-Linear Scale Curve

**Desktop (7 cards):**
- Offset 0 (center): `scale(1.0)` - 100% size
- Offset 1: `scale(0.88)` - 88% size (12% reduction)
- Offset 2: `scale(0.78)` - 78% size (22% reduction)
- Offset 3: `scale(0.70)` - 70% size (30% reduction)

**Visual Impact:**
- Center card is **clearly largest** (1.0 vs 0.88 = 12% difference)
- Progressive reduction creates strong depth perception
- Non-linear curve makes differences more obvious

### Spacing Formula

**Desktop:**
```
baseSpacing = 185px (cardWidth) × 1.15 (spacingFactor) = 212.75px
translateX = offset × 212.75px
```

**Result:**
- Cards evenly spaced at ~213px intervals
- No overlap
- Clean 7-card layout

---

## Files Changed

### 1. `static/js/category-carousel.js`

**Changes:**
- ✅ Replaced `updateCards()` with dynamic transform calculation
- ✅ Added `getCarouselConfig()` with breakpoint-specific curves
- ✅ Implemented non-linear scaling algorithm
- ✅ Consistent spacing based on card width
- ✅ Stable z-index calculation
- ✅ Circular carousel wrapping logic
- ✅ CSS variable storage for hover enhancement

**Key Functions:**
- `getCarouselConfig()`: Returns configuration per breakpoint
- `updateCards()`: Calculates and applies transforms dynamically

### 2. `static/css/style.css`

**Changes:**
- ✅ Removed static transform classes (kept for compatibility)
- ✅ Added `will-change: transform, opacity` for GPU acceleration
- ✅ Increased perspective: 1000px → 1200px
- ✅ Updated transition to exclude z-index
- ✅ Added `transform-origin: center center`
- ✅ Enhanced hover effect using CSS variable
- ✅ Removed height-based animations

**Key Updates:**
- `.category-carousel`: Increased perspective
- `.category-carousel-card`: GPU acceleration, smooth transitions
- `.category-carousel-card:hover`: Enhanced with CSS variable

---

## Acceptance Criteria ✅

### Desktop 3D Depth
- ✅ Center card clearly larger than neighbors (1.0 vs 0.88 scale)
- ✅ Card sizes reduce progressively (1.0 → 0.88 → 0.78 → 0.70)
- ✅ Strong depth perception with translateZ progression
- ✅ Visual hierarchy is obvious and consistent

### Stable Layout
- ✅ No jittery or "نامنظم" arrangement
- ✅ Same spacing rules every update
- ✅ Smooth animations with GPU acceleration
- ✅ Deterministic positioning

### Functionality
- ✅ RTL support maintained (flipped transforms)
- ✅ All controls work (buttons/swipe/wheel/keyboard)
- ✅ Category links functional
- ✅ Accessibility maintained (ARIA labels, keyboard nav)
- ✅ No console errors

### Responsive
- ✅ Desktop: 7 cards visible
- ✅ Tablet: 5 cards visible
- ✅ Mobile: 3 cards visible
- ✅ Breakpoint transitions smooth

---

## Technical Details

### Transform Calculation

**For each card:**
```javascript
// Calculate offset from center
let diff = index - currentIndex;
// Handle circular wrapping
if (diff > totalCards / 2) diff -= totalCards;
if (diff < -totalCards / 2) diff += totalCards;

const absOffset = Math.abs(diff);
const baseSpacing = config.cardWidth * config.spacingFactor;

// Get values from curves
const scale = config.scaleCurve[absOffset];
const translateZ = config.translateZCurve[absOffset];
const rotateY = config.rotateYCurve[absOffset];
const opacity = config.opacityCurve[absOffset];

// Calculate transforms
const translateX = diff * baseSpacing;
const rotation = diff < 0 ? rotateY : -rotateY;
const zIndex = 10 - absOffset;

// Apply (with RTL support)
const transformStr = `translateX(${translateX}px) translateZ(${translateZ}px) rotateY(${rotation}deg) scale(${scale})`;
```

### RTL Support

**LTR:**
```javascript
transform: translateX(212px) translateZ(-80px) rotateY(-18deg) scale(0.88)
```

**RTL:**
```javascript
transform: translateX(-212px) translateZ(-80px) rotateY(18deg) scale(0.88)
```

---

## Visual Improvements

### Before:
- Cards similar size (minimal scaling)
- Uneven spacing
- Jittery transitions
- Weak 3D depth

### After:
- ✅ Center card 12% larger than first neighbor
- ✅ Progressive scaling: 1.0 → 0.88 → 0.78 → 0.70
- ✅ Consistent spacing: ~213px intervals
- ✅ Smooth GPU-accelerated animations
- ✅ Strong 3D depth with translateZ progression
- ✅ Stable, predictable layout

---

## Testing

**Verified:**
- ✅ Desktop shows 7 cards with clear size differences
- ✅ Center card is visually dominant
- ✅ Smooth navigation (buttons, swipe, wheel, keyboard)
- ✅ RTL layout works correctly
- ✅ No console errors
- ✅ No layout jitter
- ✅ Responsive breakpoints work

---

## Summary

**Problem:** Uneven scaling, jittery layout, weak 3D depth  
**Solution:** Non-linear scaling curves, consistent spacing, GPU-accelerated transforms  
**Result:** Strong 3D depth, smooth animations, stable layout

**Files Modified:** 2 files
- `static/js/category-carousel.js` - Dynamic transform calculation
- `static/css/style.css` - GPU acceleration, smooth transitions

**Complexity:** Medium  
**Risk:** Low (backward compatible, maintains all functionality)

---

**Implementation Complete** ✅

