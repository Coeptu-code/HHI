from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.customers.models import CustomerActivity


logger = logging.getLogger(__name__)


def _safe_create_activity(**kwargs: Any) -> CustomerActivity | None:
    try:
        return CustomerActivity.objects.create(**kwargs)
    except Exception:
        logger.exception("Failed to create customer activity", extra={"activity_type": kwargs.get("activity_type")})
        return None


def record_customer_activity(
    *,
    customer_id: int | None,
    activity_type: str,
    title: str,
    description: str | None = None,
    intake_session_id: int | None = None,
    actor_type: str | None = None,
    actor_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_window_seconds: int | None = None,
) -> CustomerActivity | None:
    if not customer_id:
        return None

    if dedupe_window_seconds:
        threshold = timezone.now() - timedelta(seconds=dedupe_window_seconds)
        exists = CustomerActivity.objects.filter(
            customer_id=customer_id,
            intake_session_id=intake_session_id,
            activity_type=activity_type,
            title=title,
            created_at__gte=threshold,
        ).exists()
        if exists:
            return None

    return _safe_create_activity(
        customer_id=customer_id,
        intake_session_id=intake_session_id,
        activity_type=activity_type,
        title=title,
        description=description or "",
        actor_type=actor_type or "",
        actor_name=actor_name or "",
        metadata=metadata or {},
    )


def list_customer_activity(*, customer_id: int, limit: int = 25, offset: int = 0, activity_type: str | None = None) -> dict[str, Any]:
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    queryset = CustomerActivity.objects.filter(customer_id=customer_id)
    if activity_type:
        queryset = queryset.filter(activity_type=activity_type)
    queryset = queryset.order_by("-created_at")
    total = queryset.count()
    items = list(queryset[offset : offset + limit])
    return {
        "items": [
            {
                "id": item.id,
                "activity_type": item.activity_type,
                "title": item.title,
                "description": item.description or None,
                "actor_type": item.actor_type or None,
                "actor_name": item.actor_name or None,
                "created_at": item.created_at.isoformat(),
                "metadata": item.metadata or {},
            }
            for item in items
        ],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


def record_intake_event(
    *,
    customer_id: int | None,
    activity_type: str,
    title: str,
    intake_session_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> CustomerActivity | None:
    return record_customer_activity(
        customer_id=customer_id,
        activity_type=activity_type,
        title=title,
        intake_session_id=intake_session_id,
        actor_type="system",
        actor_name="Avery",
        metadata=metadata,
    )


def record_analysis_event(
    *,
    customer_id: int | None,
    intake_session_id: int | None,
    activity_type: str,
    title: str,
    metadata: dict[str, Any] | None = None,
) -> CustomerActivity | None:
    return record_customer_activity(
        customer_id=customer_id,
        intake_session_id=intake_session_id,
        activity_type=activity_type,
        title=title,
        actor_type="system",
        actor_name="Avery",
        metadata=metadata,
    )


def record_admin_event(
    *,
    customer_id: int | None,
    intake_session_id: int | None,
    activity_type: str,
    title: str,
    actor_name: str | None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_window_seconds: int | None = None,
) -> CustomerActivity | None:
    return record_customer_activity(
        customer_id=customer_id,
        intake_session_id=intake_session_id,
        activity_type=activity_type,
        title=title,
        description=description,
        actor_type="agent",
        actor_name=actor_name,
        metadata=metadata,
        dedupe_window_seconds=dedupe_window_seconds,
    )
