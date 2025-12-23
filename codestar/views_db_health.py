import logging
from typing import List, Dict, Any, Optional, Tuple

from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


logger = logging.getLogger(__name__)


def _is_postgres_backend() -> bool:
    """Check if current DB engine is PostgreSQL."""
    engine = connection.settings_dict.get("ENGINE", "")
    return "postgresql" in engine or "postgis" in engine


def _fetch_db_size() -> Tuple[Optional[int], str]:
    """
    Return (size_bytes, human_readable).
    If backend not Postgres or query fails, returns (None, "Not available").
    Read-only; uses pg_database_size.
    """
    if not _is_postgres_backend():
        return None, "Not available for this backend"

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_database_size(current_database()), "
                "pg_size_pretty(pg_database_size(current_database()));"
            )
            size_bytes, size_pretty = cursor.fetchone()
            return int(size_bytes), str(size_pretty)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("DB health: failed to fetch database size: %s", exc, exc_info=True)
        return None, "Not available"


def _fetch_table_sizes() -> List[Dict[str, Any]]:
    """
    Return list of {'table_name', 'total_size_pretty', 'total_size_bytes'}.
    For non-Postgres backends or failures, returns empty list.
    Read-only; uses pg_total_relation_size.
    """
    if not _is_postgres_backend():
        return []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    relname AS table_name,
                    pg_total_relation_size(relid) AS total_size_bytes,
                    pg_size_pretty(pg_total_relation_size(relid)) AS total_size_pretty
                FROM pg_catalog.pg_statio_user_tables
                ORDER BY pg_total_relation_size(relid) DESC;
                """
            )
            results = cursor.fetchall()
            return [
                {
                    "table_name": row[0],
                    "total_size_bytes": int(row[1]),
                    "total_size_pretty": str(row[2]),
                }
                for row in results
            ]
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("DB health: failed to fetch table sizes: %s", exc, exc_info=True)
        return []


def _model_counts() -> List[Dict[str, Any]]:
    """
    Collect row counts for key models. Missing models are skipped gracefully.
    """
    model_specs = [
        ("Posts", "blog", "Post"),
        ("Comments", "blog", "Comment"),
        ("Favorites", "blog", "Favorite"),
        ("Likes", "blog", "Like"),
        ("PageViews", "blog", "PageView"),
        ("Ads", "ads", "Ad"),
        ("Ad Categories", "ads", "AdCategory"),
        ("Users", "auth", "User"),
        ("Sessions", "sessions", "Session"),
    ]

    counts: List[Dict[str, Any]] = []
    for label, app_label, model_name in model_specs:
        try:
            from django.apps import apps

            model = apps.get_model(app_label=app_label, model_name=model_name)
            if model is None:
                continue
            counts.append(
                {
                    "label": label,
                    "model": f"{app_label}.{model_name}",
                    "count": model.objects.count(),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.info(
                "DB health: skipping count for %s.%s (%s)", app_label, model_name, exc
            )
            continue
    return counts


def _warnings(db_size_bytes: Optional[int], table_sizes: List[Dict[str, Any]]) -> List[str]:
    """
    Generate simple informational warnings based on size thresholds.
    """
    notices: List[str] = []
    # Notional free-tier threshold 500 MB
    threshold_bytes = 500 * 1024 * 1024
    if db_size_bytes is not None and db_size_bytes > 0.7 * threshold_bytes:
        notices.append(
            "پایگاه داده به بیش از ۷۰٪ ظرفیت پیشنهادی رایگان (۵۰۰ مگابایت) رسیده است."
        )

    # Sessions table size heuristic
    session_entry = next((t for t in table_sizes if t["table_name"] == "django_session"), None)
    if session_entry and session_entry.get("total_size_bytes", 0) > 50 * 1024 * 1024:
        notices.append(
            "حجم جدول سشن‌ها زیاد است. اجرای دوره‌ای «python manage.py clearsessions» را در نظر بگیرید."
        )

    return notices


@staff_member_required
def db_health_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Read-only database health dashboard.

    Shows total DB size, per-table sizes, and key model row counts.
    No mutations or schema changes are performed.
    Access: staff/superusers only.
    """
    db_size_bytes, db_size_pretty = _fetch_db_size()
    table_sizes = _fetch_table_sizes()
    model_counts = _model_counts()
    warnings_list = _warnings(db_size_bytes, table_sizes)

    backend_engine = connection.settings_dict.get("ENGINE", "unknown")

    context = {
        "db_size_human": db_size_pretty,
        "table_sizes": table_sizes,
        "model_counts": model_counts,
        "warnings": warnings_list,
        "backend_engine": backend_engine,
        "is_postgres": _is_postgres_backend(),
    }
    return render(request, "admin/db_health.html", context)

