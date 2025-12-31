# Color System Refactoring - Phase 5: Category Filter Buttons (Glass-morphism)

## Overview
This document summarizes Phase 5 of the color system refactoring, focusing on the glass-morphism category filter buttons and mapping them to semantic colors.

## Changes Made

### Category Button Accent Rings

#### 1. Mint Tone (Row 1) - Secondary Color
**Before:**
```css
.category-btn[data-tone="mint"] {
  inset 0 0 0 2px rgba(16, 185, 129, 0.22); /* mint accent ring */
}

.category-btn[data-tone="mint"]:hover {
  inset 0 0 0 2px rgba(16, 185, 129, 0.3);
}
```

**After:**
```css
.category-btn[data-tone="mint"] {
  inset 0 0 0 2px rgba(31, 138, 112, 0.22); /* secondary color accent ring */
}

.category-btn[data-tone="mint"]:hover {
  inset 0 0 0 2px rgba(31, 138, 112, 0.3); /* secondary color accent ring */
}
```

**Impact**: Mint tone now uses secondary color token (#1F8A70) for accent rings. This row contains categories like law-integration, careers-economy, life-in-sweden, skills-learning, and platform-updates.

#### 2. Purple Tone (Row 2) - Experiences Semantic Color
**Before:**
```css
.category-btn[data-tone="purple"] {
  inset 0 0 0 2px rgba(139, 92, 246, 0.22); /* purple accent ring */
}

.category-btn[data-tone="purple"]:hover {
  inset 0 0 0 2px rgba(139, 92, 246, 0.3);
}
```

**After:**
```css
.category-btn[data-tone="purple"] {
  inset 0 0 0 2px rgba(155, 89, 182, 0.22); /* experiences semantic color accent ring */
}

.category-btn[data-tone="purple"]:hover {
  inset 0 0 0 2px rgba(155, 89, 182, 0.3); /* experiences semantic color accent ring */
}
```

**Impact**: Purple tone now uses experiences semantic color token (#9B59B6). This row contains events-announcements and photo-gallery categories.

#### 3. Peach Tone (Row 3) - Events Semantic Color
**Before:**
```css
.category-btn[data-tone="peach"] {
  inset 0 0 0 2px rgba(251, 146, 60, 0.22); /* peach accent ring */
}

.category-btn[data-tone="peach"]:hover {
  inset 0 0 0 2px rgba(251, 146, 60, 0.3);
}
```

**After:**
```css
.category-btn[data-tone="peach"] {
  inset 0 0 0 2px rgba(230, 126, 34, 0.22); /* events semantic color accent ring */
}

.category-btn[data-tone="peach"]:hover {
  inset 0 0 0 2px rgba(230, 126, 34, 0.3); /* events semantic color accent ring */
}
```

**Impact**: Peach tone now uses events semantic color token (#E67E22). This row contains public-services, stories-experiences, community-engagement, and personalities categories.

#### 4. Active State - CTA Services Color
**Before:**
```css
.category-btn.active {
  border-color: rgba(251, 191, 36, 0.6); /* amber border */
  box-shadow: 0 6px 20px rgba(251, 191, 36, 0.25), 
              inset 0 0 0 2px rgba(251, 191, 36, 0.35);
}

.category-btn.active:hover {
  box-shadow: 0 8px 24px rgba(251, 191, 36, 0.3), 
              inset 0 0 0 2px rgba(251, 191, 36, 0.45);
}
```

**After:**
```css
.category-btn.active {
  border-color: rgba(244, 180, 0, 0.6); /* CTA Services color */
  box-shadow: 0 6px 20px rgba(244, 180, 0, 0.25), 
              inset 0 0 0 2px rgba(244, 180, 0, 0.35); /* CTA Services color */
}

.category-btn.active:hover {
  box-shadow: 0 8px 24px rgba(244, 180, 0, 0.3), 
              inset 0 0 0 2px rgba(244, 180, 0, 0.45); /* CTA Services color */
}
```

**Impact**: Active state now uses CTA Services color token (#F4B400) for consistency.

#### 5. Text Colors
**Before:**
```css
.category-btn {
  color: #0f172a; /* slate-900 */
}

.category-btn:hover {
  color: #0f172a;
}
```

**After:**
```css
.category-btn {
  color: var(--pv-text-main); /* Use main text color token */
}

.category-btn:hover {
  color: var(--pv-text-main); /* Use main text color token */
}
```

**Impact**: Text colors now use main text token for consistency.

#### 6. Shadows
**Before:**
```css
.category-btn {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12), 
              0 2px 6px rgba(0, 0, 0, 0.08);
}

.category-btn:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18), 
              0 4px 12px rgba(0, 0, 0, 0.12);
}
```

**After:**
```css
.category-btn {
  box-shadow: 0 4px 16px var(--pv-shadow-soft), 
              0 2px 6px var(--pv-shadow-soft);
}

.category-btn:hover {
  box-shadow: 0 8px 24px var(--pv-shadow-medium), 
              0 4px 12px var(--pv-shadow-soft);
}
```

**Impact**: Shadows now use design tokens.

#### 7. Focus State
**Before:**
```css
.category-btn:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.6); /* blue-500 */
}
```

**After:**
```css
.category-btn:focus-visible {
  outline: 2px solid var(--pv-cta-ask); /* Use CTA Ask color */
}
```

**Impact**: Focus state uses CTA Ask color token for accessibility.

---

## Category Mapping

### Row 1 (Mint Tone → Secondary Color)
- **platform-updates** - Uses secondary color (#1F8A70)
- **careers-economy** - Uses secondary color (Economy semantic: #1E8449 - very similar)
- **life-in-sweden** - Uses secondary color (Life semantic: #48C9B0 - similar green family)
- **law-integration** - Uses secondary color (Legal semantic: #2C7BE5 - different, but grouped)
- **skills-learning** - Uses secondary color (Education semantic: #5DADE2 - different, but grouped)

**Note**: Row 1 uses secondary color as a compromise since categories have different semantic meanings. Future enhancement could add individual category-specific colors.

### Row 2 (Purple Tone → Experiences Color)
- **events-announcements** - Uses experiences color (#9B59B6)
- **photo-gallery** - Uses experiences color (#9B59B6)

**Note**: Both categories relate to experiences/stories, so the purple experiences color is appropriate.

### Row 3 (Peach Tone → Events Color)
- **public-services** - Uses events color (#E67E22) (Public semantic: #7DCEA0 - different, but grouped)
- **stories-experiences** - Uses events color (#E67E22) (Experiences semantic: #9B59B6 - different, but grouped)
- **community-engagement** - Uses events color (#E67E22) (People semantic: #566573 - different, but grouped)
- **personalities** - Uses events color (#E67E22) (People semantic: #566573 - different, but grouped)

**Note**: Row 3 uses events color as a compromise. Future enhancement could add individual category-specific colors.

---

## Visual Changes Summary

### Accent Rings
- **Mint tone**: Changed from teal/mint (`rgba(16, 185, 129)`) to secondary green (`rgba(31, 138, 112)`)
- **Purple tone**: Changed from purple (`rgba(139, 92, 246)`) to experiences purple (`rgba(155, 89, 182)`)
- **Peach tone**: Changed from orange (`rgba(251, 146, 60)`) to events orange (`rgba(230, 126, 34)`)

### Active State
- Changed from amber (`rgba(251, 191, 36)`) to CTA Services yellow (`rgba(244, 180, 0)`)

### Text & Shadows
- Text colors use main text token
- Shadows use shadow tokens
- Focus state uses CTA Ask color

---

## Files Modified

1. **`static/css/style.css`**
   - Updated `.category-btn[data-tone="mint"]` accent rings
   - Updated `.category-btn[data-tone="purple"]` accent rings
   - Updated `.category-btn[data-tone="peach"]` accent rings
   - Updated `.category-btn.active` colors
   - Updated text colors to use tokens
   - Updated shadows to use tokens
   - Updated focus state to use CTA Ask color

---

## Testing Checklist

### ✅ Category Buttons
- [ ] Mint tone buttons show secondary green accent rings
- [ ] Purple tone buttons show experiences purple accent rings
- [ ] Peach tone buttons show events orange accent rings
- [ ] Active state shows CTA Services yellow
- [ ] Hover states work correctly for all tones
- [ ] Glass-morphism effect is preserved
- [ ] Text is readable on all buttons
- [ ] Focus states are visible (keyboard navigation)

### ✅ Responsive Design
- [ ] Desktop: Category buttons display correctly
- [ ] Tablet: Buttons wrap correctly
- [ ] Mobile: Buttons stack correctly
- [ ] No layout shifts

### ✅ RTL Support
- [ ] Persian text readable
- [ ] Buttons aligned correctly in RTL
- [ ] Icons positioned correctly
- [ ] No layout issues

### ✅ Accessibility
- [ ] Text contrast meets WCAG AA standards
- [ ] Focus indicators visible
- [ ] Hover states provide clear feedback
- [ ] Active state is clearly distinguishable

---

## Color Mapping

### Accent Rings
| Tone | Old Color | New Color | Token Used |
|------|-----------|-----------|------------|
| Mint | `rgba(16, 185, 129, 0.22)` | `rgba(31, 138, 112, 0.22)` | Secondary (#1F8A70) |
| Purple | `rgba(139, 92, 246, 0.22)` | `rgba(155, 89, 182, 0.22)` | Experiences (#9B59B6) |
| Peach | `rgba(251, 146, 60, 0.22)` | `rgba(230, 126, 34, 0.22)` | Events (#E67E22) |

### Active State
| Element | Old Color | New Color | Token Used |
|---------|-----------|-----------|------------|
| Border | `rgba(251, 191, 36, 0.6)` | `rgba(244, 180, 0, 0.6)` | CTA Services (#F4B400) |
| Shadow | `rgba(251, 191, 36, 0.25)` | `rgba(244, 180, 0, 0.25)` | CTA Services (#F4B400) |
| Accent Ring | `rgba(251, 191, 36, 0.35)` | `rgba(244, 180, 0, 0.35)` | CTA Services (#F4B400) |

---

## Notes

### Design Decisions
1. **Tone-based grouping**: Maintained the data-tone system for visual grouping while updating colors to semantic tokens.
2. **Semantic color mapping**: Used semantic colors where appropriate (experiences for purple, events for peach).
3. **Secondary color for mint**: Used secondary color for mint tone as it's in the green family and works well for the grouped categories.
4. **Active state**: Used CTA Services color for active state to maintain brand consistency.
5. **Glass-morphism preserved**: All glass-morphism effects (backdrop-filter, transparency, gradients) are maintained.

### Future Enhancements
- Consider adding individual category-specific accent colors based on category slug
- Could add data attributes like `data-category="legal"` to map directly to semantic colors
- Could create category-specific CSS classes for more precise color mapping

---

## Rollback Plan

If issues arise, revert `static/css/style.css` to the previous commit:

```bash
git checkout HEAD~1 -- static/css/style.css
```

Or manually restore the old color values from this document.

---

**Status**: ✅ Phase 5 (Category Filter Buttons) Complete
**Next Phase**: Continue with other sections (forms, alerts, etc.)

