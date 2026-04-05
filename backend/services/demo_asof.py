"""Shared 'as of' calendar date for analytics and insights (demo-aware)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import settings
from models.booking import DailyOccupancy


def _to_date(rd: Any) -> date:
    if isinstance(rd, datetime):
        return rd.date()
    if isinstance(rd, date):
        return rd
    if hasattr(rd, "date"):
        return rd.date()
    return datetime.fromisoformat(str(rd)[:10]).date()


def get_asof_date(db: Session, property_id: int) -> date:
    q = select(func.max(DailyOccupancy.date)).where(DailyOccupancy.property_id == property_id)
    d = db.scalar(q)
    if d is None:
        return datetime.now(timezone.utc).date()
    mx = _to_date(d)
    if settings.demo_today:
        return min(settings.demo_today, mx)
    return mx
