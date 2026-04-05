"""Load daily occupancy, competitor rates, and demand signals for pricing."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.booking import DailyOccupancy
from models.property import RoomType
from models.signal import Competitor, CompetitorRate, ExternalSignal


def get_daily_occupancy(db: Session, property_id: int, d: date) -> DailyOccupancy | None:
    stmt = (
        select(DailyOccupancy)
        .where(
            DailyOccupancy.property_id == property_id,
            func.date(DailyOccupancy.date) == d,
        )
        .limit(1)
    )
    return db.scalars(stmt).first()


def list_daily_in_range(db: Session, property_id: int, start: date, end: date) -> list[DailyOccupancy]:
    stmt = (
        select(DailyOccupancy)
        .where(
            DailyOccupancy.property_id == property_id,
            func.date(DailyOccupancy.date) >= start,
            func.date(DailyOccupancy.date) <= end,
        )
        .order_by(DailyOccupancy.date)
    )
    return list(db.scalars(stmt).all())


def estimated_room_rate(property_adr: float, rt: RoomType) -> float:
    raw = property_adr * float(rt.rate_multiplier or 1.0)
    lo = float(rt.floor_rate) if rt.floor_rate is not None else raw * 0.5
    hi = float(rt.ceiling_rate) if rt.ceiling_rate is not None else raw * 2.0
    return max(lo, min(hi, raw))


def competitor_avg_rate(db: Session, property_id: int, d: date) -> float | None:
    stmt = (
        select(func.avg(CompetitorRate.rate))
        .join(Competitor, CompetitorRate.competitor_id == Competitor.id)
        .where(
            Competitor.property_id == property_id,
            func.date(CompetitorRate.date) == d,
        )
    )
    v = db.scalar(stmt)
    if v is None:
        return None
    return float(v)


def build_demand_signals(db: Session, property_id: int, d: date) -> list[dict[str, Any]]:
    stmt = select(ExternalSignal).where(
        ExternalSignal.property_id == property_id,
        func.date(ExternalSignal.date) == d,
    )
    sigs = db.scalars(stmt).all()
    out: list[dict[str, Any]] = []
    for s in sigs:
        if s.signal_type == "weather" and s.weather_score is not None:
            out.append(
                {
                    "type": "weather",
                    "label": f"Score {s.weather_score:.0f}",
                    "magnitude": float(s.weather_score),
                    "impact": "positive",
                }
            )
        elif s.signal_type == "flight" and s.flight_arrivals is not None:
            mag = min(100.0, float(s.flight_arrivals) / 250.0 * 100.0)
            yoy = s.flight_yoy_change or 0
            out.append(
                {
                    "type": "flight",
                    "label": f"Arrivals {s.flight_arrivals}, YoY {yoy:+.0%}",
                    "magnitude": mag,
                    "impact": "positive" if yoy >= 0 else "negative",
                }
            )
        elif s.signal_type == "event" and s.event_impact_score is not None:
            out.append(
                {
                    "type": "event",
                    "label": s.event_name or "Event",
                    "magnitude": float(s.event_impact_score),
                    "impact": "positive",
                }
            )
    return out


def season_str(daily: DailyOccupancy) -> str:
    if daily.season is not None:
        return daily.season.value
    return "shoulder"
