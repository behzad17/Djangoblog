# Peyvand Notification Scheduler (Heroku)

Production uses **Heroku Scheduler** add-on (one-off dynos). There is no Celery worker in this project.

## Prerequisites

1. Deploy the app with the `notifications` migration applied:
   ```bash
   python manage.py migrate notifications
   ```
2. Backfill preferences for existing users (run once after the first notifications deploy):
   ```bash
   python manage.py backfill_notification_preferences
   ```
   Dry run: `python manage.py backfill_notification_preferences --dry-run`
3. Ensure production email env vars are set (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`).
4. Install [Heroku Scheduler](https://devcenter.heroku.com/articles/scheduler) on the `djangoblog17` app.

## Jobs

### 1. Ad expiration warnings (daily)

Warns ad owners **7 days before** `end_date`.

| Field | Value |
|---|---|
| **Command** | `python manage.py send_expiring_ad_notifications` |
| **Frequency** | Daily |
| **Suggested time** | `06:00 UTC` (morning Europe/Stockholm off-peak) |
| **Dyno** | Standard-1X (or current web dyno size) |

Dry run (manual):

```bash
heroku run python manage.py send_expiring_ad_notifications --dry-run -a djangoblog17
```

Live:

```bash
heroku run python manage.py send_expiring_ad_notifications -a djangoblog17
```

**Deduplication:** Each ad/user receives at most one `ad_expiring` notification per 7-day window (`metadata.dedup_key = ad:{id}:expiring:7`).

### 2. Weekly digest (weekly)

Email-only digest for users with `weekly_digest=True` (default on).

| Field | Value |
|---|---|
| **Command** | `python manage.py send_weekly_digest` |
| **Frequency** | Weekly |
| **Suggested time** | Friday `07:00 UTC` |
| **Dyno** | Standard-1X |

Dry run:

```bash
heroku run python manage.py send_weekly_digest --dry-run -a djangoblog17
```

Single-user test:

```bash
heroku run python manage.py send_weekly_digest --user-id=123 -a djangoblog17
```

**Preferences:** Users with `weekly_digest=False` are skipped. No in-app `Notification` rows are created.

**Pro ads stat:** Counts ads with `plan='pro'` whose `updated_on` falls in the digest window. There is no dedicated `pro_upgraded_at` field yet (see Known limitations).

## Scheduler dashboard setup

1. Open Heroku Dashboard → `djangoblog17` → **Scheduler**.
2. Add job: `python manage.py send_expiring_ad_notifications` — Daily.
3. Add job: `python manage.py send_weekly_digest` — Weekly (Friday).
4. After deploy, run each command once with `--dry-run` to verify output.

## Monitoring

- Check Heroku Scheduler run logs for `[LIVE]` summary lines.
- Django admin → **Notifications** → filter `notification_type = ad_expiring` for expiration sends.
- Weekly digest leaves no notification rows; monitor email provider / `EMAIL_BACKEND` logs instead.

## Notes

- Scheduler runs commands in a **one-off dyno**; SMTP latency is acceptable for current scale.
- Expiration command only targets ads with `is_approved=True`, `is_active=True`, and an `owner`.
- Digest stats cover the **7 calendar days ending today** (local timezone).

## Known limitations

### Weekly digest — “new Pro ads”

The digest **new Pro ads** count uses `Ad.updated_on`, not a dedicated upgrade timestamp. Any save to a Pro ad (title edit, image change, admin tweak) can count toward this stat. The model has `pro_requested_at` (when the user requested Pro) but no `pro_upgraded_at` (when admin approved the upgrade).

### Phase 2 backlog

- Add `pro_upgraded_at` on `Ad`, set when `plan` changes from `free` to `pro` (admin action or automated flow).
- Switch weekly digest `new_pro_ads` query to `pro_upgraded_at` in range.
- Comment notifications (`comment_notifications` preference) — UI and dispatchers.
