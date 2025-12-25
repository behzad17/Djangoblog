# Ads Favorites Feature - Technical Feasibility Report

**Date:** 2025-12-25  
**Status:** ✅ FEASIBLE

---

## 1. Current Favorites Implementation (Posts)

### Model
**File:** `blog/models.py` (lines 210-228)
```python
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
```

### View
**File:** `blog/views.py` (lines 407-426)
- `add_to_favorites(request, post_id)` - Toggles favorite status
- Uses `get_or_create()` then deletes if exists (toggle behavior)
- Redirects to `HTTP_REFERER` or 'favorites'

### URL
**File:** `blog/urls.py` (line 11)
- `path('add-to-favorites/<int:post_id>/', views.add_to_favorites, name='add_to_favorites')`

### Template Logic
**File:** `blog/templates/blog/post_detail.html` (lines 86-107)
- Checks `is_favorited` variable (set in view)
- Shows "افزودن به علاقه‌مندی‌ها" if not favorited
- Shows "افزوده شده به علاقه‌مندی‌ها" (disabled) if favorited
- Shows login link if not authenticated

### How `is_favorited` is Set
**File:** `blog/views.py` (lines 175-181)
```python
is_favorited = False
if request.user.is_authenticated:
    is_favorited = Favorite.objects.filter(
        user=request.user,
        post=post,
    ).exists()
```

---

## 2. Recommended Approach: **Option B (Separate FavoriteAd Model)**

### Why Option B?

✅ **Safety:**
- Does NOT modify existing `Favorite` model
- Zero risk of breaking Post favorites
- Clean separation of concerns

✅ **Simplicity:**
- Same pattern as existing `Favorite` model
- Easy to understand and maintain
- No ContentTypes complexity

✅ **Performance:**
- Direct ForeignKey (no GenericForeignKey overhead)
- Simple queries
- Easy to index

### Why NOT Option A (GenericForeignKey)?

❌ **Complexity:**
- Requires ContentTypes framework
- More complex queries
- Harder to understand

❌ **Risk:**
- Modifies existing Favorite model
- Potential migration issues
- Could affect existing Post favorites

---

## 3. Implementation Plan

### Step 1: Create FavoriteAd Model
**File:** `ads/models.py`
```python
class FavoriteAd(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'ad')
```

### Step 2: Create Migration
- Run `makemigrations ads`
- Run `migrate`

### Step 3: Add View
**File:** `ads/views.py`
- Add `add_ad_to_favorites(request, ad_id)` - Same toggle logic as posts
- Check if ad is favorited in `ad_detail` view

### Step 4: Add URL
**File:** `ads/urls.py`
- Add `path('add-to-favorites/<int:ad_id>/', views.add_ad_to_favorites, name='add_ad_to_favorites')`

### Step 5: Update Template
**File:** `ads/templates/ads/ad_detail.html`
- Add favorite button similar to post_detail.html
- Check `is_favorited` variable

---

## 4. Files to Create/Modify

### New Files:
- None (all changes in existing files)

### Modified Files:
1. `ads/models.py` - Add FavoriteAd model
2. `ads/views.py` - Add `add_ad_to_favorites` view, update `ad_detail` view
3. `ads/urls.py` - Add favorite URL
4. `ads/templates/ads/ad_detail.html` - Add favorite button
5. `ads/migrations/XXXX_favoritead.py` - New migration (auto-generated)

---

## 5. Implementation Details

### Model Structure:
- `FavoriteAd` mirrors `Favorite` structure
- Same `unique_together` constraint
- Same `added_on` timestamp

### View Logic:
- Same toggle pattern: `get_or_create()` then delete if exists
- Redirect to `HTTP_REFERER` (stays on ad detail page)
- Check favorite status in `ad_detail` view

### Template Button:
- Same UI pattern as post detail
- Persian text: "افزودن به علاقه‌مندی‌ها" / "حذف از علاقه‌مندی‌ها"
- Login link for non-authenticated users

---

## 6. Feasibility Confirmation

✅ **FEASIBLE** - Safe, isolated implementation

### Requirements Met:
- ✅ Does not break existing Post favorites
- ✅ Same behavior as Post favorites
- ✅ Per-user favorites
- ✅ No duplicates (unique constraint)
- ✅ Redirects back to ad detail page
- ✅ Clean, maintainable code

### Risk Level: **LOW**
- Isolated to ads app
- No changes to blog app
- Simple model addition

---

## 7. Next Steps

1. Create FavoriteAd model
2. Generate and run migration
3. Add view and URL
4. Update ad_detail template
5. Test favorite toggle functionality

