from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from ..models import Client


def _today() -> date:
    return timezone.localdate()


def _birthday_in_year(born: date, year: int) -> date:
    """
    Compute birthday date for a given year, safely handling Feb 29.
    """

    try:
        return date(year, born.month, born.day)
    except ValueError:
        # Feb 29 -> Feb 28 on non-leap years.
        return date(year, 2, 28)


@dataclass(frozen=True)
class ClientsAddedSeriesPoint:
    day: date
    label: str
    count: int
    pct_of_max: int


def clients_added_last_n_days(*, days: int = 7) -> dict:
    if days <= 0:
        raise ValueError("days must be positive")

    today = _today()
    start = today - timedelta(days=days - 1)

    rows = (
        Client.objects.filter(created_at__date__gte=start, created_at__date__lte=today)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    counts_by_day = {r["day"]: int(r["count"]) for r in rows}

    series: list[ClientsAddedSeriesPoint] = []
    max_count = max(counts_by_day.values() or [0])
    denom = max_count if max_count > 0 else 1

    for i in range(days):
        d = start + timedelta(days=i)
        count = counts_by_day.get(d, 0)
        pct = int(round((count / denom) * 100))
        series.append(
            ClientsAddedSeriesPoint(
                day=d,
                label=d.strftime("%m/%d"),
                count=count,
                pct_of_max=pct,
            )
        )

    return {
        "start": start,
        "end": today,
        "total": sum(p.count for p in series),
        "max": max_count,
        "series": series,
    }


def clients_turning_65(*, window_days: int = 90) -> list[dict]:
    today = _today()
    end = today + timedelta(days=window_days)

    results: list[dict] = []

    for client in Client.objects.exclude(dob__isnull=True).only("id", "full_name", "dob", "phone_number"):
        dob = client.dob

        turning = _birthday_in_year(dob, dob.year + 65)
        if turning < today:
            continue
        if turning > end:
            continue

        results.append(
            {
                "id": client.id,
                "full_name": client.full_name or f"Client #{client.id}",
                "dob": dob.strftime("%m/%d/%Y"),
                "phone_number": client.phone_number or "",
                "turns_65_on": turning,
                "age_now": today.year
                - dob.year
                - (1 if (today.month, today.day) < (dob.month, dob.day) else 0),
                "days_until": (turning - today).days,
            }
        )

    results.sort(key=lambda r: (r["turns_65_on"], r["full_name"]))
    return results


# TODO (future dashboard cards):
# - Recent clients
# - Missing documents (no policy / no attachments)
# - Recent attachments
# - Follow-up needed (needs activity tracking)
# - Monthly client growth
# - Upcoming birthdays / renewals
# - Incomplete profiles
# - Document capture activity
