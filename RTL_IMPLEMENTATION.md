# RTL Implementation Guide - Phase 1

## Overview

The site is **RTL (Persian-first) by default**, but supports mixing RTL and LTR content per page and per section using CSS classes and template blocks.

## Default Behavior

- **HTML lang**: `fa` (Persian)
- **HTML dir**: `rtl` (Right-to-Left)
- **Body class**: `rtl`

All pages inherit these defaults unless explicitly overridden.

## Full-Page LTR Override

To make an entire page LTR (English/Swedish), override the blocks in your template:

```django
{% extends 'base.html' %}

{% block html_lang %}en{% endblock %}
{% block html_dir %}ltr{% endblock %}
{% block body_class %}ltr{% endblock %}

{% block content %}
  <!-- Your page content here -->
{% endblock %}
```

**Example**: See `about/templates/about/about.html` for a working example.

## Mixing RTL and LTR Sections

### RTL Page with LTR Section

Inside an RTL page (default), wrap English/Swedish content in a `.ltr` div:

```django
{% block content %}
  <!-- Default RTL content -->
  <div class="rtl">
    <p>این متن فارسی است و از راست به چپ نمایش داده می‌شود.</p>
  </div>

  <!-- English/Swedish section forced to LTR -->
  <div class="ltr">
    <p>This is English text and displays left-to-right.</p>
  </div>
{% endblock %}
```

### LTR Page with RTL Section

Inside an LTR page, wrap Persian content in a `.rtl` div:

```django
{% block html_dir %}ltr{% endblock %}
{% block body_class %}ltr{% endblock %}

{% block content %}
  <!-- Default LTR content -->
  <div class="ltr">
    <p>This is English text.</p>
  </div>

  <!-- Persian section forced to RTL -->
  <div class="rtl">
    <p>این متن فارسی است.</p>
  </div>
{% endblock %}
```

## CSS Classes

### `.rtl` Class
- Sets `direction: rtl` and `text-align: right`
- Applies to inputs, textareas, cards, dropdowns, and Summernote editor

### `.ltr` Class
- Sets `direction: ltr` and `text-align: left`
- Applies to inputs, textareas, cards, dropdowns, and Summernote editor

## Files Modified

1. **`templates/base.html`**
   - Added `{% block html_lang %}fa{% endblock %}` (default: `fa`)
   - Added `{% block html_dir %}rtl{% endblock %}` (default: `rtl`)
   - Added `{% block body_class %}rtl{% endblock %}` (default: `rtl`)
   - Loaded `bidi.css` stylesheet

2. **`static/css/bidi.css`** (new file)
   - Defines `.rtl` and `.ltr` scope classes
   - Minimal safe rules for common components

3. **`about/templates/about/about.html`** (example)
   - Demonstrates full-page LTR override

## Verification Checklist

- ✅ Default pages render RTL (check homepage)
- ✅ A page can be forced to LTR via template blocks (check About page)
- ✅ A section can be forced to LTR inside RTL page using `<div class="ltr">`
- ✅ A section can be forced to RTL inside LTR page using `<div class="rtl">`

## Notes

- This is **Phase 1** - infrastructure only. No language switcher or Django i18n.
- Bootstrap layout and styling remain unchanged.
- CSS overrides are minimal and safe.
- Future phases can add translation strings and language detection.

