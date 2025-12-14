# Expert User Access Feature - Setup & Verification Guide

## Quick Verification Steps

### 1. Restart Your Django Server

**Important:** The server must be restarted to load the new code!

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python3 manage.py runserver
```

### 2. Check Admin Interface

1. Go to: `http://localhost:8000/admin/` (or your server URL)
2. Login as admin
3. Look for **"User Profiles"** in the admin sidebar
4. You should see a list of all users with their expert status

### 3. Grant Expert Access to a User

1. In Django Admin → **User Profiles**
2. Click on a user profile
3. Check the box: **"Can publish without approval"**
4. Click **Save**
5. The user now has expert access!

### 4. Test Expert Post Creation

1. Login as the expert user
2. Go to **Create Post**
3. Create a new post
4. The post should be **published immediately** (status=1)
5. You should see: "Post Published Successfully!" message

### 5. Check Expert Content Sidebar

1. Go to homepage or any post detail page
2. Look at the right sidebar
3. You should see **"Expert Content"** (not "Popular Posts")
4. It should show posts from expert users only

## Troubleshooting

### If User Profiles don't appear in Admin:

1. **Check migrations:**
   ```bash
   python3 manage.py showmigrations blog
   ```
   Should show `[X] 0019_userprofile` and `[X] 0020_create_user_profiles`

2. **Verify admin registration:**
   ```bash
   python3 manage.py shell
   >>> from blog.models import UserProfile
   >>> from django.contrib import admin
   >>> UserProfile in admin.site._registry
   True
   ```

3. **Restart server** - This is critical!

### If Expert Content sidebar is empty:

1. **Check if you have expert users:**
   ```bash
   python3 manage.py shell
   >>> from django.contrib.auth.models import User
   >>> User.objects.filter(profile__can_publish_without_approval=True).count()
   ```

2. **Check if expert users have published posts:**
   ```bash
   >>> from blog.models import Post
   >>> expert_users = User.objects.filter(profile__can_publish_without_approval=True)
   >>> Post.objects.filter(status=1, author__in=expert_users).count()
   ```

3. **Grant expert access to a user** (see step 3 above)
4. **Create a post as that expert user**

### If changes don't appear in frontend:

1. **Hard refresh browser:** Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. **Clear browser cache**
3. **Check browser console** for JavaScript errors
4. **Verify templates are updated:**
   - Check `blog/templates/blog/index.html` line 232-233
   - Should show: `<i class="fas fa-star me-2"></i>Expert Content`

## Verification Checklist

- [ ] Server restarted
- [ ] User Profiles visible in admin
- [ ] Can grant expert access to users
- [ ] Expert user can create posts (auto-published)
- [ ] Expert Content sidebar shows on homepage
- [ ] Expert Content sidebar shows on post detail page
- [ ] Sidebar shows posts from expert users only
- [ ] Regular users still create drafts

## Expected Behavior

### Expert Users:
- ✅ Posts auto-publish (status=1)
- ✅ See "Post Published Successfully!" message
- ✅ Posts appear in main feed immediately
- ✅ Posts appear in Expert Content sidebar

### Regular Users:
- ✅ Posts saved as draft (status=0)
- ✅ See "Post Created Successfully! Pending for review" message
- ✅ Posts require admin approval
- ✅ Posts do NOT appear in Expert Content sidebar

## Admin Interface Location

**Django Admin → User Profiles**

You should see:
- List of all users
- Expert status column (✓ Expert or Regular User)
- Expert since date
- Published posts count

Click on any user to:
- Grant expert access (check "Can publish without approval")
- Revoke expert access (uncheck the box)
- View expert_since timestamp

