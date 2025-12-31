# Color System Refactoring - Phase 6: Forms & Inputs

## Overview
This document summarizes Phase 6 of the color system refactoring, focusing on form inputs, buttons, and validation states.

## Changes Made

### Form Inputs

#### 1. Input Borders
**Before:**
```css
.login-card .form-control {
  border: 1px solid #dadce0;
}

.collaboration-form input.form-control {
  border: 1px solid #dadce0;
}
```

**After:**
```css
.login-card .form-control {
  border: 1px solid var(--pv-border-soft);
}

.collaboration-form input.form-control {
  border: 1px solid var(--pv-border-soft);
}
```

**Impact**: All form input borders now use the border token for consistency.

#### 2. Input Focus States
**Before:**
```css
.login-card .form-control:focus {
  border-color: #188181;
  box-shadow: 0 0 0 3px rgba(24, 129, 129, 0.1);
}

.collaboration-form input.form-control:focus {
  border-color: #188181;
  box-shadow: 0 0 0 3px rgba(24, 129, 129, 0.1);
}
```

**After:**
```css
.login-card .form-control:focus {
  border-color: var(--pv-color-secondary);
  box-shadow: 0 0 0 3px rgba(31, 138, 112, 0.1);
}

.collaboration-form input.form-control:focus {
  border-color: var(--pv-color-secondary);
  box-shadow: 0 0 0 3px rgba(31, 138, 112, 0.1);
}
```

**Impact**: Focus states now use secondary color token for consistency.

#### 3. Form Labels
**Before:**
```css
.login-card .form-label {
  color: #3c4043;
}

.login-card .form-check-label {
  color: #5f6368;
}
```

**After:**
```css
.login-card .form-label {
  color: var(--pv-text-main);
}

.login-card .form-check-label {
  color: var(--pv-text-muted);
}
```

**Impact**: Labels now use text tokens for consistency.

#### 4. Form Help Text
**Before:**
```css
.login-card .form-text {
  color: #6c757d;
}
```

**After:**
```css
.login-card .form-text {
  color: var(--pv-text-muted);
}
```

**Impact**: Help text uses muted text token.

#### 5. Error Text
**Before:**
```css
.login-card .text-danger {
  color: #dc3545 !important;
}
```

**After:**
```css
.login-card .text-danger {
  color: var(--pv-validation-error) !important;
}
```

**Impact**: Error text uses validation error token.

### Form Buttons

#### 1. Signup/Edit Buttons
**Before:**
```css
.btn-signup,
.btn-edit {
  background-color: #188181;
  color: #fff;
}

.btn-signup:hover,
.btn-signup:active {
  background-color: #fff;
  color: #23bbbb;
}
```

**After:**
```css
.btn-signup,
.btn-edit {
  background-color: var(--pv-color-secondary);
  color: #fff;
}

.btn-signup:hover,
.btn-signup:active {
  background-color: var(--pv-bg-card);
  color: var(--pv-color-secondary);
}
```

**Impact**: Signup/edit buttons use secondary color token.

#### 2. Modal Primary Buttons
**Before:**
```css
#questionModal .modal-body .btn-primary {
  background-color: #00A693 !important;
  border-color: #00A693 !important;
}

#questionModal .modal-body .btn-primary:hover {
  background-color: #008a7a !important;
  border-color: #008a7a !important;
}
```

**After:**
```css
#questionModal .modal-body .btn-primary {
  background-color: var(--pv-color-secondary) !important;
  border-color: var(--pv-color-secondary) !important;
}

#questionModal .modal-body .btn-primary:hover {
  background-color: var(--pv-color-secondary) !important;
  filter: brightness(0.9);
  border-color: var(--pv-color-secondary) !important;
}
```

**Impact**: Modal buttons use secondary color token with brightness filter for hover.

#### 3. Google Sign In Button
**Before:**
```css
.btn-google {
  background-color: #fff;
  color: #3c4043;
  border: 1px solid #dadce0;
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15);
}

.btn-google:hover {
  background-color: #f8f9fa;
  box-shadow: 0 1px 3px 0 rgba(60, 64, 67, 0.3), 0 4px 8px 3px rgba(60, 64, 67, 0.15);
  color: #3c4043;
  border-color: #dadce0;
}
```

**After:**
```css
.btn-google {
  background-color: var(--pv-bg-card);
  color: var(--pv-text-main);
  border: 1px solid var(--pv-border-soft);
  box-shadow: 0 1px 2px 0 var(--pv-shadow-soft), 0 1px 3px 1px var(--pv-shadow-soft);
}

.btn-google:hover {
  background-color: var(--pv-bg-main);
  box-shadow: 0 1px 3px 0 var(--pv-shadow-soft), 0 4px 8px 3px var(--pv-shadow-medium);
  color: var(--pv-text-main);
  border-color: var(--pv-border-soft);
}
```

**Impact**: Google button uses design tokens for all colors and shadows.

### Validation States

#### 1. Pending Post Alert (Warning)
**Before:**
```css
.pending-post-alert {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  border-left: 4px solid #ffc107;
  color: #856404;
}

.pending-post-alert strong {
  color: #856404;
}

.pending-post-alert i {
  color: #ffc107;
}
```

**After:**
```css
.pending-post-alert {
  background: linear-gradient(135deg, rgba(244, 180, 0, 0.1) 0%, rgba(244, 180, 0, 0.15) 100%);
  border-left: 4px solid var(--pv-validation-warning);
  color: var(--pv-text-main);
}

.pending-post-alert strong {
  color: var(--pv-text-main);
}

.pending-post-alert i {
  color: var(--pv-validation-warning);
}
```

**Impact**: Warning alerts use validation warning token (CTA Services color).

### Other Form Elements

#### 1. Divider Lines
**Before:**
```css
.divider-line {
  background-color: #e0e0e0;
}

.divider-text {
  color: #757575;
}
```

**After:**
```css
.divider-line {
  background-color: var(--pv-border-soft);
}

.divider-text {
  color: var(--pv-text-muted);
}
```

**Impact**: Dividers use border and text tokens.

#### 2. Card Titles
**Before:**
```css
.login-card .card-title {
  color: #333;
}
```

**After:**
```css
.login-card .card-title {
  color: var(--pv-text-main);
}
```

**Impact**: Card titles use main text token.

---

## New Tokens Added

### Validation States
Added to `tokens.css`:
```css
--pv-validation-success: #1E8449; /* Green - success state */
--pv-validation-error: #E74C3C; /* Red - error state */
--pv-validation-warning: #F4B400; /* Yellow - warning state (uses CTA Services) */
--pv-validation-info: #3498DB; /* Blue - info state (uses CTA Ask) */
```

---

## Visual Changes Summary

### Form Inputs
- **Borders**: Changed from `#dadce0` to border token
- **Focus states**: Changed from `#188181` to secondary color token
- **Labels**: Changed from `#3c4043` to main text token
- **Help text**: Changed from `#6c757d` to muted text token
- **Error text**: Changed from `#dc3545` to validation error token

### Form Buttons
- **Signup/Edit**: Changed from `#188181` to secondary color token
- **Modal buttons**: Changed from `#00A693` to secondary color token
- **Google button**: All colors now use tokens

### Validation States
- **Warning alerts**: Changed from `#ffc107` to validation warning token
- **Error text**: Uses validation error token

---

## Files Modified

1. **`static/css/tokens.css`**
   - Added validation state tokens (success, error, warning, info)

2. **`static/css/style.css`**
   - Updated form input borders
   - Updated form input focus states
   - Updated form labels and help text
   - Updated error text colors
   - Updated signup/edit buttons
   - Updated modal buttons
   - Updated Google sign-in button
   - Updated pending post alert (warning)
   - Updated divider lines and text
   - Updated card titles

---

## Testing Checklist

### ✅ Form Inputs
- [ ] Input borders are visible and subtle
- [ ] Focus states show secondary green color
- [ ] Focus shadow is visible and not too strong
- [ ] Labels are readable
- [ ] Help text is visible but muted
- [ ] Error text is clearly visible (red)
- [ ] CAPTCHA inputs styled correctly
- [ ] Textarea inputs work correctly

### ✅ Form Buttons
- [ ] Signup buttons show secondary green
- [ ] Signup button hover shows white background with green text
- [ ] Modal primary buttons show secondary green
- [ ] Modal button hover darkens correctly
- [ ] Google sign-in button displays correctly
- [ ] Google button hover works
- [ ] All buttons maintain proper contrast

### ✅ Validation States
- [ ] Warning alerts show yellow/orange color
- [ ] Error messages show red color
- [ ] Success messages (if any) show green color
- [ ] Info messages (if any) show blue color
- [ ] Validation states are clearly distinguishable

### ✅ Responsive Design
- [ ] Desktop: Forms display correctly
- [ ] Tablet: Forms responsive
- [ ] Mobile: Forms stack correctly
- [ ] No horizontal scrolling issues
- [ ] Touch targets are adequate size

### ✅ RTL Support
- [ ] Persian text readable in forms
- [ ] Form labels aligned correctly in RTL
- [ ] Inputs aligned correctly in RTL
- [ ] Buttons positioned correctly
- [ ] No layout issues in RTL mode

### ✅ Accessibility
- [ ] Focus indicators visible (keyboard navigation)
- [ ] Color contrast meets WCAG AA standards:
  - [ ] Text on backgrounds
  - [ ] Error text on white background
  - [ ] Button text on button backgrounds
- [ ] Form labels are properly associated
- [ ] Error messages are accessible

---

## Color Mapping

### Form Inputs
| Element | Old Color | New Token | New Value |
|---------|-----------|-----------|-----------|
| Border | `#dadce0` | `--pv-border-soft` | `rgba(229, 231, 235, 0.5)` |
| Focus Border | `#188181` | `--pv-color-secondary` | `#1F8A70` |
| Focus Shadow | `rgba(24, 129, 129, 0.1)` | `rgba(31, 138, 112, 0.1)` | Secondary with opacity |
| Label | `#3c4043` | `--pv-text-main` | `#2C2C2C` |
| Help Text | `#6c757d` | `--pv-text-muted` | `#6B7280` |
| Error Text | `#dc3545` | `--pv-validation-error` | `#E74C3C` |

### Form Buttons
| Element | Old Color | New Token | New Value |
|---------|-----------|-----------|-----------|
| Signup BG | `#188181` | `--pv-color-secondary` | `#1F8A70` |
| Signup Hover BG | `#fff` | `--pv-bg-card` | `#FFFFFF` |
| Signup Hover Text | `#23bbbb` | `--pv-color-secondary` | `#1F8A70` |
| Modal Button | `#00A693` | `--pv-color-secondary` | `#1F8A70` |
| Google Button BG | `#fff` | `--pv-bg-card` | `#FFFFFF` |
| Google Button Text | `#3c4043` | `--pv-text-main` | `#2C2C2C` |

### Validation States
| Element | Old Color | New Token | New Value |
|---------|-----------|-----------|-----------|
| Warning | `#ffc107` | `--pv-validation-warning` | `#F4B400` |
| Error | `#dc3545` | `--pv-validation-error` | `#E74C3C` |

---

## Notes

### Design Decisions
1. **Focus states**: Using secondary color for consistency with the design system.
2. **Validation tokens**: Added new tokens for validation states to maintain semantic meaning.
3. **Warning color**: Uses CTA Services color (#F4B400) for consistency.
4. **Error color**: Uses standard red (#E74C3C) for clear error indication.
5. **Button hover**: Using brightness filter for hover states where appropriate for consistency.

### Future Enhancements
- Consider adding success/info alert styles if needed
- Could add form input validation states (is-valid, is-invalid) with visual feedback
- Could add loading states for form submissions
- Consider adding disabled state styling

---

## Rollback Plan

If issues arise, revert these files:
1. `static/css/tokens.css` - Remove validation tokens
2. `static/css/style.css` - Restore original form colors

**Git commands for rollback:**
```bash
git checkout HEAD~1 -- static/css/tokens.css static/css/style.css
```

---

**Status**: ✅ Phase 6 (Forms & Inputs) Complete
**Next Phase**: Continue with other sections (alerts, pagination, etc.)

