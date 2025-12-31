# Comment Moderation & Trust-Based Approval System
## Technical Assessment & Implementation Plan

**Project:** Peyvand / Djangoblog PP4  
**Date:** 2025-01-27  
**Feature:** Trust-based comment moderation with link detection  
**Status:** Analysis & Planning (No Code Changes)

---

## Executive Summary

**Current State:**
- Comments are auto-approved (`approved=True` by default)
- All comments appear immediately without review
- No trust system or moderation workflow
- Basic Django admin registration (no custom configuration)

**Proposed System:**
- First 5 comments require manual approval per user
- After 5 approved comments, user becomes "trusted"
- Trusted users' comments auto-approve (unless link detected)
- Any comment with a link requires moderation
- Enhanced admin interface with filters and indicators

**Complexity:** Medium  
**Impact:** High (Security & Quality)  
**Risk:** Low (Backward compatible)

---

## 1. Current System Analysis

### 1.1 Comment Model Structure

**Location:** `blog/models.py:186-208`

```python
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commenter")
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=True)  # ⚠️ Auto-approved
```

**Key Observations:**
- ✅ `approved` field exists (no model changes needed)
- ⚠️ Default is `True` (must change to `False`)
- ❌ No fields for tracking trust status or moderation reason
- ❌ No link detection flag

### 1.2 Comment Creation Flow

**Location:** `blog/views.py:222-227`

**Current Flow:**
1. User submits comment via `CommentForm`
2. Form validates
3. Comment saved with `approved=True` (default)
4. Comment appears immediately on post page
5. No approval logic or checks

**Code:**
```python
comment_form = CommentForm(data=request.POST)
if comment_form.is_valid():
    comment = comment_form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()  # approved=True by default
```

**Issues:**
- No approval logic in view
- No trust check
- No link detection
- No notification to admin

### 1.3 Comment Display Logic

**Location:** `blog/views.py:173`

**Current Behavior:**
```python
comments = post.comments.all().order_by("-created_on")
```

**Template:** `blog/templates/blog/post_detail.html:288`
- Loops through all comments
- No filtering by `approved` status in template
- ⚠️ **Potential Issue:** Unapproved comments might be visible

**Comment Count Logic:**
- Multiple places use: `Count('comments', filter=Q(comments__approved=True))`
- Only approved comments counted
- But template shows all comments

**Recommendation:** Filter comments in view before passing to template.

### 1.4 Admin Interface

**Location:** `blog/admin.py:114`

**Current State:**
```python
admin.site.register(Comment)  # Default registration only
```

**Issues:**
- ❌ No custom admin configuration
- ❌ No filters for pending comments
- ❌ No list display customization
- ❌ No indicators for moderation reason
- ❌ No bulk actions

### 1.5 Comment Form

**Location:** `blog/forms.py:138-157`

**Current State:**
- Basic ModelForm
- Honeypot field for spam protection
- No approval logic in form
- No link detection

---

## 2. Recommended Model Changes

### 2.1 Option A: Minimal Changes (Recommended)

**Add fields to Comment model:**

```python
class Comment(models.Model):
    # ... existing fields ...
    approved = models.BooleanField(default=False)  # ⚠️ CHANGE DEFAULT
    
    # New fields (optional, for tracking)
    moderation_reason = models.CharField(
        max_length=50,
        choices=[
            ('new_user', 'New user (first 5 comments)'),
            ('contains_link', 'Contains link'),
            ('manual_review', 'Manual review'),
        ],
        blank=True,
        null=True,
        help_text="Reason why comment requires moderation"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_comments',
        help_text="Admin who reviewed this comment"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this comment was reviewed"
    )
```

**Migration Required:**
- Change default of `approved` from `True` to `False`
- Add new fields (nullable, safe migration)
- Update existing comments: Set `approved=True` for all existing comments (data migration)

**Pros:**
- Minimal changes
- Backward compatible (existing comments remain approved)
- Tracks moderation reason
- Audit trail (reviewed_by, reviewed_at)

**Cons:**
- Adds 3 new fields
- Requires data migration for existing comments

### 2.2 Option B: UserProfile Extension (Alternative)

**Add to UserProfile model:**

```python
class UserProfile(models.Model):
    # ... existing fields ...
    approved_comment_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of approved comments (for trust calculation)"
    )
    is_trusted_commenter = models.BooleanField(
        default=False,
        help_text="User has 5+ approved comments"
    )
```

**Pros:**
- Centralized trust tracking
- Easy to query trusted users
- Can be used for other features

**Cons:**
- Requires maintaining count (signal or method)
- More complex than Option A

**Recommendation:** Use **Option A** (minimal) for initial implementation. Option B can be added later if needed.

---

## 3. Approval Logic Flow

### 3.1 Trust Calculation

**Method 1: Query-based (Recommended)**
```python
def is_trusted_commenter(user):
    """Check if user has 5+ approved comments."""
    approved_count = Comment.objects.filter(
        author=user,
        approved=True
    ).count()
    return approved_count >= 5
```

**Pros:**
- No model changes needed
- Always accurate (no sync issues)
- Simple to implement

**Cons:**
- Query on every comment creation (minimal performance impact)

**Method 2: Cached in UserProfile (Alternative)**
- Store count in UserProfile
- Update via signal when comment approved/rejected
- Faster but requires maintenance

**Recommendation:** Use **Method 1** (query-based) for simplicity.

### 3.2 Link Detection

**Regex Pattern:**
```python
import re

LINK_PATTERNS = [
    r'https?://\S+',  # http:// or https://
    r'www\.\S+',      # www.example.com
    r'\S+\.(com|org|net|io|se|ir)\S*',  # domain extensions
]

def contains_link(text):
    """Check if text contains any URL pattern."""
    text_lower = text.lower()
    for pattern in LINK_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False
```

**Considerations:**
- Case-insensitive matching
- Handle Persian/Arabic text (URLs are usually Latin)
- False positives possible (e.g., "example.com" in sentence)
- Can be refined based on testing

**Alternative:** Use more sophisticated URL detection library (e.g., `urlextract`), but regex is simpler and sufficient.

### 3.3 Approval Logic Flow

**Location:** `blog/views.py:post_detail()` - Comment creation section

**Proposed Flow:**

```python
# In post_detail view, when comment is created:

comment = comment_form.save(commit=False)
comment.author = request.user
comment.post = post

# Step 1: Check if user is trusted
is_trusted = is_trusted_commenter(request.user)

# Step 2: Check for links
has_link = contains_link(comment.body)

# Step 3: Determine approval status
if has_link:
    # STRICT RULE: Links always require moderation
    comment.approved = False
    comment.moderation_reason = 'contains_link'
elif not is_trusted:
    # New user: First 5 comments require approval
    comment.approved = False
    comment.moderation_reason = 'new_user'
else:
    # Trusted user, no link: Auto-approve
    comment.approved = True
    comment.moderation_reason = None

comment.save()
```

**Decision Tree:**
```
Comment Created
    │
    ├─ Contains Link? ──YES──> approved=False, reason='contains_link'
    │
    └─NO
        │
        ├─ User has 5+ approved comments? ──NO──> approved=False, reason='new_user'
        │
        └─YES──> approved=True (auto-approve)
```

### 3.4 User Feedback

**Current:** Generic success message  
**Proposed:** Context-aware messages

```python
if comment.approved:
    messages.success(request, 'نظر شما با موفقیت ثبت شد!')
else:
    if comment.moderation_reason == 'contains_link':
        messages.info(request, 
            'نظر شما ثبت شد و در انتظار بررسی است. '
            'نظرات حاوی لینک نیاز به تایید مدیر دارند.'
        )
    else:
        messages.info(request,
            'نظر شما ثبت شد و در انتظار بررسی است. '
            'پس از تایید ۵ نظر، نظرات بعدی شما به صورت خودکار تایید می‌شوند.'
        )
```

### 3.5 Comment Display Updates

**Current Issue:** Template shows all comments  
**Fix Required:** Filter in view

**Location:** `blog/views.py:173`

**Change:**
```python
# Current:
comments = post.comments.all().order_by("-created_on")

# Proposed:
if request.user.is_authenticated:
    # Show approved comments + user's own unapproved comments
    comments = post.comments.filter(
        Q(approved=True) | Q(author=request.user)
    ).order_by("-created_on")
else:
    # Show only approved comments
    comments = post.comments.filter(approved=True).order_by("-created_on")
```

**Template Update:** No changes needed (already loops through comments)

---

## 4. Admin UI Improvements

### 4.1 Custom Admin Configuration

**Location:** `blog/admin.py`

**Proposed Configuration:**

```python
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for comment moderation."""
    
    list_display = (
        'id',
        'body_preview',
        'author',
        'post',
        'approval_status',
        'moderation_reason_display',
        'created_on',
        'reviewed_info'
    )
    
    list_filter = (
        'approved',
        'moderation_reason',
        'created_on',
        'reviewed_at',
    )
    
    search_fields = ('body', 'author__username', 'post__title')
    
    list_editable = ('approved',)  # Quick approve/reject
    
    readonly_fields = ('created_on', 'reviewed_by', 'reviewed_at')
    
    actions = ['approve_comments', 'reject_comments']
    
    fieldsets = (
        ('Comment Content', {
            'fields': ('body', 'post', 'author')
        }),
        ('Moderation', {
            'fields': (
                'approved',
                'moderation_reason',
                'reviewed_by',
                'reviewed_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_on',),
            'classes': ('collapse',)
        }),
    )
    
    def body_preview(self, obj):
        """Show first 50 characters of comment."""
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body
    body_preview.short_description = 'Comment'
    
    def approval_status(self, obj):
        """Color-coded approval status."""
        if obj.approved:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Approved</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">⏳ Pending</span>'
        )
    approval_status.short_description = 'Status'
    
    def moderation_reason_display(self, obj):
        """Display moderation reason with icon."""
        if not obj.moderation_reason:
            return '-'
        reasons = {
            'new_user': '👤 New User',
            'contains_link': '🔗 Contains Link',
            'manual_review': '📋 Manual Review',
        }
        return reasons.get(obj.moderation_reason, obj.moderation_reason)
    moderation_reason_display.short_description = 'Reason'
    
    def reviewed_info(self, obj):
        """Show who reviewed and when."""
        if obj.reviewed_by and obj.reviewed_at:
            return f"{obj.reviewed_by.username} ({obj.reviewed_at.strftime('%Y-%m-%d %H:%M')})"
        return '-'
    reviewed_info.short_description = 'Reviewed By'
    
    def approve_comments(self, request, queryset):
        """Bulk approve action."""
        updated = queryset.update(
            approved=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} comment(s) approved.")
    approve_comments.short_description = 'Approve selected comments'
    
    def reject_comments(self, request, queryset):
        """Bulk reject action."""
        updated = queryset.update(
            approved=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} comment(s) rejected.")
    reject_comments.short_description = 'Reject selected comments'
    
    def save_model(self, request, obj, form, change):
        """Track who reviewed the comment."""
        if change and 'approved' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
```

### 4.2 Admin Filters

**Proposed Filters:**
1. **Approval Status:** Approved / Pending
2. **Moderation Reason:** New User / Contains Link / Manual Review
3. **Created Date:** Today / This Week / This Month
4. **Reviewed Status:** Reviewed / Unreviewed
5. **Post:** Filter by post (useful for reviewing comments on specific posts)

### 4.3 Admin Dashboard Counter

**Location:** Custom admin dashboard or admin index override

**Proposed Counter:**
```python
def get_admin_stats():
    return {
        'pending_comments': Comment.objects.filter(approved=False).count(),
        'pending_new_user': Comment.objects.filter(
            approved=False,
            moderation_reason='new_user'
        ).count(),
        'pending_links': Comment.objects.filter(
            approved=False,
            moderation_reason='contains_link'
        ).count(),
    }
```

**Display:** Widget on admin home page showing pending comment counts by reason.

---

## 5. Implementation Considerations

### 5.1 Backward Compatibility

**Existing Comments:**
- All existing comments have `approved=True`
- Migration should preserve this
- No breaking changes for existing functionality

**Data Migration Strategy:**
```python
# In migration file:
def migrate_existing_comments(apps, schema_editor):
    Comment = apps.get_model('blog', 'Comment')
    # Keep all existing comments approved
    Comment.objects.all().update(approved=True)
```

### 5.2 Performance Considerations

**Trust Calculation:**
- Query runs on every comment creation
- Impact: Minimal (indexed query on `author` + `approved`)
- Optimization: Can cache in UserProfile if needed later

**Link Detection:**
- Regex matching on comment body
- Impact: Negligible (text processing)
- No database queries needed

**Comment Display:**
- Filtering in view (not template)
- Uses database query (efficient)
- Index recommended on `approved` field

### 5.3 Security Considerations

**Link Detection:**
- Prevents spam/scam links
- Protects users from malicious URLs
- Admin can review before approval

**Trust System:**
- Prevents spam from new accounts
- Builds community trust gradually
- 5-comment threshold is reasonable (can be adjusted)

**Admin Actions:**
- Bulk approve/reject actions
- Audit trail (reviewed_by, reviewed_at)
- Prevents accidental mass approval

### 5.4 User Experience

**Positive:**
- Trusted users have seamless experience
- Clear messaging about moderation
- Users understand why comment is pending

**Potential Issues:**
- New users might be discouraged by moderation
- **Mitigation:** Clear messaging + quick admin review

**Edge Cases:**
- User edits comment (should re-check for links)
- User deletes comment (trust count unaffected)
- Admin rejects comment (trust count unaffected - only approved count)

### 5.5 Edge Cases & Special Scenarios

#### **Scenario 1: User Edits Comment**
**Current:** `comment_edit()` view doesn't check approval  
**Proposed:** Re-check approval logic on edit if comment was previously approved

```python
def comment_edit(request, slug, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == "POST":
        # ... existing edit logic ...
        # Re-check approval if comment was approved
        if comment.approved:
            has_link = contains_link(comment.body)
            if has_link:
                comment.approved = False
                comment.moderation_reason = 'contains_link'
                comment.reviewed_by = None  # Reset review
                comment.reviewed_at = None
        comment.save()
```

#### **Scenario 2: Admin Rejects Comment**
**Behavior:** Comment remains in user's count (only approved comments count)
- User still needs 5 approved comments
- Rejected comments don't count toward trust

#### **Scenario 3: User Deletes Comment**
**Behavior:** Deleted comment removed from count
- Trust calculation uses only existing approved comments
- No special handling needed

#### **Scenario 4: Comment Contains Multiple Links**
**Behavior:** Single flag (`contains_link`) - no need to count links

#### **Scenario 5: Link in Already-Approved Comment**
**Current:** Comment stays approved  
**Proposed:** On edit, re-check and unapprove if link added

---

## 6. Database Schema Changes

### 6.1 Required Migrations

**Migration 1: Change Default + Add Fields**
```python
# 1. Change approved default from True to False
# 2. Add moderation_reason field (CharField, nullable)
# 3. Add reviewed_by field (ForeignKey, nullable)
# 4. Add reviewed_at field (DateTimeField, nullable)
```

**Migration 2: Data Migration**
```python
# Set all existing comments to approved=True
# (preserve current state)
```

**Migration 3: Indexes (Optional but Recommended)**
```python
# Add index on approved field for faster filtering
# Add index on moderation_reason for faster filtering
```

### 6.2 Index Recommendations

```python
class Comment(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['approved', 'created_on']),
            models.Index(fields=['author', 'approved']),  # For trust calculation
            models.Index(fields=['moderation_reason', 'approved']),
        ]
```

---

## 7. Testing Considerations

### 7.1 Test Cases Required

**Trust System:**
1. New user's 1st comment → `approved=False`, `reason='new_user'`
2. New user's 5th comment → `approved=False`, `reason='new_user'`
3. New user's 6th comment (no link) → `approved=True`
4. Trusted user's comment (no link) → `approved=True`
5. Trusted user's comment (with link) → `approved=False`, `reason='contains_link'`

**Link Detection:**
1. Comment with `http://example.com` → detected
2. Comment with `https://example.com` → detected
3. Comment with `www.example.com` → detected
4. Comment with `example.com` → detected (if pattern matches)
5. Comment with "example.com" in sentence → detected (potential false positive)
6. Comment with no link → not detected

**Admin Interface:**
1. Filter by `approved=False` shows pending comments
2. Filter by `moderation_reason` works correctly
3. Bulk approve action updates `reviewed_by` and `reviewed_at`
4. List display shows correct status indicators

**Display Logic:**
1. Unapproved comments not visible to other users
2. Unapproved comments visible to comment author
3. Approved comments visible to all users
4. Comment count only includes approved comments

---

## 8. Implementation Phases

### Phase 1: Core Functionality (Week 1)
1. ✅ Update Comment model (add fields, change default)
2. ✅ Create migrations
3. ✅ Implement trust calculation function
4. ✅ Implement link detection function
5. ✅ Update comment creation logic
6. ✅ Update comment display logic (filtering)

### Phase 2: Admin Interface (Week 1-2)
1. ✅ Create custom CommentAdmin
2. ✅ Add filters and list display
3. ✅ Add bulk actions
4. ✅ Add review tracking
5. ✅ Test admin workflow

### Phase 3: User Experience (Week 2)
1. ✅ Update user messages (context-aware)
2. ✅ Test user feedback
3. ✅ Verify comment display behavior

### Phase 4: Testing & Refinement (Week 2)
1. ✅ Write tests
2. ✅ Test edge cases
3. ✅ Refine link detection patterns
4. ✅ Performance testing

---

## 9. Risk Assessment

### 9.1 Low Risks ✅
- **Model changes:** Additive (new fields nullable)
- **Backward compatibility:** Existing comments preserved
- **Performance:** Minimal impact (indexed queries)

### 9.2 Medium Risks ⚠️
- **Link detection false positives:** May flag non-URLs
  - **Mitigation:** Refine regex patterns based on testing
- **User confusion:** New users might not understand moderation
  - **Mitigation:** Clear messaging in UI

### 9.3 High Risks 🔴
- **None identified** - Implementation is low-risk

---

## 10. Alternative Approaches Considered

### 10.1 Option: Always Moderate Links (Current Choice) ✅
**Pros:** Simple, strict security  
**Cons:** Trusted users inconvenienced  
**Decision:** Chosen for security

### 10.2 Option: Allow Links After N Approved Comments
**Pros:** Better UX for trusted users  
**Cons:** More complex logic  
**Decision:** Rejected (security priority)

### 10.3 Option: AI/ML Spam Detection
**Pros:** Automated filtering  
**Cons:** High complexity, false positives  
**Decision:** Future enhancement (non-goal)

### 10.4 Option: Community Reporting
**Pros:** User involvement  
**Cons:** Not in requirements  
**Decision:** Future enhancement (non-goal)

---

## 11. Summary & Recommendations

### 11.1 Recommended Approach

**Model Changes:**
- ✅ Change `approved` default to `False`
- ✅ Add `moderation_reason` field (CharField, choices)
- ✅ Add `reviewed_by` and `reviewed_at` fields (audit trail)

**Logic Implementation:**
- ✅ Trust calculation: Query-based (5+ approved comments)
- ✅ Link detection: Regex patterns (http/https/www/domains)
- ✅ Approval flow: Link check → Trust check → Auto-approve if both pass

**Admin Interface:**
- ✅ Custom CommentAdmin with filters, indicators, bulk actions
- ✅ Dashboard counter for pending comments
- ✅ Review tracking (who/when)

**User Experience:**
- ✅ Context-aware messages
- ✅ Filter comments in view (not template)
- ✅ Show unapproved comments to author only

### 11.2 Implementation Complexity

**Estimated Effort:**
- Model changes: 2-3 hours
- Logic implementation: 4-6 hours
- Admin interface: 4-6 hours
- Testing: 3-4 hours
- **Total: 13-19 hours** (2-3 days)

### 11.3 Key Decisions

1. **Trust Calculation:** Query-based (no model changes needed)
2. **Link Detection:** Regex (simple, effective)
3. **Model Fields:** Minimal additions (3 fields)
4. **Admin UI:** Full customization (filters, actions, indicators)
5. **Backward Compatibility:** Preserve existing approved comments

### 11.4 Next Steps

1. **Review this assessment** with stakeholders
2. **Confirm requirements** (5-comment threshold, link rules)
3. **Approve approach** before implementation
4. **Create implementation plan** with detailed tasks
5. **Begin Phase 1** (model changes + migrations)

---

## 12. Questions for Clarification

1. **Trust Threshold:** Confirm 5 approved comments is the target?
2. **Link Patterns:** Should we detect partial URLs (e.g., "example.com" without http)?
3. **Existing Comments:** Should all existing comments remain approved?
4. **Admin Notifications:** Should we add email notifications for pending comments? (Separate feature)
5. **Comment Editing:** Should edited comments be re-checked for links even if previously approved?

---

**End of Technical Assessment**

