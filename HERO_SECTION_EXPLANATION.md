# Hero Section Code Explanation

## Overview
The hero section is the main visual area at the top of the homepage. It has **different layouts for mobile and desktop** devices, using Bootstrap's responsive utilities and custom CSS.

---

## 📱 **MOBILE LAYOUT** (≤768px)

### Structure (Top to Bottom):
1. **Hero Image** (Mobile Only)
2. **CTA Cards** (3 gradient feature cards)
3. Rest of homepage content

### Code Breakdown:

#### 1. Hero Image (Mobile Only)
```html
<!-- Lines 5-13 in blog/templates/blog/index.html -->
<div class="d-lg-none hero-image-mobile-wrapper">
  <img src="{% static 'images/hero-mobile.png' %}" 
       class="img-fluid w-100 hero-mobile-img" />
</div>
```

**Key Classes:**
- `d-lg-none` = Hide on large screens (≥992px), show only on mobile/tablet
- `hero-image-mobile-wrapper` = Full-width container with teal background
- `hero-mobile-img` = Image styled to be 56% width, centered

**CSS Styling:**
```css
.hero-image-mobile-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;  /* Centers the image */
  background: #00A693;      /* Teal background */
  margin-top: 15px;         /* 15px spacing from navbar */
}

.hero-mobile-img {
  width: 56% !important;    /* 20% smaller than original size */
  object-fit: contain;       /* Maintains aspect ratio */
  margin: 0 auto;           /* Centers horizontally */
}
```

---

#### 2. Hero Section Container
```html
<!-- Lines 15-24 in blog/templates/blog/index.html -->
<section class="hero-section text-white">
  <div class="container">
    <div class="row align-items-center g-2">
      <div class="col-12 col-lg-6 order-lg-2">
        <div class="hero-content text-center">
          {% include 'includes/hero_cta_cards.html' %}
        </div>
      </div>
      <!-- Featured Post (hidden on mobile with d-none d-lg-block) -->
    </div>
  </div>
</section>
```

**On Mobile:**
- `col-12` = Full width (12 columns)
- Featured post is **hidden** (`d-none d-lg-block`)
- Only CTA cards are visible

**CSS for Mobile:**
```css
@media (max-width: 768px) {
  .hero-section {
    padding: 0 !important;  /* No padding on mobile */
    margin: 0 !important;
  }
  
  .hero-section .container {
    padding: 0 !important;  /* Remove container padding */
  }
}
```

---

#### 3. CTA Cards (Feature Cards)
```html
<!-- templates/includes/hero_cta_cards.html -->
<div class="hero-cta-cards-container">
  <!-- Card 1: Orange (Create Post) -->
  <a href="..." class="hero-cta-card hero-cta-card-orange">
    <div class="hero-cta-card-icon">...</div>
    <div class="hero-cta-card-content">...</div>
    <div class="hero-cta-card-arrow">...</div>
  </a>
  <!-- Card 2: Blue (Ask Me) -->
  <!-- Card 3: Yellow (Guide) -->
</div>
```

**Card Structure:**
- **Icon** (left side) - FontAwesome icon with low opacity
- **Content** (center) - Title + Subtitle in Persian (RTL)
- **Arrow** (right side) - Points left (RTL direction)

**CSS Styling:**
```css
.hero-cta-cards-container {
  display: flex;
  flex-direction: column;  /* Stacked vertically */
  gap: 0.8rem;            /* Space between cards */
  max-width: 500px;       /* Limit width on desktop */
  margin: 0 auto;         /* Center the container */
}

.hero-cta-card {
  display: flex;
  align-items: center;
  padding: 1rem 1.2rem;
  border-radius: 24px;
  min-height: 72px;
  /* Gradient background (orange/blue/yellow) */
  transition: all 0.2s ease;
}

.hero-cta-card:hover {
  transform: translateY(-4px);  /* Lift effect */
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
}
```

**Mobile-Specific Margins:**
```css
@media (max-width: 768px) {
  /* First card gets 15px top margin */
  .hero-cta-cards-container .hero-cta-card:first-child {
    margin-top: 15px;
  }
  
  /* Last card gets 15px bottom margin */
  .hero-cta-cards-container .hero-cta-card:last-child {
    margin-bottom: 15px;
  }
}
```

---

## 🖥️ **DESKTOP LAYOUT** (≥992px)

### Structure (Side by Side):
- **Left Column:** Featured Post Card
- **Right Column:** CTA Cards

### Code Breakdown:

```html
<div class="row align-items-center g-2">
  <!-- Right Column: CTA Cards -->
  <div class="col-12 col-lg-6 order-lg-2">
    {% include 'includes/hero_cta_cards.html' %}
  </div>
  
  <!-- Left Column: Featured Post -->
  <div class="col-12 col-lg-6 order-lg-1 d-none d-lg-block">
    <!-- Featured post card -->
  </div>
</div>
```

**Key Classes:**
- `col-lg-6` = Each column takes 6/12 width (50%) on large screens
- `order-lg-1` = Featured post appears first (left) on desktop
- `order-lg-2` = CTA cards appear second (right) on desktop
- `d-none d-lg-block` = Hide on mobile, show on desktop

**CSS:**
```css
.hero-section {
  padding: 0.75rem 0;  /* Has padding on desktop */
  background: #00A693;
}
```

---

## 🎨 **Visual Design**

### Color Scheme:
- **Background:** Teal (#00A693)
- **Card 1:** Orange gradient (#ff6b35 → #f7931e)
- **Card 2:** Blue gradient (#4a90e2 → #357abd)
- **Card 3:** Yellow gradient (#ffc107 → #ffb300)

### Typography:
- **Title:** 1.12rem, bold (700), white
- **Subtitle:** 0.8rem, regular (400), white with 90% opacity
- **RTL Support:** `direction: rtl` for Persian text

### Interactions:
- **Hover Effect:** Cards lift up 4px with stronger shadow
- **Arrow Animation:** Moves left 5px on hover
- **Gradient Change:** Background becomes lighter on hover

---

## 📐 **Responsive Breakpoints**

### Mobile (≤576px):
- Hero image: 56% width, 15px top margin
- Cards: Smaller padding, reduced font sizes
- No padding in hero section

### Tablet (577px - 768px):
- Hero image: 56% width, 15px top margin
- Cards: Medium sizing
- No padding in hero section

### Desktop (≥992px):
- Hero image: **Hidden** (d-lg-none)
- Featured post: **Visible** (d-lg-block)
- Cards: Full size, side-by-side with featured post
- Hero section: Has padding (0.75rem)

---

## 🔄 **How It Works Together**

1. **Page Loads:**
   - Django template renders `blog/index.html`
   - Includes `hero_cta_cards.html` partial

2. **Responsive Detection:**
   - Bootstrap classes (`d-lg-none`, `d-none d-lg-block`) control visibility
   - CSS media queries adjust sizing and spacing

3. **Mobile View:**
   - Hero image shows first (after navbar)
   - CTA cards stack vertically below image
   - Featured post is hidden

4. **Desktop View:**
   - Hero image is hidden
   - Featured post and CTA cards appear side-by-side
   - Both columns are 50% width

5. **User Interaction:**
   - Clicking cards navigates to different pages
   - Hover effects provide visual feedback
   - Smooth transitions enhance UX

---

## 🛠️ **Key Technologies**

- **Bootstrap 5:** Grid system, responsive utilities
- **Django Templates:** Template inheritance, includes, conditionals
- **CSS3:** Flexbox, gradients, transitions, media queries
- **FontAwesome:** Icons for cards and arrows

---

## 📝 **Summary**

The hero section uses a **mobile-first approach** with:
- **Conditional rendering** (Bootstrap classes)
- **Responsive CSS** (media queries)
- **Reusable components** (template includes)
- **Smooth animations** (CSS transitions)

This creates a seamless experience across all device sizes while maintaining clean, maintainable code.

