# Ads System - Full Technical Analysis & Architecture Report

**Date:** 2025-01-XX  
**Status:** 📋 Complete System Analysis  
**Project:** Peyvand (Djangoblog-4)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Database Models](#database-models)
4. [Views & URL Routing](#views--url-routing)
5. [Forms & Validation](#forms--validation)
6. [Templates & Frontend](#templates--frontend)
7. [Admin Interface](#admin-interface)
8. [Image Processing & Storage](#image-processing--storage)
9. [Filtering & Pagination](#filtering--pagination)
10. [Free/Pro Plan System](#freepro-plan-system)
11. [Static Sidebar Ads](#static-sidebar-ads)
12. [Security & Permissions](#security--permissions)
13. [Performance Considerations](#performance-considerations)
14. [Technical Strengths](#technical-strengths)
15. [Technical Weaknesses & Issues](#technical-weaknesses--issues)
16. [Recommended Improvements](#recommended-improvements)

---

## Executive Summary

The Peyvand Ads system is a comprehensive Django-based classified advertisements platform with the following key features:

- **Multi-category ad listings** with filtering and pagination
- **Free/Pro ad plans** with upgrade request workflow
- **Featured ads** with priority-based positioning
- **Image carousel** support (main + 2 optional extra images)
- **City-based filtering** and date sorting
- **User-owned ads** with CRUD operations
- **Comments system** on ads
- **Favorites/bookmarks** functionality
- **View count tracking** with session-based deduplication
- **Admin moderation** workflow (approval, URL approval, social URLs approval)
- **Static sidebar ads** (separate from dynamic ads)

**Technology Stack:**
- Django 4.2.18
- Cloudinary (image storage)
- Bootstrap 5 (UI framework)
- Pillow (image validation)
- django-ratelimit (rate limiting)

---

## System Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Templates  │  │  Static CSS  │  │  JavaScript  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Views     │  │    Forms     │  │   Admin      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Models     │  │  Database    │  │  Cloudinary   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
ads/
├── models.py              # Ad, AdCategory, FavoriteAd, AdComment, AdsViewCount
├── views.py               # All view functions (11 views)
├── urls.py                # URL routing
├── forms.py               # AdForm, AdCommentForm, AdFilterForm, ProRequestForm
├── admin.py               # Admin configuration
├── templatetags/
│   └── ads_extras.py      # Template filters (category icons, images)
├── templates/ads/
│   ├── ads_home.html      # Category listing page
│   ├── ads_by_category.html  # Ads list by category
│   ├── ad_detail.html     # Individual ad detail page
│   ├── create_ad.html     # Create ad form
│   ├── edit_ad.html       # Edit ad form
│   ├── delete_ad.html     # Delete confirmation
│   ├── my_ads.html        # User's ads list
│   └── includes/
│       └── _category_slider.html  # Category slider component
└── migrations/            # 14 migration files

blog/
└── utils.py               # increment_ad_view_count() helper function

static/
├── images/
│   ├── ad-1.jpg to ad-5.jpg  # Static sidebar ads
│   └── ad-top.jpg            # Top sidebar ad
└── css/
    └── style.css          # Ad styling (glass cards, badges, etc.)
```

---

## Database Models

### 1. AdCategory Model

**File:** `ads/models.py` (lines 8-30)

**Purpose:** Categories for organizing ads (e.g., "خدمات مالی", "خدمات آموزشی")

**Fields:**
- `name` (CharField, max_length=100, unique=True) - Category name in Persian
- `slug` (SlugField, max_length=100, unique=True) - URL-friendly identifier
- `description` (TextField, blank=True) - Optional category description
- `created_on` (DateTimeField, auto_now_add=True) - Creation timestamp

**Methods:**
- `ad_count()` - Returns count of approved, active ads in this category

**Database Indexes:** None (could benefit from index on `slug`)

**Admin:** `AdCategoryAdmin` - Simple list display with search

---

### 2. Ad Model

**File:** `ads/models.py` (lines 32-238)

**Purpose:** Main advertisement model - stores all ad data

**Key Fields:**

**Basic Information:**
- `title` (CharField, max_length=200) - Ad title
- `slug` (SlugField, max_length=200, unique=True, blank=True) - Auto-generated from title
- `category` (ForeignKey to AdCategory) - Required category
- `owner` (ForeignKey to User, null=True, blank=True) - Ad creator

**Images:**
- `image` (CloudinaryField, required) - Main ad image
- `extra_image_1` (CloudinaryField, optional) - Second image for carousel
- `extra_image_2` (CloudinaryField, optional) - Third image for carousel

**Links & URLs:**
- `target_url` (URLField, max_length=500) - Click-through URL
- `url_approved` (BooleanField, default=False) - Admin approval for target URL
- `instagram_url`, `telegram_url`, `website_url` (URLField, optional)
- `social_urls_approved` (BooleanField, default=False) - Admin approval for social URLs

**Location & Contact:**
- `city` (CharField, max_length=100, required) - City name
- `address` (TextField, max_length=500, required) - Full address
- `phone` (CharField, max_length=50, optional) - Phone number

**Moderation & Visibility:**
- `is_active` (BooleanField, default=True) - Soft delete flag
- `is_approved` (BooleanField, default=False) - Admin approval for listing
- `start_date`, `end_date` (DateField, optional) - Scheduling

**Featured System:**
- `is_featured` (BooleanField, default=False) - Featured status
- `featured_priority` (PositiveIntegerField, 1-39, optional) - Position priority
- `featured_until` (DateTimeField, optional) - Expiration date

**Free/Pro Plan:**
- `plan` (CharField, choices=[('free', 'Free'), ('pro', 'Pro')], default='free')
- `pro_requested` (BooleanField, default=False) - Pro upgrade requested
- `pro_request_phone` (CharField, max_length=30, optional) - Phone from Pro request
- `pro_requested_at` (DateTimeField, optional) - Request timestamp

**Timestamps:**
- `created_on` (DateTimeField, auto_now_add=True)
- `updated_on` (DateTimeField, auto_now=True)

**Database Indexes:**
- `Index(fields=['city'])` - For city filtering
- `Index(fields=['category', 'city'])` - Composite index for category+city queries

**Model Methods:**

1. **`save()`** (lines 201-213)
   - Auto-generates unique slug from title if not provided
   - Handles slug collisions with counter suffix

2. **`is_currently_visible()`** (lines 215-227)
   - Checks: `is_active`, `is_approved`, `url_approved`
   - Validates date range (`start_date`, `end_date`)
   - Returns boolean

3. **`is_currently_featured()`** (lines 229-237)
   - Checks: `is_featured=True` and `featured_until` not expired
   - Returns boolean

**Meta Options:**
- `ordering = ["-created_on"]` - Default ordering (newest first)
- Indexes for performance optimization

---

### 3. FavoriteAd Model

**File:** `ads/models.py` (lines 240-259)

**Purpose:** Many-to-many relationship between users and ads (bookmarks)

**Fields:**
- `user` (ForeignKey to User)
- `ad` (ForeignKey to Ad, related_name='favorites')
- `added_on` (DateTimeField, auto_now_add=True)

**Constraints:**
- `unique_together = ('user', 'ad')` - Prevents duplicate favorites

**Usage:** Users can save ads for later reference

---

### 4. AdComment Model

**File:** `ads/models.py` (lines 261-309)

**Purpose:** Comments on advertisements (published immediately, no moderation)

**Fields:**
- `ad` (ForeignKey to Ad, related_name='comments')
- `author` (ForeignKey to User, related_name='ad_comments')
- `body` (TextField) - Comment content (sanitized)
- `created_on`, `updated_on` (DateTimeField)
- `is_deleted` (BooleanField, default=False) - Soft delete flag

**Database Indexes:**
- `Index(fields=['ad', 'created_on'])` - For ad comment queries
- `Index(fields=['author', 'created_on'])` - For user comment queries

**Meta Options:**
- `ordering = ["created_on"]` - Oldest first

---

### 5. AdsViewCount Model

**File:** `ads/models.py` (lines 311-345)

**Purpose:** Aggregated view count cache (performance optimization)

**Fields:**
- `ad` (OneToOneField to Ad, related_name='view_count_cache', unique=True)
- `total_views` (PositiveIntegerField, default=0)
- `last_viewed_at` (DateTimeField, optional)
- `updated_at` (DateTimeField, auto_now=True)

**Purpose:** Stores pre-calculated view counts to avoid expensive COUNT queries

**Usage:** Updated atomically via `F()` expressions in `increment_ad_view_count()`

---

## Views & URL Routing

### URL Patterns

**File:** `ads/urls.py`

```python
urlpatterns = [
    path("", views.ad_category_list, name="ads_home"),                    # /ads/
    path("category/<slug:category_slug>/", views.ad_list_by_category, ...),  # /ads/category/legal-financial/
    path("ad/<slug:slug>/", views.ad_detail, name="ad_detail"),          # /ads/ad/my-ad-slug/
    path("create/", views.create_ad, name="create_ad"),                 # /ads/create/
    path("my-ads/", views.my_ads, name="my_ads"),                       # /ads/my-ads/
    path("edit/<slug:slug>/", views.edit_ad, name="edit_ad"),          # /ads/edit/my-ad-slug/
    path("delete/<slug:slug>/", views.delete_ad, name="delete_ad"),    # /ads/delete/my-ad-slug/
    path("add-to-favorites/<int:ad_id>/", ...),                        # /ads/add-to-favorites/123/
    path("remove-from-favorites/<int:ad_id>/", ...),                   # /ads/remove-from-favorites/123/
    path("ad/<slug:slug>/comment/<int:comment_id>/delete/", ...),      # /ads/ad/slug/comment/456/delete/
]
```

---

### View Functions

#### 1. `_visible_ads_queryset()` (Helper Function)

**File:** `ads/views.py` (lines 13-58)

**Purpose:** Base queryset for all visible ads (used by multiple views)

**Logic:**
1. Filters: `is_active=True`, `is_approved=True`
2. Date range: `start_date <= today <= end_date` (if set)
3. Annotates `is_currently_featured` (checks `featured_until`)
4. Annotates `priority_value` for sorting
5. Orders by: featured first → priority (lower = higher) → newest

**Returns:** QuerySet with `select_related("category")` for optimization

**Key Features:**
- Complex annotation logic for featured ads
- Handles featured expiration (`featured_until`)
- Priority-based sorting (1-39, lower = higher priority)

---

#### 2. `ad_category_list()` - Ads Home Page

**File:** `ads/views.py` (lines 61-84)

**URL:** `/ads/`

**Purpose:** Landing page showing all ad categories with counts

**Flow:**
1. Gets all categories ordered by name
2. Gets visible ads via `_visible_ads_queryset()`
3. Counts ads per category (in Python, not DB - could be optimized)
4. Renders `ads/ads_home.html`

**Template:** `ads/templates/ads/ads_home.html`

**Features:**
- Category slider with images
- Ad counts per category
- "Create Ad" button (if authenticated)

**Performance Note:** Category counting is done in Python loop - could use `annotate()` for better performance

---

#### 3. `ad_list_by_category()` - Category Listing

**File:** `ads/views.py` (lines 87-234)

**URL:** `/ads/category/<category_slug>/`

**Purpose:** Lists all ads in a specific category with filtering and pagination

**Complex Pagination Logic:**

**Page 1:**
- Featured ads first (up to 39 positions)
- Remaining slots filled with normal ads
- Total: 39 ads per page

**Page 2+:**
- Only normal ads (featured excluded)
- 39 ads per page

**Filtering:**
- **City filter:** `city__iexact=selected_city` (case-insensitive)
- **Sort order:** `newest` (default) or `oldest`
- Featured ads always appear first (not affected by sort)

**City Dropdown:**
- Dynamically populated from unique cities in current category
- Query: `Ad.objects.filter(category=category).values_list('city', flat=True).distinct()`

**Pagination:**
- Custom implementation (not using Django Paginator for page 1)
- Uses Django Paginator for page 2+
- Handles `EmptyPage` and `PageNotAnInteger` exceptions

**Template:** `ads/templates/ads/ads_by_category.html`

**Context Variables:**
- `category` - AdCategory instance
- `ads` - List of ads for current page
- `filter_form` - AdFilterForm instance
- `selected_city`, `sort_order` - Current filter values
- Pagination variables: `is_paginated`, `has_previous`, `has_next`, `current_page`, `total_pages`

**Performance Considerations:**
- City dropdown query could be cached
- Featured/normal separation done in Python (could be optimized with DB queries)

---

#### 4. `ad_detail()` - Ad Detail Page

**File:** `ads/views.py` (lines 237-360)

**URL:** `/ads/ad/<slug>/`

**Purpose:** Individual ad detail page with comments and Pro request

**Decorators:**
- `@ratelimit(key='ip', rate='20/m', method='POST')` - Rate limiting
- `@login_required` - Authentication required

**GET Request Flow:**
1. Gets ad from `_visible_ads_queryset()` (404 if not visible)
2. Increments view count (via `increment_ad_view_count()`)
3. Checks if user favorited this ad
4. Loads comments (excludes deleted)
5. Initializes forms (comment, Pro request)
6. Checks if user can request Pro upgrade

**POST Request Flow:**
- **Pro Request:** If `'pro_request' in request.POST`
  - Validates ownership
  - Checks if already Pro or already requested
  - Saves Pro request with phone number
- **Comment:** Otherwise
  - Requires site verification
  - Validates and saves comment (published immediately)

**View Count Tracking:**
- Calls `blog.utils.increment_ad_view_count(request, ad)`
- Session-based deduplication (30 minutes)
- Atomic update using `F()` expressions

**Template:** `ads/templates/ads/ad_detail.html`

**Context:**
- `ad` - Ad instance
- `is_favorited` - Boolean
- `comments` - QuerySet of comments
- `comment_form`, `pro_request_form` - Form instances
- `can_request_pro` - Boolean

---

#### 5. `create_ad()` - Create Ad

**File:** `ads/views.py` (lines 363-398)

**URL:** `/ads/create/`

**Purpose:** Allow users to create new ads

**Decorators:**
- `@ratelimit(key='user', rate='5/h')` - 5 ads per hour per user
- `@ratelimit(key='ip', rate='10/h')` - 10 ads per hour per IP
- `@site_verified_required` - Requires site verification
- `@login_required` - Authentication required

**Flow:**
1. **POST:** Validates form, sets `owner=request.user`, `is_approved=False`, `url_approved=False`, saves
2. **GET:** Shows form, pre-selects category if provided in query string

**Default Values:**
- `is_active = True`
- `is_approved = False` (requires admin approval)
- `url_approved = False` (requires admin approval)
- `plan = 'free'` (model default)

**Template:** `ads/templates/ads/create_ad.html`

---

#### 6. `edit_ad()` - Edit Ad

**File:** `ads/views.py` (lines 401-434)

**URL:** `/ads/edit/<slug>/`

**Purpose:** Allow ad owners to edit their ads

**Decorators:**
- `@site_verified_required`
- `@login_required`

**Security:**
- Ownership check: `if ad.owner != request.user: redirect()`

**Flow:**
1. **POST:** Validates form, resets approval if content changed
2. **GET:** Shows form with existing ad data

**Approval Reset Logic:**
- If ad was approved and user edits, sets `is_approved=False`, `url_approved=False`
- Admin must re-approve after edit

**Template:** `ads/templates/ads/edit_ad.html`

---

#### 7. `delete_ad()` - Delete Ad

**File:** `ads/views.py` (lines 437-455)

**URL:** `/ads/delete/<slug>/`

**Purpose:** Allow ad owners to delete their ads

**Decorators:**
- `@login_required`

**Security:**
- Ownership check: `if ad.owner != request.user: redirect()`

**Flow:**
- **POST:** Deletes ad (hard delete, not soft delete)
- **GET:** Shows confirmation page

**Template:** `ads/templates/ads/delete_ad.html`

**Note:** Uses hard delete - ad is permanently removed from database

---

#### 8. `my_ads()` - User's Ads List

**File:** `ads/views.py` (lines 458-465)

**URL:** `/ads/my-ads/`

**Purpose:** List all ads created by current user

**Decorators:**
- `@login_required`

**Flow:**
- Queries: `Ad.objects.filter(owner=request.user).order_by('-created_on')`
- Shows all ads (including unapproved, inactive)

**Template:** `ads/templates/ads/my_ads.html`

**Features:**
- Approval status badges
- Plan status badges (Free/Pro)
- Edit/Delete buttons
- Links to ad detail pages

---

#### 9. `add_ad_to_favorites()` - Toggle Favorite

**File:** `ads/views.py` (lines 468-487)

**URL:** `/ads/add-to-favorites/<ad_id>/`

**Purpose:** Add or remove ad from user's favorites (toggle)

**Decorators:**
- `@login_required`

**Flow:**
- Uses `get_or_create()` - creates if not exists, deletes if exists
- Redirects to referer (previous page)

**Note:** Toggle behavior - clicking again removes from favorites

---

#### 10. `remove_from_favorites()` - Remove Favorite

**File:** `ads/views.py` (lines 490-506)

**URL:** `/ads/remove-from-favorites/<ad_id>/`

**Purpose:** Remove ad from favorites (from favorites page)

**Decorators:**
- `@login_required`

**Flow:**
- Gets FavoriteAd instance, deletes it
- Shows success/error message
- Redirects to favorites page

---

#### 11. `delete_ad_comment()` - Delete Comment

**File:** `ads/views.py` (lines 509-533)

**URL:** `/ads/ad/<slug>/comment/<comment_id>/delete/`

**Purpose:** Soft delete ad comment (only by author)

**Decorators:**
- `@login_required`

**Security:**
- Ownership check: `if comment.author != request.user: redirect()`

**Flow:**
- **POST:** Sets `is_deleted=True` (soft delete)
- **GET:** Shows error message

**Note:** Uses soft delete - comment hidden but not removed from database

---

## Forms & Validation

### 1. AdForm

**File:** `ads/forms.py` (lines 7-224)

**Purpose:** Form for creating/editing ads

**Fields:**
- `title`, `category`, `image`, `extra_image_1`, `extra_image_2`
- `target_url`, `city`, `address`, `phone`
- `instagram_url`, `telegram_url`, `website_url`
- `start_date`, `end_date`

**Validation Methods:**

1. **`clean_image()`** (lines 119-141)
   - File size: Max 5MB
   - Image validation: Uses Pillow to verify valid image
   - Reopens file after `verify()` (required for Django)

2. **`clean_extra_image_1()`**, **`clean_extra_image_2()`** (lines 166-174)
   - Uses helper `_validate_image_file()`
   - Same validation as main image

3. **`clean_address()`**, **`clean_city()`**, **`clean_phone()`** (lines 176-195)
   - Strips whitespace
   - Basic sanitization

4. **`clean_instagram_url()`**, **`clean_telegram_url()`**, **`clean_website_url()`** (lines 197-223)
   - Validates URL starts with `http://` or `https://`
   - Strips whitespace

**Required Fields:**
- `title`, `category`, `image`, `target_url`, `city`, `address`

**Optional Fields:**
- `extra_image_1`, `extra_image_2`, `phone`, social URLs, dates

**Widgets:** Bootstrap form controls with Persian placeholders

---

### 2. AdCommentForm

**File:** `ads/forms.py` (lines 226-287)

**Purpose:** Form for commenting on ads

**Fields:**
- `body` (Textarea, maxlength=2000)
- `honeypot` (hidden field for spam protection)

**Validation:**

1. **`clean_honeypot()`** (lines 260-265)
   - Detects bot submissions
   - Raises error if field has value

2. **`clean_body()`** (lines 267-287)
   - Required field check
   - Max length: 2000 characters
   - HTML sanitization via `blog.utils.sanitize_html()`
   - Strips whitespace

**Security:**
- Honeypot field (hidden, tabindex=-1)
- HTML sanitization prevents XSS

---

### 3. AdFilterForm

**File:** `ads/forms.py` (lines 290-324)

**Purpose:** Filter form for category listing page

**Fields:**
- `city` (ChoiceField, dynamic choices)
- `sort` (ChoiceField, choices: 'newest', 'oldest')

**Dynamic City Choices:**
- Populated from available cities in current category
- Passed via `city_choices` kwarg in `__init__()`
- Format: `[('', 'همه شهرها'), ('city1', 'city1'), ...]`

**Usage:** Used in `ad_list_by_category()` view

---

### 4. ProRequestForm

**File:** `ads/forms.py` (lines 327-354)

**Purpose:** Form for requesting Pro upgrade

**Fields:**
- `phone` (CharField, max_length=30, required)

**Validation:**
- `clean_phone()` - Strips whitespace, ensures not empty

**Usage:** Used in `ad_detail()` view for Pro request modal

---

## Templates & Frontend

### Template Files

1. **`ads_home.html`** - Category listing page
2. **`ads_by_category.html`** - Ads list by category (with filters)
3. **`ad_detail.html`** - Individual ad detail page
4. **`create_ad.html`** - Create ad form
5. **`edit_ad.html`** - Edit ad form
6. **`delete_ad.html`** - Delete confirmation
7. **`my_ads.html`** - User's ads list
8. **`includes/_category_slider.html`** - Category slider component

### Key Template Features

#### Ad Cards (Category Listing)

**File:** `ads/templates/ads/ads_by_category.html`

**Structure:**
- Bootstrap grid: `col-md-3` (4 cards per row on desktop)
- Glass morphism card design
- Image wrapper with aspect ratio 1:1
- Badges: Featured, Pro/Free, Owner, Active

**Badges:**
- **Featured:** Gold badge with star icon (top-right)
- **Pro/Free:** Plan badge (top-left)
- **Owner:** "تبلیغ شما" badge (if user owns ad)
- **Active:** "فعال" badge (if approved)

**Image Display:**
- Main image: `ad.image.url` (Cloudinary)
- Fallback: `default.jpg` if image fails
- Aspect ratio: 1:1 (square)
- Object-fit: Cover

**Responsive:**
- Desktop: 4 cards per row (`col-md-3`)
- Tablet: 2 cards per row (`col-md-6`)
- Mobile: 1 card per row (`col-12`)

---

#### Ad Detail Page

**File:** `ads/templates/ads/ad_detail.html`

**Structure:**
1. **Hero Section:** Title and category
2. **Image Carousel:** Bootstrap 5 carousel (if extra images exist)
3. **Target URL Button:** (if approved)
4. **Contact Information:** City, address, phone, social links
5. **Favorite Button:** Add/remove from favorites
6. **Pro Request Section:** Button/modal (if owner, Free, not requested)
7. **Comments Section:** Comment form and list

**Image Carousel:**
- Main image always first (active)
- Extra images as additional carousel items
- Navigation controls (prev/next buttons)
- Only shows if extra images exist

**Pro Request Modal:**
- Bootstrap 5 modal
- Phone number input
- CSRF protection
- Form validation

**Comments:**
- Published immediately (no moderation)
- Soft delete support (`is_deleted` flag)
- Author can delete own comments

---

#### Create/Edit Ad Forms

**Files:** `create_ad.html`, `edit_ad.html`

**Features:**
- Bootstrap form styling
- Persian labels and placeholders
- Image preview (edit page)
- Required field indicators (*)
- Help text for each field
- Error display

**Image Upload:**
- File input with `accept="image/*"`
- Validation: 5MB max, valid image format
- Preview thumbnails on edit page

---

### CSS Styling

**File:** `static/css/style.css`

**Key Classes:**

1. **`.glass-morphism-card`** - Main ad card container
   - Glass effect with backdrop blur
   - Rounded corners
   - Shadow effects

2. **`.glass-card-image-wrapper`** - Image container
   - Aspect ratio: 1:1 (square)
   - Overflow: hidden
   - Background: #f0f0f0

3. **`.glass-card-badge`** - Badge styling
   - Position: absolute
   - Rounded corners
   - Backdrop filter blur
   - Color-coded (featured, owner, active, pro, free)

4. **`.ad-featured`** - Featured ad styling
   - Border: 2px solid #ffc107
   - Highlighted appearance

5. **`.ad-detail-image`** - Detail page image
   - Responsive width
   - Rounded corners

**Responsive Design:**
- Mobile-first approach
- Breakpoints: 768px (tablet), 992px (desktop)
- Grid system: Bootstrap 5

---

## Admin Interface

### AdAdmin

**File:** `ads/admin.py` (lines 16-159)

**List Display:**
- Title, category, owner, status flags
- Featured priority, plan, Pro request status
- URL status, social URLs status
- Dates, timestamps

**List Filters:**
- Category, owner, status flags
- Plan, Pro requested
- Dates

**List Editable:**
- `is_approved`, `is_featured`, `featured_priority`

**Search Fields:**
- Title, target_url, category name, city, address, phone

**Fieldsets:**
1. Ad Information
2. Media (images)
3. Target URL
4. Location & Contact
5. Social Media URLs
6. Visibility & Scheduling
7. Featured Ad
8. Ad Plan & Pro Request
9. Timestamps

**Custom Methods:**
- `url_status()` - Color-coded URL approval status
- `social_urls_status()` - Color-coded social URLs status
- `pro_request_status()` - Plan status with Pro request details

**Features:**
- Bulk editing via list_editable
- Color-coded status indicators
- Organized fieldsets
- Readonly fields (timestamps, pro_requested_at)

---

### AdCategoryAdmin

**File:** `ads/admin.py` (lines 6-14)

**Simple configuration:**
- List display: name, slug, ad_count, created_on
- Search: name, description
- Auto-slug generation from name

---

### AdCommentAdmin

**File:** `ads/admin.py` (lines 162-202)

**Features:**
- List display with body preview
- Filter by deletion status, date
- Search: body, author, ad title
- Soft delete support

---

### AdsViewCountAdmin

**File:** `ads/admin.py` (lines 205-234)

**Features:**
- View statistics display
- Filters out orphaned records
- Readonly fields
- Safe title display (handles deleted ads)

---

## Image Processing & Storage

### Cloudinary Integration

**Storage:** All ad images stored in Cloudinary (cloud-based CDN)

**Fields:**
- `image` (CloudinaryField, required)
- `extra_image_1` (CloudinaryField, optional)
- `extra_image_2` (CloudinaryField, optional)

**Image Validation:**
- **File Size:** Max 5MB (checked in form validation)
- **Format:** Validated using Pillow
- **Process:** `verify()` → `load()` → `seek(0)`

**Image Display:**
- URLs: `ad.image.url` (Cloudinary CDN URL)
- Responsive: `img-fluid` class
- Fallback: `default.jpg` if image fails to load
- Error handling: `onerror` attribute in templates

**Image Sizing:**
- **Category Cards:** 1:1 aspect ratio (square)
- **Detail Page:** Full width, responsive
- **Carousel:** Full width, responsive

**Performance:**
- Cloudinary CDN for fast delivery
- Lazy loading: Not implemented for ad images (could be added)
- Image optimization: Handled by Cloudinary

---

## Filtering & Pagination

### City Filtering

**Implementation:** `ads/views.py` - `ad_list_by_category()`

**Query:**
```python
if selected_city:
    all_ads = all_ads.filter(city__iexact=selected_city)
```

**Features:**
- Case-insensitive matching (`iexact`)
- Dynamic dropdown populated from category
- Filter persists in pagination links

**Database Index:**
- `Index(fields=['city'])` - Optimizes city filtering
- `Index(fields=['category', 'city'])` - Optimizes category+city queries

**Limitations:**
- No partial matching (must be exact city name)
- No city normalization (e.g., "Stockholm" vs "stockholm")
- Dropdown query runs on every page load (could be cached)

---

### Date Sorting

**Implementation:** `ads/views.py` - `ad_list_by_category()`

**Options:**
- `newest` (default) - Newest first
- `oldest` - Oldest first

**Logic:**
- Featured ads always appear first (not affected by sort)
- Only normal ads are sorted
- Sort applied in Python (not DB query)

**Code:**
```python
if sort_order == 'oldest':
    normal_ads = sorted(normal_ads, key=lambda x: x.created_on)
```

**Limitations:**
- Sort only affects normal ads (featured always first)
- Python-based sorting (could be optimized with DB ordering)

---

### Pagination

**Implementation:** Custom pagination logic

**Page 1:**
- Featured ads: Up to 39 positions
- Normal ads: Fill remaining slots
- Total: 39 ads per page

**Page 2+:**
- Only normal ads (featured excluded)
- 39 ads per page

**Pagination Variables:**
- `is_paginated` - Boolean
- `has_previous`, `has_next` - Boolean
- `current_page`, `total_pages` - Integers
- `previous_page_number`, `next_page_number` - Integers or None

**Template:**
- Custom pagination links
- Preserves filter parameters in URLs

**Limitations:**
- Complex logic (featured/normal separation)
- Python-based pagination for page 1 (could use DB)
- No page size configuration

---

## Free/Pro Plan System

### Model Fields

**File:** `ads/models.py` (lines 164-189)

**Fields:**
- `plan` - CharField, choices: ('free', 'Pro'), default='free'
- `pro_requested` - BooleanField, default=False
- `pro_request_phone` - CharField, optional
- `pro_requested_at` - DateTimeField, optional

---

### Pro Request Workflow

**File:** `ads/views.py` - `ad_detail()` (lines 294-322)

**Flow:**
1. User clicks "می‌خواهم تبلیغ من Pro شود" button
2. Modal opens with phone number form
3. User submits phone number
4. System validates:
   - Ownership check
   - Not already Pro
   - Not already requested
5. Saves: `pro_requested=True`, `pro_request_phone`, `pro_requested_at`
6. Shows confirmation message

**Admin Workflow:**
1. Admin filters ads by `pro_requested=True` and `plan='free'`
2. Reviews phone number and request date
3. Contacts user if needed
4. Manually changes `plan` from 'free' to 'pro' in admin

**No Payment Integration:**
- Manual process only
- No automatic upgrade
- Admin must manually approve

---

### Plan Display

**Templates:**
- **Category Listing:** Pro/Free badges on ad cards
- **My Ads Page:** Plan status badges
- **Ad Detail:** Pro request button/modal (if applicable)

**Badges:**
- **Pro:** Gold/yellow badge with crown icon
- **Free:** Gray badge with tag icon
- **Pro Requested:** Info alert message

---

## Static Sidebar Ads

### Overview

**Separate System:** Static image files, not database-driven

**Files:** `static/images/ad-1.jpg` to `ad-5.jpg`, `ad-top.jpg`

**Purpose:** Display promotional banners in sidebar

---

### Display Locations

1. **Homepage** (`blog/templates/blog/index.html`)
   - Desktop: Left sidebar (below popular posts)
   - Mobile: Inline between posts (every 4 posts)

2. **Post Detail Page** (`blog/templates/blog/post_detail.html`)
   - Desktop: Left sidebar (below popular posts)
   - Mobile: Same sidebar structure

---

### Implementation

**Template Structure:**
```html
<div class="ad-placeholder ad-placeholder-bottom">
  <a href="#" target="_blank" rel="noopener noreferrer" class="ad-link">
    <img src="{% static 'images/ad-1.jpg' %}" 
         alt="تبلیغات" 
         class="ad-image"
         loading="eager" />
  </a>
</div>
```

**Loading Behavior:**
- Desktop/Tablet: `loading="eager"` (load immediately)
- Mobile: `loading="lazy"` (lazy load)

**CSS:**
- Aspect ratio: 2:1 (width:height)
- Min height: 120px
- Responsive width: 100% of sidebar

**Links:**
- Currently: `href="#"` (no-op)
- Can be updated to actual URLs in templates

---

### Mobile Inline Ads

**Homepage Only:**
- Ads appear between posts
- Pattern: After every 4 posts
- Rotates: ad-1 → ad-2 → ad-3 → ad-4 → ad-5 → repeat

**Code Logic:**
```django
{% if forloop.counter|divisibleby:4 %}
  <!-- Show ad based on counter -->
{% endif %}
```

---

## Security & Permissions

### Authentication & Authorization

**Decorators Used:**
- `@login_required` - Requires authentication
- `@site_verified_required` - Requires site verification (profile completion)
- `@ratelimit` - Rate limiting (prevents spam/abuse)

**Rate Limiting:**
- **Create Ad:** 5/h per user, 10/h per IP
- **Ad Detail POST:** 20/m per IP
- **Comments:** Handled by ad_detail rate limit

---

### Ownership Checks

**Edit Ad:**
```python
if ad.owner != request.user:
    messages.error(...)
    return redirect(...)
```

**Delete Ad:**
```python
if ad.owner != request.user:
    messages.error(...)
    return redirect(...)
```

**Pro Request:**
```python
if ad.owner != request.user:
    messages.error(...)
    return redirect(...)
```

**Delete Comment:**
```python
if comment.author != request.user:
    messages.error(...)
    return redirect(...)
```

---

### Input Validation

**Forms:**
- Image file size: Max 5MB
- Image format: Pillow validation
- URL format: Must start with http:// or https://
- Text fields: Whitespace stripping
- Comment body: HTML sanitization, max 2000 chars

**Honeypot:**
- Hidden field in comment form
- Detects bot submissions

**CSRF Protection:**
- All forms include `{% csrf_token %}`
- Django middleware handles validation

---

### Data Exposure

**Public Data:**
- Ad titles, images, categories (if approved)
- City, address, phone (if provided)
- Comments (if not deleted)

**Protected Data:**
- Owner information (visible but not editable)
- Approval status (visible to owner in "My Ads")
- Pro request details (admin only)

**URL Approval:**
- Target URLs only clickable if `url_approved=True`
- Social URLs only clickable if `social_urls_approved=True`

---

## Performance Considerations

### Database Queries

**Optimizations:**
- `select_related('category', 'owner')` - Reduces JOIN queries
- Database indexes on `city`, `(category, city)`
- Aggregated view counts (AdsViewCount model)

**Potential Issues:**
- Category counting in Python loop (could use `annotate()`)
- Featured/normal separation in Python (could use DB queries)
- City dropdown query on every page load (could be cached)

---

### Image Loading

**Current:**
- Cloudinary CDN (fast delivery)
- No lazy loading for ad images (could be added)
- Eager loading for static sidebar ads (desktop)

**Recommendations:**
- Add lazy loading for ad card images
- Implement image placeholders
- Use responsive images (srcset)

---

### Caching Opportunities

**Potential Cache Targets:**
- Category ad counts
- City dropdown lists
- Featured ads list
- Category slider data

**Current:** No caching implemented

---

## Technical Strengths

### ✅ Well-Structured Code

- Clear separation of concerns (models, views, forms, templates)
- Reusable helper functions (`_visible_ads_queryset()`)
- Consistent naming conventions
- Good use of Django best practices

### ✅ Security Features

- Rate limiting on critical endpoints
- Ownership validation
- Input sanitization (HTML, URLs)
- CSRF protection
- Honeypot spam protection

### ✅ User Experience

- Responsive design (mobile, tablet, desktop)
- Clear visual indicators (badges, status)
- Intuitive navigation
- Error messages in Persian

### ✅ Admin Interface

- Well-organized fieldsets
- Color-coded status indicators
- Bulk editing capabilities
- Comprehensive filtering

### ✅ Database Design

- Proper indexes for performance
- Soft delete support (comments)
- Aggregated view counts
- Unique constraints (favorites)

---

## Technical Weaknesses & Issues

### ⚠️ Performance Issues

1. **Category Counting in Python**
   - **Location:** `ad_category_list()` view
   - **Issue:** Loops through all ads to count per category
   - **Fix:** Use `annotate(Count('ads'))` in queryset

2. **Featured/Normal Separation in Python**
   - **Location:** `ad_list_by_category()` view
   - **Issue:** Separates featured/normal ads in Python list
   - **Fix:** Use separate querysets or DB annotations

3. **City Dropdown Query on Every Load**
   - **Location:** `ad_list_by_category()` view
   - **Issue:** Queries unique cities on every page load
   - **Fix:** Cache city list or use `values_list().distinct()` more efficiently

4. **No Lazy Loading for Ad Images**
   - **Issue:** All ad images load immediately
   - **Fix:** Add `loading="lazy"` attribute to ad card images

---

### ⚠️ Missing Validations

1. **Phone Number Format**
   - **Location:** `ProRequestForm.clean_phone()`
   - **Issue:** Only checks not empty, no format validation
   - **Fix:** Add regex pattern or phone number library

2. **City Name Normalization**
   - **Issue:** "Stockholm" vs "stockholm" treated as different
   - **Fix:** Normalize city names (lowercase, strip) before saving

3. **URL Domain Validation**
   - **Issue:** No validation of URL domains (could be malicious)
   - **Fix:** Add domain whitelist/blacklist or URL reputation check

4. **Image Dimensions**
   - **Issue:** No minimum/maximum dimension validation
   - **Fix:** Add dimension checks in form validation

---

### ⚠️ Security Concerns

1. **Owner Field Nullable**
   - **Issue:** `owner` field allows `null=True, blank=True`
   - **Risk:** Ads could be created without owner
   - **Fix:** Make owner required or set default to request.user

2. **No Rate Limiting on Favorites**
   - **Issue:** Users could spam favorite/unfavorite actions
   - **Fix:** Add rate limiting to favorite endpoints

3. **Comment Spam Protection**
   - **Current:** Honeypot only
   - **Enhancement:** Could add more sophisticated spam detection

4. **Image Upload Security**
   - **Current:** File size and format validation
   - **Enhancement:** Could add virus scanning or image content validation

---

### ⚠️ Code Quality Issues

1. **Redundant Image Validation**
   - **Location:** `AdForm._validate_image_file()` and `clean_image()`
   - **Issue:** Similar validation code duplicated
   - **Fix:** Use helper method consistently

2. **Complex Pagination Logic**
   - **Location:** `ad_list_by_category()` view
   - **Issue:** Custom pagination logic is hard to maintain
   - **Fix:** Refactor into helper function or use Django Paginator more effectively

3. **Hardcoded Values**
   - **Issue:** `ads_per_page = 39` hardcoded
   - **Fix:** Move to settings or make configurable

4. **Missing Error Handling**
   - **Issue:** Some operations don't handle edge cases
   - **Example:** What if Cloudinary upload fails?
   - **Fix:** Add try-except blocks and error messages

---

### ⚠️ Edge Cases Not Handled

1. **Ad Without Owner**
   - **Issue:** `owner` is nullable, but views assume owner exists
   - **Risk:** Could cause AttributeError
   - **Fix:** Add null checks or make owner required

2. **Concurrent Pro Requests**
   - **Issue:** No locking mechanism for Pro requests
   - **Risk:** Race condition if user clicks multiple times
   - **Fix:** Add database-level locking or check before save

3. **Featured Priority Conflicts**
   - **Issue:** Multiple ads could have same priority
   - **Current:** Sorted by created_on as tiebreaker
   - **Enhancement:** Could add unique constraint or better priority system

4. **Deleted Category**
   - **Issue:** `on_delete=models.PROTECT` prevents deletion
   - **Enhancement:** Could add cascade delete or category archiving

---

### ⚠️ Missing Features

1. **Search Functionality**
   - **Current:** No search for ads
   - **Enhancement:** Add full-text search (title, description, city)

2. **Price/Price Range Filtering**
   - **Current:** No price field or filtering
   - **Enhancement:** Add price field and range filter

3. **Ad Expiration Notifications**
   - **Current:** No notification when ad expires
   - **Enhancement:** Email notification before/after expiration

4. **Bulk Operations**
   - **Current:** No bulk edit/delete for users
   - **Enhancement:** Add bulk actions in "My Ads" page

5. **Ad Analytics**
   - **Current:** Only view count
   - **Enhancement:** Click tracking, engagement metrics

---

## Recommended Improvements

### High Priority

1. **Optimize Category Counting**
   ```python
   # Current (slow):
   for ad in visible_ads:
       if ad.category_id in counts:
           counts[ad.category_id] += 1
   
   # Recommended (fast):
   categories = AdCategory.objects.annotate(
       ad_count=Count('ads', filter=Q(ads__is_active=True, ads__is_approved=True))
   )
   ```

2. **Add Lazy Loading for Ad Images**
   ```html
   <img src="{{ ad.image.url }}" 
        loading="lazy" 
        alt="{{ ad.title }}" />
   ```

3. **Cache City Dropdown**
   ```python
   from django.core.cache import cache
   
   cache_key = f'ad_cities_{category.id}'
   cities = cache.get(cache_key)
   if not cities:
       cities = list(available_cities)
       cache.set(cache_key, cities, 3600)  # 1 hour
   ```

4. **Make Owner Required**
   ```python
   owner = models.ForeignKey(
       User,
       on_delete=models.CASCADE,
       related_name="ads",
       # Remove null=True, blank=True
   )
   ```

5. **Add Phone Number Validation**
   ```python
   import re
   
   def clean_phone(self):
       phone = self.cleaned_data.get('phone')
       if phone:
           # Remove spaces, dashes, parentheses
           phone = re.sub(r'[\s\-\(\)]', '', phone)
           # Validate format (Swedish phone: +46XXXXXXXXX or 0XXXXXXXXX)
           if not re.match(r'^(\+46|0)[0-9]{9}$', phone):
               raise ValidationError('Invalid phone number format')
       return phone
   ```

---

### Medium Priority

6. **Refactor Pagination Logic**
   - Create helper function: `paginate_ads_with_featured(queryset, page, per_page)`
   - Simplify view code
   - Make pagination reusable

7. **Add Image Dimension Validation**
   ```python
   def clean_image(self):
       image = self.cleaned_data.get('image')
       if image:
           # ... existing validation ...
           img = Image.open(image)
           width, height = img.size
           if width < 200 or height < 200:
               raise ValidationError('Image must be at least 200x200 pixels')
           if width > 5000 or height > 5000:
               raise ValidationError('Image dimensions too large')
       return image
   ```

8. **Implement Search Functionality**
   ```python
   # Add to views.py
   def search_ads(request):
       query = request.GET.get('q', '')
       ads = _visible_ads_queryset().filter(
           Q(title__icontains=query) |
           Q(city__icontains=query) |
           Q(address__icontains=query)
       )
       # ... pagination ...
   ```

9. **Add Rate Limiting to Favorites**
   ```python
   @ratelimit(key='user', rate='30/m', method='POST')
   @login_required
   def add_ad_to_favorites(request, ad_id):
       # ... existing code ...
   ```

10. **Normalize City Names**
    ```python
    def clean_city(self):
        city = self.cleaned_data.get('city')
        if city:
            city = city.strip().title()  # Normalize: "stockholm" -> "Stockholm"
        return city
    ```

---

### Low Priority / Enhancements

11. **Add Price Field and Filtering**
    - Add `price` DecimalField to Ad model
    - Add price range filter to AdFilterForm
    - Update templates to show price

12. **Implement Ad Analytics**
    - Track clicks on target_url
    - Track engagement (time on page, scroll depth)
    - Add analytics dashboard in admin

13. **Add Bulk Operations**
    - Bulk edit in "My Ads" page
    - Bulk delete with confirmation
    - Bulk status change

14. **Improve SEO**
    - Add meta descriptions for ad pages
    - Add structured data (Schema.org)
    - Add canonical URLs
    - Add Open Graph tags

15. **Add Email Notifications**
    - Notify when ad is approved
    - Notify when ad expires
    - Notify when Pro request is processed

16. **Implement Ad Expiration Workflow**
    - Auto-deactivate expired ads
    - Email reminder before expiration
    - Option to extend expiration

17. **Add Ad Reporting System**
    - Allow users to report inappropriate ads
    - Admin review queue for reports
    - Auto-flagging based on keywords

18. **Improve Admin Interface**
    - Add bulk actions (approve, reject, feature)
    - Add export functionality (CSV, Excel)
    - Add analytics dashboard
    - Add Pro request queue view

19. **Add Ad Preview**
    - Preview before publishing
    - Preview in different screen sizes
    - Preview with different themes

20. **Implement Ad Scheduling**
    - Schedule ads to go live at specific time
    - Schedule ads to expire automatically
    - Recurring ad campaigns

---

## Conclusion

The Peyvand Ads system is a well-architected, feature-rich classified advertisements platform with strong security measures and good user experience. The codebase follows Django best practices and includes comprehensive functionality for ad management, moderation, and user interaction.

**Key Strengths:**
- Clean code structure
- Strong security measures
- Good user experience
- Comprehensive admin interface
- Performance optimizations (indexes, aggregated counts)

**Areas for Improvement:**
- Performance optimizations (caching, query optimization)
- Additional validations (phone, city normalization)
- Missing features (search, price filtering, analytics)
- Code refactoring (pagination logic, redundant code)

**Overall Assessment:** The system is production-ready but would benefit from the recommended improvements, particularly in performance optimization and additional features for better user experience and admin efficiency.

---

**Report Generated:** 2025-01-XX  
**Analysis Scope:** Complete Ads system (models, views, forms, templates, admin, static files)  
**Codebase Version:** Current (as of analysis date)

