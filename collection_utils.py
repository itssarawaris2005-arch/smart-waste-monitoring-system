"""Shared helpers for interpreting Firebase bin/task records.

Mirrors the flexible field-name matching used by admin_dashboard_kivy.py
so the staff dashboard and the admin dashboard agree on what counts as
"collected" and how collected weight is computed.
"""

from datetime import datetime


def records(data):
    if data is None:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        result = []
        for key, value in data.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("_id", key)
                result.append(item)
        return result
    return []


def is_collected(record):
    for key in (
        "collected",
        "is_collected",
        "collection_completed",
        "is_completed",
        "completed",
    ):
        if key in record:
            value = record.get(key)
            if value is True:
                return True
            if str(value).strip().lower() in (
                "true", "1", "yes", "collected", "completed", "complete",
            ):
                return True

    for key in ("collection_status", "task_status", "status", "state"):
        if key not in record:
            continue
        text = str(record.get(key) or "").strip().lower()
        if text in (
            "collected", "completed", "complete", "done",
            "picked", "picked up", "true", "finished", "closed",
        ):
            return True

    for key in (
        "collected_at", "collectedAt",
        "collection_datetime", "collectionDateTime",
        "collection_date", "collectionDate",
        "completed_at", "completedAt",
        "picked_up_at", "pickedUpAt",
    ):
        if record.get(key) not in (None, "", False):
            return True

    return False


def record_datetime(record):
    candidates = (
        "collected_at", "collectedAt",
        "collection_datetime", "collectionDateTime",
        "datetime", "created_at", "createdAt", "timestamp", "date",
        "task_date", "taskDate", "collection_date", "collectionDate",
        "updated_at", "updatedAt",
    )

    for key in candidates:
        value = record.get(key)

        if value is None:
            continue

        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(float(value))
            except Exception:
                pass

        text = str(value).strip()

        if not text:
            continue

        try:
            return datetime.fromisoformat(
                text.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except Exception:
            pass

    return None


def is_today(record):
    dt = record_datetime(record)
    return dt is not None and dt.date() == datetime.now().date()


def is_bin_full(record):
    if record.get("bin_full") is True:
        return True
    status = str(record.get("status") or "").strip().lower()
    return status in ("full", "filled", "100", "100%", "full bin")


def is_bin_empty(record):
    if record.get("bin_full") is False:
        return True
    status = str(record.get("status") or "").strip().lower()
    return status in ("empty", "empty bin", "0", "0%")


def collection_tons(record):
    for key in (
        "weight_ton", "weight_tons", "weightTon", "weightTons", "tons",
        "collection_ton", "collectionTon", "collected_ton", "collectedTon",
    ):
        if key in record:
            try:
                return float(record[key])
            except Exception:
                pass

    for key in (
        "weight_kg", "weightKg", "kg", "weight",
        "collection_weight", "collectionWeight",
    ):
        if key in record:
            try:
                return float(record[key]) / 1000.0
            except Exception:
                pass

    return 0.0
