# Google OAuth Setup Guide

## Fixing "redirect_uri_mismatch" Error

If you see the error **"Error 400: redirect_uri_mismatch"** when trying to sign in with Google, it means the redirect URI in your Google Cloud Console doesn't match what Django is sending.

## Quick Fix

### Step 1: Check Your Current Setup

Run the management command to see what redirect URIs you need:

```bash
python manage.py check_oauth_setup
```

This will show you:
- Current Site domain configuration
- Required redirect URIs
- Environment variable status
- Instructions for fixing

### Step 2: Fix Site Domain (if needed)

If the Site domain is incorrect, automatically fix it:

```bash
python manage.py check_oauth_setup --fix-site-domain
```

### Step 3: Add Redirect URIs to Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: **APIs & Services** > **Credentials**
3. Click on your **OAuth 2.0 Client ID**
4. Under **"Authorized redirect URIs"**, click **"ADD URI"**
5. Add ALL of these URIs (one by one):

**Production:**
```
https://peyvand.se/accounts/google/login/callback/
https://www.peyvand.se/accounts/google/login/callback/
https://djangoblog17-173e7e5e5186.herokuapp.com/accounts/google/login/callback/
```

**Development (for local testing):**
```
http://localhost:8000/accounts/google/login/callback/
http://127.0.0.1:8000/accounts/google/login/callback/
```

6. Click **"SAVE"**

## Important Notes

- ✅ URIs must match **EXACTLY** (including trailing slash `/`)
- ✅ Use `https://` for production domains
- ✅ Use `http://` for localhost
- ❌ No wildcards allowed
- ❌ Case-sensitive

## How Django-allauth Generates Redirect URIs

Django-allauth automatically creates redirect URIs using this format:
```
{PROTOCOL}://{SITE_DOMAIN}/accounts/google/login/callback/
```

The `SITE_DOMAIN` comes from your Django Sites framework (Site ID 1).

To check/update the Site domain:
- Django Admin: `/admin/sites/site/`
- Or use: `python manage.py check_oauth_setup --fix-site-domain`

## Environment Variables

Make sure these are set in your environment (Heroku Config Vars or `.env` file):

```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

## Troubleshooting

### Error persists after adding URIs?
1. Wait a few minutes for Google's changes to propagate
2. Clear your browser cache
3. Try in an incognito/private window
4. Verify the exact URI matches (check trailing slash)

### Still having issues?
Run the diagnostic command:
```bash
python manage.py check_oauth_setup
```

This will show you exactly what needs to be configured.

