# Ads Pro Request Feature (Method 1) - Technical Feasibility Report

**Date:** 2025-01-XX  
**Status:** 📋 Analysis Only (No Implementation)

---

## Executive Summary

Implementing a Free/Pro ad system with Pro request functionality (Method 1) is **highly feasible** with low to medium complexity. The existing architecture supports this feature well, and implementation can be done incrementally without breaking existing functionality.

**Recommended Approach:** Store Pro request fields directly on Ad model  
**Estimated Complexity:** Low to Medium  
**Backwards Compatibility:** 100% (all new fields optional with defaults)

---

## 1. Feature Overview

### 1.1 Desired Behavior

**User Flow:**
1. User creates ad → Ad is **Free** by default
2. User views their ad in ads list → Sees simple card (Free ad)
3. User views ad detail page → Sees button: "I want my ad to be Pro"
4. User clicks button → Small form appears (phone number input)
5. User submits form → System stores Pro request (no payment, no auto-upgrade)
6. Confirmation message shown: "درخواست شما ثبت شد، به زودی با شما تماس می‌گیریم."
7. Admin reviews request in Django Admin → Manually switches ad from Free to Pro

**Key Requirements:**
- No online payment integration (manual process)
- Pro request stored on Ad model (not separate model)
- Only ad owner can request Pro upgrade
- Admin manually approves/upgrades ads

---

## 2. Current Ads System Analysis

### 2.1 Ad Model (`ads/models.py`)

**Current Structure:**
- **Model:** `Ad` (lines 32-211)
- **Key Fields:**
  - `owner` - ForeignKey to User (nullable, blank=True)
  - `is_active` - Boolean (default=True)
  - `is_approved` - Boolean (default=False)
  - `is_featured` - Boolean (default=False)
  - `phone` - CharField (max_length=50, blank=True)
  - `created_on` - DateTimeField (auto_now_add)
  - `updated_on` - DateTimeField (auto_now)

**Current Methods:**
- `save()` - Auto-generates slug
- `is_currently_visible()` - Checks visibility flags
- `is_currently_featured()` - Checks featured status

**Model Meta:**
- Ordering: `["-created_on"]`
- Indexes: `['city']`, `['category', 'city']`

### 2.2 Views (`ads/views.py`)

**Relevant Views:**

1. **`ad_detail(request, slug)`** (lines 237-319)
   - Decorators: `@ratelimit`, `@login_required`
   - Handles: GET (display) and POST (comment submission)
   - Current POST handling: Comment form only
   - Permission: Public view (anyone can see approved ads)
   - Owner check: Not currently enforced for viewing

2. **`create_ad(request)`** (lines 322-357)
   - Decorators: `@ratelimit`, `@site_verified_required`, `@login_required`
   - Sets: `ad.owner = request.user`
   - Sets: `ad.is_approved = False` (requires admin approval)

3. **`edit_ad(request, slug)`** (lines 360-393)
   - Decorators: `@site_verified_required`, `@login_required`
   - Ownership check: `if ad.owner != request.user: redirect()`
   - Pattern: Permission check before processing

4. **`my_ads(request)`** (lines 417-424)
   - Decorators: `@login_required`
   - Shows: All ads owned by current user

### 2.3 Templates

**Ad Detail Page (`ads/templates/ads/ad_detail.html`):**
- Lines 1-380: Full ad display
- Lines 164-176: Target URL button (if approved)
- Lines 178-258: Contact/Location information
- Lines 260-284: Favorite button section
- Lines 288-323: Comment form section
- **Location for Pro button:** After favorite button, before comment form (around line 285)

**Ads List Page (`ads/templates/ads/ads_by_category.html`):**
- Lines 84-193: Grid of ad cards
- Lines 112-119: Badge showing "تبلیغ شما" if user owns ad
- **No changes needed** - Free/Pro distinction can be visual (badge or styling)

**My Ads Page (`ads/templates/ads/my_ads.html`):**
- Lines 14-83: Grid of user's ads
- Lines 42-61: Approval status badges
- **Location for plan badge:** Add alongside approval status (line 42-61)

### 2.4 Admin Interface (`ads/admin.py`)

**Current Configuration:**
- **AdAdmin** (lines 16-133)
- **list_display:** title, category, owner, is_active, is_approved, is_featured, etc.
- **list_filter:** category, owner, is_active, is_approved, is_featured, etc.
- **list_editable:** is_approved, is_featured, featured_priority
- **fieldsets:** Organized into sections (Ad Information, Media, Target URL, etc.)
- **Custom methods:** `url_status()`, `social_urls_status()`

**Admin Features:**
- Approval workflow already exists
- Status indicators (green/orange)
- Filtering and search capabilities

### 2.5 Forms (`ads/forms.py`)

**Current Forms:**
- **AdForm** (lines 7-243): For creating/editing ads
- **AdCommentForm** (lines 180-241): For comments
- **AdFilterForm** (lines 245-275): For filtering ads

**Form Patterns:**
- Uses Django ModelForm
- Custom validation methods (`clean_*`)
- Widget customization
- Help texts and labels in Persian

---

## 3. Required Model Changes

### 3.1 New Fields to Add

**Location:** `ads/models.py` - Add after line 162 (after `featured_until` field)

**Fields:**
```python
# Ad Plan (Free/Pro)
plan = models.CharField(
    max_length=10,
    choices=[('free', 'Free'), ('pro', 'Pro')],
    default='free',
    help_text="Ad plan type: Free or Pro",
)

# Pro Request Fields
pro_requested = models.BooleanField(
    default=False,
    help_text="Whether the user has requested Pro upgrade",
)

pro_request_phone = models.CharField(
    max_length=30,
    null=True,
    blank=True,
    help_text="Phone number provided when requesting Pro upgrade",
)

pro_requested_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text="When the Pro upgrade was requested",
)
```

### 3.2 Migration Impact

**Migration Type:** Add fields (non-destructive)

**Impact on Existing Data:**
- ✅ **No data loss** - All fields are optional with defaults
- ✅ **Existing ads:** Will have `plan='free'`, `pro_requested=False`, `pro_request_phone=None`, `pro_requested_at=None`
- ✅ **No breaking changes** - All existing queries continue to work
- ✅ **Safe to apply** - Can be applied during business hours

**Migration File:**
- Will be auto-generated: `ads/migrations/0014_ad_plan_and_pro_request.py`
- Operations: 4 `AddField` operations

### 3.3 Model Methods (Optional)

**Helper Method (Optional):**
```python
def can_request_pro(self, user):
    """Check if user can request Pro upgrade for this ad."""
    if not user.is_authenticated:
        return False
    if self.owner != user:
        return False
    if self.plan == 'pro':
        return False  # Already Pro
    if self.pro_requested:
        return False  # Already requested
    return True
```

**Note:** This can be added later if needed, not required for v1.

---

## 4. Required View Changes

### 4.1 Ad Detail View (`ads/views.py`)

**Current Function:** `ad_detail(request, slug)` (lines 237-319)

**Required Changes:**

1. **Handle Pro Request POST:**
   - Add logic to detect Pro request submission (separate from comment form)
   - Check ownership: `if ad.owner != request.user: return error`
   - Validate phone number
   - Save Pro request fields
   - Show success message

2. **Modify POST Handling:**
   - Current: Only handles comment form
   - New: Check if `request.POST.get('pro_request')` exists
   - If Pro request: Process it, else process comment form

3. **Add Pro Request Form:**
   - Create `ProRequestForm` in `ads/forms.py`
   - Pass to template context

**Code Location:** Lines 279-311 (POST handling section)

**Implementation Pattern:**
```python
# In ad_detail view, after line 278
pro_request_form = ProRequestForm()

if request.method == "POST":
    # Check if this is a Pro request or comment
    if 'pro_request' in request.POST:
        # Handle Pro request
        if not request.user.is_authenticated:
            messages.error(request, 'لطفاً برای درخواست Pro وارد شوید.')
            return redirect('account_login')
        
        # Check ownership
        if ad.owner != request.user:
            messages.error(request, 'شما اجازه درخواست Pro برای این تبلیغ را ندارید.')
            return redirect('ads:ad_detail', slug=slug)
        
        # Check if already Pro or already requested
        if ad.plan == 'pro':
            messages.info(request, 'این تبلیغ قبلاً Pro است.')
            return redirect('ads:ad_detail', slug=slug)
        
        if ad.pro_requested:
            messages.info(request, 'درخواست Pro شما قبلاً ثبت شده است.')
            return redirect('ads:ad_detail', slug=slug)
        
        # Process Pro request form
        pro_request_form = ProRequestForm(data=request.POST)
        if pro_request_form.is_valid():
            ad.pro_requested = True
            ad.pro_request_phone = pro_request_form.cleaned_data['phone']
            ad.pro_requested_at = timezone.now()
            ad.save()
            messages.success(request, 'درخواست شما ثبت شد، به زودی با شما تماس می‌گیریم.')
            return redirect('ads:ad_detail', slug=slug)
    else:
        # Handle comment form (existing logic)
        # ... existing comment handling code ...
```

4. **Update Context:**
   - Add `pro_request_form` to context (line 312-318)
   - Add `can_request_pro` boolean to context

### 4.2 Create Ad View (`ads/views.py`)

**Current Function:** `create_ad(request)` (lines 322-357)

**Required Changes:**
- ✅ **None** - New ads are Free by default (handled by model default)

### 4.3 My Ads View (`ads/views.py`)

**Current Function:** `my_ads(request)` (lines 417-424)

**Required Changes:**
- ✅ **None** - Template will show plan status (no view changes needed)

### 4.4 New View (Optional)

**Pro Request View (Alternative Approach):**
- Could create separate view: `request_pro_upgrade(request, slug)`
- URL: `/ads/ad/<slug>/request-pro/`
- **Recommendation:** Handle in `ad_detail` view (simpler, no new URL needed)

---

## 5. Required Template Changes

### 5.1 Ad Detail Template (`ads/templates/ads/ad_detail.html`)

**Location for Pro Request Button:**
- **After Favorite Button** (after line 284)
- **Before Comment Form** (before line 288)

**Required Changes:**

1. **Add Pro Request Button (for Free ads owned by user):**
```html
<!-- Pro Request Section -->
{% if user.is_authenticated and ad.owner == user and ad.plan == 'free' and not ad.pro_requested %}
  <div class="mt-4 d-flex align-items-center justify-content-center">
    <button 
      type="button" 
      class="btn btn-warning btn-lg" 
      data-bs-toggle="modal" 
      data-bs-target="#proRequestModal"
    >
      <i class="fas fa-crown ms-2"></i>می‌خواهم تبلیغ من Pro شود
    </button>
  </div>
{% elif user.is_authenticated and ad.owner == user and ad.pro_requested %}
  <div class="mt-4">
    <div class="alert alert-info text-center">
      <i class="fas fa-clock ms-2"></i>
      درخواست Pro شما ثبت شده است. به زودی با شما تماس می‌گیریم.
    </div>
  </div>
{% elif user.is_authenticated and ad.owner == user and ad.plan == 'pro' %}
  <div class="mt-4">
    <div class="alert alert-success text-center">
      <i class="fas fa-crown ms-2"></i>
      این تبلیغ شما Pro است.
    </div>
  </div>
{% endif %}
```

2. **Add Bootstrap Modal for Pro Request Form:**
```html
<!-- Pro Request Modal -->
{% if user.is_authenticated and ad.owner == user and ad.plan == 'free' and not ad.pro_requested %}
<div class="modal fade" id="proRequestModal" tabindex="-1" aria-labelledby="proRequestModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="proRequestModalLabel">
          <i class="fas fa-crown ms-2"></i>درخواست ارتقا به Pro
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <form method="post" action="{% url 'ads:ad_detail' ad.slug %}">
        {% csrf_token %}
        <input type="hidden" name="pro_request" value="1">
        <div class="modal-body">
          <p class="mb-3">لطفاً شماره تماس خود را وارد کنید تا با شما تماس بگیریم:</p>
          {{ pro_request_form.phone }}
          {% if pro_request_form.phone.errors %}
            <div class="text-danger small mt-1">{{ pro_request_form.phone.errors }}</div>
          {% endif %}
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">انصراف</button>
          <button type="submit" class="btn btn-warning">
            <i class="fas fa-paper-plane ms-2"></i>ارسال درخواست
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
{% endif %}
```

**Note:** Bootstrap 5.0.1 is already included in the project, so modal will work.

### 5.2 Ads List Template (`ads/templates/ads/ads_by_category.html`)

**Required Changes:**
- ✅ **Minimal** - Optional: Add visual indicator for Pro ads (badge or styling)
- **Location:** Lines 107-119 (badge section)
- **Optional Enhancement:** Add "Pro" badge if `ad.plan == 'pro'`

### 5.3 My Ads Template (`ads/templates/ads/my_ads.html`)

**Required Changes:**
- **Add Plan Badge:** Show Free/Pro status alongside approval status
- **Location:** Lines 42-61 (approval status section)

**Implementation:**
```html
<!-- Plan Status Badge -->
<div class="mb-2">
  {% if ad.plan == 'pro' %}
  <span class="badge bg-warning text-dark">
    <i class="fas fa-crown ms-1"></i>Pro
  </span>
  {% else %}
  <span class="badge bg-secondary">
    <i class="fas fa-tag ms-1"></i>Free
  </span>
  {% endif %}
  {% if ad.pro_requested %}
  <span class="badge bg-info">
    <i class="fas fa-clock ms-1"></i>درخواست Pro ثبت شده
  </span>
  {% endif %}
</div>
```

---

## 6. Required Form Changes

### 6.1 New Form: ProRequestForm (`ads/forms.py`)

**Location:** After `AdFilterForm` (after line 275)

**Implementation:**
```python
class ProRequestForm(forms.Form):
    """
    Form for requesting Pro upgrade for an ad.
    Only requires phone number.
    """
    phone = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'شماره تماس',
            'type': 'tel',
        }),
        label='شماره تماس',
        help_text='شماره تماس خود را وارد کنید',
    )
    
    def clean_phone(self):
        """Validate and sanitize phone number."""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip()
            # Basic validation - ensure it's not empty after strip
            if not phone:
                raise ValidationError('شماره تماس نمی‌تواند خالی باشد.')
            # Optional: Add format validation (e.g., digits, length)
            # For now, keep it simple
        return phone
```

**Validation:**
- Required field
- Strip whitespace
- Basic format check (optional, can be enhanced later)

---

## 7. Required Admin Changes

### 7.1 AdAdmin Updates (`ads/admin.py`)

**Required Changes:**

1. **Add to list_display:**
   - Add `'plan'` and `'pro_request_status'` (custom method)

2. **Add to list_filter:**
   - Add `'plan'` and `'pro_requested'`

3. **Add to list_editable:**
   - Add `'plan'` (so admin can quickly change Free ↔ Pro)

4. **Add to fieldsets:**
   - New fieldset: "Ad Plan & Pro Request" (after "Featured Ad" fieldset)
   - Fields: `plan`, `pro_requested`, `pro_request_phone`, `pro_requested_at`

5. **Add Custom Method:**
```python
def pro_request_status(self, obj):
    """Display Pro request status."""
    if obj.plan == 'pro':
        return format_html('<span style="color: green;">✓ Pro</span>')
    if obj.pro_requested:
        return format_html(
            '<span style="color: orange;">⏳ Pro Requested</span><br>'
            '<small>Phone: {}</small><br>'
            '<small>Date: {}</small>',
            obj.pro_request_phone or 'N/A',
            obj.pro_requested_at.strftime('%Y-%m-%d %H:%M') if obj.pro_requested_at else 'N/A'
        )
    return format_html('<span style="color: gray;">Free</span>')

pro_request_status.short_description = "Plan Status"
```

**Code Location:**
- `list_display`: Line 20-33
- `list_filter`: Line 34-44
- `list_editable`: Line 45
- `fieldsets`: Line 50-111
- Custom methods: After line 132

---

## 8. Edge Cases & Security Considerations

### 8.1 Edge Cases

**Case 1: Anonymous Users**
- ✅ **Handled:** Button only shows if `user.is_authenticated and ad.owner == user`
- ✅ **Security:** View requires login for POST requests (`@login_required`)

**Case 2: Non-Owner Trying to Request Pro**
- ✅ **Handled:** Ownership check in view: `if ad.owner != request.user: return error`
- ✅ **Security:** Same pattern as `edit_ad` view

**Case 3: Multiple Requests for Same Ad**
- ✅ **Handled:** Check `if ad.pro_requested: return info message`
- ✅ **Prevention:** Button hidden if `pro_requested == True`

**Case 4: Already Pro Ad**
- ✅ **Handled:** Check `if ad.plan == 'pro': return info message`
- ✅ **Prevention:** Button hidden if `plan == 'pro'`

**Case 5: Ad Without Owner**
- ⚠️ **Consideration:** `owner` field is nullable (`null=True, blank=True`)
- ✅ **Handled:** Button check includes `ad.owner == user`, so no button if owner is None

**Case 6: Concurrent Requests**
- ⚠️ **Consideration:** Two requests at same time
- ✅ **Mitigation:** Check `pro_requested` before saving (atomic operation)

### 8.2 Security Considerations

**1. CSRF Protection:**
- ✅ **Handled:** Django forms include `{% csrf_token %}`
- ✅ **Automatic:** Django middleware handles CSRF validation

**2. Ownership Verification:**
- ✅ **Required:** Check `ad.owner == request.user` in view
- ✅ **Pattern:** Same as `edit_ad` view (proven pattern)

**3. Rate Limiting:**
- ✅ **Recommended:** Add rate limiting to Pro request
- ✅ **Implementation:** Use `@ratelimit` decorator (already used in project)
- **Suggestion:** `@ratelimit(key='user', rate='3/h', method='POST')`

**4. Phone Number Validation:**
- ✅ **Basic:** Strip whitespace, check not empty
- ⚠️ **Optional Enhancement:** Format validation (digits, length, country code)
- **Recommendation:** Start simple, enhance later if needed

**5. Input Sanitization:**
- ✅ **Handled:** Django form validation
- ✅ **Phone Field:** CharField (no HTML, safe from XSS)

**6. Authorization:**
- ✅ **View Level:** `@login_required` decorator
- ✅ **Object Level:** Ownership check in view logic
- ✅ **Template Level:** Conditional rendering based on ownership

**7. Data Integrity:**
- ✅ **Model Level:** Defaults ensure consistency
- ✅ **Validation:** Form validation before saving
- ⚠️ **Consideration:** Prevent setting `pro_requested=True` if `plan='pro'` (can add model validation)

---

## 9. Complexity & Risk Assessment

### 9.1 Complexity: **LOW to MEDIUM** ✅

**Justification:**

**Low Complexity Areas:**
- ✅ Model changes: Simple field additions (4 fields)
- ✅ Migration: Non-destructive, safe
- ✅ Form creation: Simple form with one field
- ✅ Template changes: Add button and modal (Bootstrap already included)
- ✅ Admin changes: Standard Django admin configuration

**Medium Complexity Areas:**
- ⚠️ View logic: Need to handle two POST types (comment vs Pro request)
- ⚠️ Edge case handling: Multiple checks (ownership, plan status, request status)
- ⚠️ User experience: Modal form, confirmation messages

**Overall:** Most components are straightforward. The main complexity is in the view logic to handle multiple POST scenarios cleanly.

### 9.2 Risk Assessment: **LOW** ✅

**Justification:**

**Low Risk Areas:**
- ✅ **Backwards Compatibility:** 100% - All new fields optional with defaults
- ✅ **Data Safety:** No data loss, no breaking changes
- ✅ **Existing Functionality:** No impact on current ad features
- ✅ **Security:** Uses proven patterns (ownership checks, CSRF, rate limiting)

**Potential Risks:**
- ⚠️ **View POST Handling:** Need to distinguish between comment and Pro request (low risk, simple check)
- ⚠️ **Concurrent Requests:** Race condition if two requests at same time (low risk, mitigated by check)
- ⚠️ **Phone Validation:** Basic validation may allow invalid formats (low risk, can enhance later)

**Mitigation:**
- Use atomic database operations
- Clear error messages for users
- Admin can manually correct any issues

---

## 10. Implementation Plan

### Phase 1: Model & Migration

1. Add 4 fields to `Ad` model (`ads/models.py`)
2. Create migration: `python manage.py makemigrations ads`
3. Test migration locally (if possible)
4. Review migration file

### Phase 2: Forms

1. Create `ProRequestForm` in `ads/forms.py`
2. Add phone validation logic

### Phase 3: Views

1. Update `ad_detail` view to handle Pro request POST
2. Add ownership and status checks
3. Add rate limiting decorator
4. Update context to include `pro_request_form` and `can_request_pro`

### Phase 4: Templates

1. Add Pro request button to `ad_detail.html`
2. Add Bootstrap modal for Pro request form
3. Add plan status badges to `my_ads.html`
4. (Optional) Add Pro badge to `ads_by_category.html`

### Phase 5: Admin

1. Update `AdAdmin.list_display`
2. Update `AdAdmin.list_filter`
3. Update `AdAdmin.list_editable`
4. Add new fieldset for plan/Pro request
5. Add `pro_request_status()` custom method

### Phase 6: Testing

1. Test Pro request flow (authenticated owner)
2. Test edge cases (non-owner, already Pro, already requested)
3. Test admin interface (filtering, editing plan)
4. Test backwards compatibility (existing ads)
5. Test mobile responsiveness

### Phase 7: Deployment

1. Commit changes
2. Run migration on production: `heroku run python manage.py migrate ads`
3. Verify functionality

---

## 11. Files to Modify

### Core Files

1. **`ads/models.py`**
   - Add 4 fields to `Ad` model
   - **Lines:** After line 162 (after `featured_until`)

2. **`ads/forms.py`**
   - Create `ProRequestForm` class
   - **Location:** After `AdFilterForm` (after line 275)

3. **`ads/views.py`**
   - Modify `ad_detail()` function
   - **Lines:** 237-319 (entire function, especially POST handling)

4. **`ads/templates/ads/ad_detail.html`**
   - Add Pro request button
   - Add Bootstrap modal
   - **Location:** After line 284 (after favorite button)

5. **`ads/templates/ads/my_ads.html`**
   - Add plan status badges
   - **Location:** Lines 42-61 (approval status section)

6. **`ads/admin.py`**
   - Update `AdAdmin` class
   - **Lines:** Multiple sections (list_display, list_filter, fieldsets, custom methods)

### Optional Files

7. **`ads/templates/ads/ads_by_category.html`**
   - (Optional) Add Pro badge to ad cards
   - **Location:** Lines 107-119 (badge section)

### Migration File (auto-generated)

8. **`ads/migrations/0014_ad_plan_and_pro_request.py`**
   - Auto-generated by Django
   - **New file:** Created by `makemigrations` command

---

## 12. Technical Details

### 12.1 Database Schema Changes

**New Columns:**
- `plan` - VARCHAR(10), default='free', NOT NULL
- `pro_requested` - BOOLEAN, default=False, NOT NULL
- `pro_request_phone` - VARCHAR(30), NULL
- `pro_requested_at` - TIMESTAMP, NULL

**Indexes:**
- ⚠️ **Consideration:** May want index on `plan` for filtering
- ⚠️ **Consideration:** May want index on `pro_requested` for admin filtering
- **Recommendation:** Add indexes if admin filtering is slow (can add later)

### 12.2 URL Patterns

**No New URLs Required:**
- Pro request handled via POST to existing `ad_detail` URL
- URL: `/ads/ad/<slug>/` (existing)
- Method: POST with `pro_request=1` parameter

**Alternative (if separate view preferred):**
- URL: `/ads/ad/<slug>/request-pro/`
- View: `request_pro_upgrade(request, slug)`
- **Recommendation:** Use existing URL (simpler)

### 12.3 Form Submission Flow

**Current Flow (Comments):**
```
POST /ads/ad/<slug>/
  → ad_detail view
  → Check POST data
  → Process AdCommentForm
  → Save comment
  → Redirect with message
```

**New Flow (Pro Request):**
```
POST /ads/ad/<slug>/ (with pro_request=1)
  → ad_detail view
  → Check if 'pro_request' in POST
  → Check ownership
  → Check plan status
  → Process ProRequestForm
  → Update ad fields
  → Redirect with message
```

**Combined Flow:**
```
POST /ads/ad/<slug>/
  → ad_detail view
  → if 'pro_request' in POST:
       → Handle Pro request
  → else:
       → Handle comment (existing)
```

### 12.4 State Management

**Ad States:**
1. **Free (default):** `plan='free'`, `pro_requested=False`
2. **Free + Requested:** `plan='free'`, `pro_requested=True`, `pro_request_phone` set, `pro_requested_at` set
3. **Pro:** `plan='pro'` (admin manually set)

**State Transitions:**
- Free → Free + Requested: User submits Pro request
- Free + Requested → Pro: Admin manually changes `plan` to 'pro'
- Pro: Final state (no further transitions)

---

## 13. User Experience Considerations

### 13.1 Button Visibility

**Show "Request Pro" Button When:**
- ✅ User is authenticated
- ✅ User is ad owner
- ✅ Ad plan is 'free'
- ✅ Pro not already requested

**Show "Request Pending" Message When:**
- ✅ User is authenticated
- ✅ User is ad owner
- ✅ `pro_requested=True`

**Show "Pro" Badge When:**
- ✅ Ad plan is 'pro'

### 13.2 Confirmation Messages

**Success Message:**
- Persian: "درخواست شما ثبت شد، به زودی با شما تماس می‌گیریم."
- English equivalent: "Your request has been registered, we will contact you soon."

**Error Messages:**
- Not owner: "شما اجازه درخواست Pro برای این تبلیغ را ندارید."
- Already Pro: "این تبلیغ قبلاً Pro است."
- Already requested: "درخواست Pro شما قبلاً ثبت شده است."
- Invalid phone: Form validation errors

### 13.3 Mobile Responsiveness

**Modal Form:**
- ✅ Bootstrap modal is responsive by default
- ✅ Works on mobile devices
- ✅ Touch-friendly buttons

**Button:**
- ✅ Bootstrap button classes are responsive
- ✅ Appropriate size for mobile

---

## 14. Admin Workflow

### 14.1 Admin Tasks

**Reviewing Pro Requests:**
1. Go to Django Admin → Ads
2. Filter by `pro_requested=True` and `plan='free'`
3. See list of ads with Pro requests
4. View phone number and request date
5. Contact user if needed
6. Change `plan` from 'free' to 'pro'
7. (Optional) Clear `pro_requested` flag after upgrade

**Admin Actions (Optional Enhancement):**
- Custom admin action: "Upgrade to Pro" (bulk action)
- Custom admin action: "Mark Pro request as reviewed"

### 14.2 Admin Filters

**Recommended Filters:**
- `plan` - Filter by Free/Pro
- `pro_requested` - Filter by request status
- Combined: `plan='free'` AND `pro_requested=True` (pending requests)

---

## 15. Future Enhancements (Out of Scope for v1)

**Potential Future Features:**
- Email notification to admin when Pro request is submitted
- Email confirmation to user when request is received
- Pro plan features (e.g., highlighted display, priority placement)
- Pro plan pricing display (even without payment)
- Pro request history/audit log
- Bulk Pro upgrade admin action
- Pro request expiration (auto-clear after X days if not upgraded)

---

## 16. Testing Checklist

### 16.1 Functional Tests

- [ ] User creates ad → Ad is Free by default
- [ ] Owner views ad detail → Sees "Request Pro" button
- [ ] Owner clicks button → Modal appears
- [ ] Owner submits form with phone → Request saved, message shown
- [ ] Owner views ad again → Sees "Request pending" message
- [ ] Non-owner views ad → No button visible
- [ ] Anonymous user views ad → No button visible
- [ ] Owner tries to request again → Error message shown
- [ ] Admin changes plan to Pro → Ad shows as Pro
- [ ] Pro ad owner views ad → Sees "Pro" badge
- [ ] My Ads page → Shows plan status badges

### 16.2 Security Tests

- [ ] Non-owner tries to POST Pro request → Rejected
- [ ] Anonymous user tries to POST → Redirected to login
- [ ] CSRF token validation → Works correctly
- [ ] Rate limiting → Prevents spam requests
- [ ] Phone validation → Rejects empty/invalid input

### 16.3 Edge Case Tests

- [ ] Ad without owner → No button shown
- [ ] Already Pro ad → No button shown
- [ ] Already requested ad → No button shown
- [ ] Concurrent requests → Handled correctly
- [ ] Invalid phone format → Validation error shown

### 16.4 Admin Tests

- [ ] Admin can filter by plan
- [ ] Admin can filter by pro_requested
- [ ] Admin can edit plan field
- [ ] Admin can see Pro request details
- [ ] Admin can change Free → Pro
- [ ] Admin can change Pro → Free

---

## 17. Conclusion

### Feasibility: ✅ **HIGHLY FEASIBLE**

**Summary:**
- Implementation is straightforward and low-risk
- All changes follow existing patterns in the codebase
- 100% backwards compatible
- No breaking changes
- Uses proven security patterns

**Estimated Effort:**
- **Development Time:** 4-6 hours
- **Testing Time:** 2-3 hours
- **Total:** 6-9 hours

**Complexity:** Low to Medium  
**Risk:** Low

**Recommendation:** ✅ **Proceed with implementation**

The Free/Pro ad system with Pro request functionality can be implemented safely with minimal risk to existing functionality. The approach of storing Pro request fields directly on the Ad model is clean, simple, and maintainable.

---

## 18. Next Steps (When Ready to Implement)

1. Review and approve this feasibility report
2. Create implementation task list
3. Begin Phase 1 (Model & Migration)
4. Test each phase before proceeding
5. Deploy to production after thorough testing

---

**Report Prepared By:** AI Assistant  
**Date:** 2025-01-XX  
**Status:** Ready for Review

