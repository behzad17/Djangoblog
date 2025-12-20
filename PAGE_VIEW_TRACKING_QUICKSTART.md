# Page View Tracking - Quick Start Guide

## ✅ Implementation Complete

The page view tracking system has been implemented in your Django blog. Here's what was added:

### Files Created/Modified:

1. **`blog/models.py`** - Added:
   - `PageView` model (tracks individual views)
   - `PostViewCount` model (cached aggregated counts)
   - `view_count()` and `unique_view_count()` methods to `Post` model

2. **`blog/utils.py`** - NEW FILE:
   - Privacy-compliant anonymization functions
   - Bot detection
   - `track_page_view()` function

3. **`blog/views.py`** - Modified:
   - Added tracking to `post_detail()` view

4. **`blog/admin.py`** - Modified:
   - Added admin interfaces for `PageView` and `PostViewCount`

5. **`PAGE_VIEW_TRACKING_IMPLEMENTATION.md`** - Complete documentation

---

## 🚀 Next Steps

### 1. Create and Run Migrations

```bash
python manage.py makemigrations blog
python manage.py migrate blog
```

### 2. Test the Implementation

1. Visit a post detail page
2. Check Django admin → Blog → Page Views
3. You should see a new `PageView` record

### 3. Display View Counts in Templates

Add to your post detail template:

```django
{# blog/templates/blog/post_detail.html #}

<div class="post-stats">
    <span class="views">
        <i class="fas fa-eye"></i>
        {{ post.view_count }} views
    </span>
</div>
```

### 4. (Optional) Add View Counts to Post List

```django
{# blog/templates/blog/index.html #}

{% for post in post_list %}
    <div class="post-card">
        <!-- existing content -->
        <div class="post-meta">
            <span>{{ post.view_count }} views</span>
        </div>
    </div>
{% endfor %}
```

---

## 🔒 Privacy Features

- ✅ IP addresses are hashed (SHA256) - not stored in plain text
- ✅ User agents are hashed
- ✅ No cookies required (uses Django sessions)
- ✅ Bot filtering enabled
- ✅ Rate limiting (1 view per post per session/IP per hour)

---

## 📊 How It Works

1. **User visits a post** → `post_detail()` view is called
2. **Tracking function** → `track_page_view()` is called
3. **Bot check** → Skips if request is from a bot
4. **Deduplication** → Checks if view already recorded in last hour
5. **Record creation** → Creates `PageView` record with anonymized data
6. **Cache update** → Updates `PostViewCount` for fast retrieval

---

## 🛠️ Admin Interface

Access via Django Admin:
- **Blog → Page Views** - See all individual views
- **Blog → Post View Counts** - See aggregated counts per post

---

## 📈 Performance

- Uses database indexes for fast queries
- Cached counts in `PostViewCount` model
- Consider async updates for high-traffic sites (see full docs)

---

## 🧹 Maintenance

### Cleanup Old Views (Optional)

Create a management command to delete old views:

```bash
python manage.py shell
```

```python
from django.utils import timezone
from datetime import timedelta
from blog.models import PageView

# Delete views older than 1 year
cutoff = timezone.now() - timedelta(days=365)
PageView.objects.filter(viewed_at__lt=cutoff).delete()
```

Or set up a cron job to run this periodically.

---

## 📝 Notes

- **Rate Limiting**: Currently set to 1 view per post per session/IP per hour
- **Bot Filtering**: Automatically filters common bots/crawlers
- **Privacy**: All IPs and user agents are hashed
- **Performance**: View counts are cached in `PostViewCount` model

---

## 🔍 Troubleshooting

**Views not being tracked?**
- Check that migrations are applied
- Verify `track_page_view()` is being called
- Check Django admin for `PageView` records
- Check browser console for errors

**Too many duplicate views?**
- Adjust rate limit window in `blog/utils.py` (currently 1 hour)
- Check bot filtering is working

**Performance issues?**
- Consider async cache updates (see full docs)
- Add database indexes if needed
- Consider pagination for admin views

---

## 📚 Full Documentation

See `PAGE_VIEW_TRACKING_IMPLEMENTATION.md` for:
- Complete implementation details
- Alternative approaches (middleware, client-side)
- Advanced features
- Testing examples
- GDPR compliance details

---

## ✨ Features

✅ Server-side tracking (works without JavaScript)  
✅ Privacy-compliant (hashed IPs/user agents)  
✅ Bot filtering  
✅ Rate limiting (prevents duplicate counting)  
✅ Cached counts (fast performance)  
✅ Admin interface  
✅ GDPR ready  

Enjoy tracking your page views! 🎉

