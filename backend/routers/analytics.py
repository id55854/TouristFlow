"""Analytics API — Section 5."""

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models.booking import Booking, BookingStatus, DailyOccupancy
from models.property import Property
from routers.deps import get_property_or_404
from services.demo_asof import get_asof_date
from schemas.analytics import (
    DowPattern,
    DowPatternsResponse,
    GuestMixItem,
    GuestMixResponse,
    OccupancyTrendResponse,
    PickupBucket,
    PickupResponse,
    RevenueTrendResponse,
    SeasonalityMonth,
    SeasonalityResponse,
    SourceMixItem,
    SourceMixResponse,
    TrendPoint,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

_DOW_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def parse_period(period: str) -> int:
    """Parse e.g. 90d, 12w, 6m, 1y into approximate days."""
    m = re.match(r"^(\d+)(d|w|m|y)$", period.strip().lower())
    if not m:
        raise HTTPException(status_code=400, detail="period must match pattern like 90d, 12w, 6m, 1y")
    n = int(m.group(1))
    u = m.group(2)
    mult = {"d": 1, "w": 7, "m": 30, "y": 365}
    return max(1, n * mult[u])


def _to_date(rd: Any) -> date:
    if isinstance(rd, datetime):
        return rd.date()
    if isinstance(rd, date):
        return rd
    if hasattr(rd, "date"):
        return rd.date()
    return datetime.fromisoformat(str(rd)[:10]).date()


@router.get("/occupancy-trend", response_model=OccupancyTrendResponse)
def occupancy_trend(
    property_id: int = Query(...),
    period: str = Query("90d", description="Window e.g. 90d, 30d, 1y"),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> OccupancyTrendResponse:
    days = parse_period(period)
    end_d = get_asof_date(db, property_id)
    start_dt = datetime.combine(end_d, datetime.min.time()) - timedelta(days=days - 1)
    end_dt = datetime.combine(end_d, datetime.max.time())

    stmt = (
        select(DailyOccupancy)
        .where(
            DailyOccupancy.property_id == property_id,
            DailyOccupancy.date >= start_dt,
            DailyOccupancy.date <= end_dt,
        )
        .order_by(DailyOccupancy.date)
    )
    rows = db.scalars(stmt).all()
    points: list[TrendPoint] = []
    for r in rows:
        points.append(
            TrendPoint(
                date=_to_date(r.date),
                occupancy=float(r.occupancy_pct) if r.occupancy_pct is not None else None,
                adr=float(r.adr) if r.adr is not None else None,
                revpar=float(r.revpar) if r.revpar is not None else None,
                total_revenue=float(r.total_revenue) if r.total_revenue is not None else None,
            )
        )
    return OccupancyTrendResponse(property_id=property_id, period_days=days, points=points)


@router.get("/revenue-trend", response_model=RevenueTrendResponse)
def revenue_trend(
    property_id: int = Query(...),
    period: str = Query("90d"),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> RevenueTrendResponse:
    days = parse_period(period)
    end_d = get_asof_date(db, property_id)
    start_dt = datetime.combine(end_d, datetime.min.time()) - timedelta(days=days - 1)
    end_dt = datetime.combine(end_d, datetime.max.time())

    stmt = (
        select(DailyOccupancy)
        .where(
            DailyOccupancy.property_id == property_id,
            DailyOccupancy.date >= start_dt,
            DailyOccupancy.date <= end_dt,
        )
        .order_by(DailyOccupancy.date)
    )
    rows = db.scalars(stmt).all()
    points: list[TrendPoint] = []
    for r in rows:
        points.append(
            TrendPoint(
                date=_to_date(r.date),
                total_revenue=float(r.total_revenue) if r.total_revenue is not None else None,
            )
        )
    return RevenueTrendResponse(property_id=property_id, period_days=days, points=points)


def _pickup_bucket(lead: int | None) -> tuple[str, int, int | None]:
    if lead is None:
        return "unknown", -1, -1
    if lead <= 7:
        return "0-7 days", 0, 7
    if lead <= 14:
        return "8-14 days", 8, 14
    if lead <= 30:
        return "15-30 days", 15, 30
    if lead <= 60:
        return "31-60 days", 31, 60
    return "61+ days", 61, None


@router.get("/pickup", response_model=PickupResponse)
def pickup(
    property_id: int = Query(...),
    stay_date: date = Query(..., description="Stay night (check-in date)"),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> PickupResponse:
    stmt = select(Booking).where(
        Booking.property_id == property_id,
        func.date(Booking.check_in) == stay_date,
        Booking.status == BookingStatus.CONFIRMED,
    )
    bookings = db.scalars(stmt).all()

    bucket_map: dict[str, dict[str, Any]] = {}
    for b in bookings:
        label, lo, hi = _pickup_bucket(b.lead_time_days)
        if label not in bucket_map:
            bucket_map[label] = {"label": label, "lo": lo, "hi": hi, "count": 0, "nights": 0}
        bucket_map[label]["count"] += 1
        bucket_map[label]["nights"] += b.nights * b.rooms_booked

    order = ["0-7 days", "8-14 days", "15-30 days", "31-60 days", "61+ days", "unknown"]
    buckets: list[PickupBucket] = []
    for key in order:
        if key in bucket_map:
            m = bucket_map[key]
            buckets.append(
                PickupBucket(
                    lead_time_label=m["label"],
                    lead_time_min=m["lo"],
                    lead_time_max=m["hi"],
                    booking_count=m["count"],
                    room_nights=m["nights"],
                )
            )
    return PickupResponse(
        property_id=property_id,
        stay_date=stay_date,
        buckets=buckets,
        total_bookings=len(bookings),
    )


@router.get("/source-mix", response_model=SourceMixResponse)
def source_mix(
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> SourceMixResponse:
    stmt = (
        select(Booking.source, func.count(Booking.id))
        .where(Booking.property_id == property_id, Booking.status == BookingStatus.CONFIRMED)
        .group_by(Booking.source)
    )
    rows = db.execute(stmt).all()
    total = sum(int(r[1]) for r in rows) or 1
    items = [
        SourceMixItem(source=str(r[0].value if hasattr(r[0], "value") else r[0]), count=int(r[1]), share=round(int(r[1]) / total, 4))
        for r in rows
    ]
    items.sort(key=lambda x: x.share, reverse=True)
    return SourceMixResponse(property_id=property_id, total_bookings=total, items=items)


@router.get("/guest-mix", response_model=GuestMixResponse)
def guest_mix(
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> GuestMixResponse:
    stmt = (
        select(Booking.guest_country, func.count(Booking.id))
        .where(Booking.property_id == property_id, Booking.status == BookingStatus.CONFIRMED)
        .group_by(Booking.guest_country)
    )
    rows = db.execute(stmt).all()
    total = sum(int(r[1]) for r in rows) or 1
    items = [
        GuestMixItem(country=str(r[0] or "Unknown"), count=int(r[1]), share=round(int(r[1]) / total, 4))
        for r in rows
    ]
    items.sort(key=lambda x: x.share, reverse=True)
    return GuestMixResponse(property_id=property_id, total_guest_stays=total, items=items)


@router.get("/seasonality", response_model=SeasonalityResponse)
def seasonality(
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> SeasonalityResponse:
    stmt = select(DailyOccupancy).where(DailyOccupancy.property_id == property_id)
    rows = db.scalars(stmt).all()
    agg: dict[tuple[int, int], list[DailyOccupancy]] = {}
    for r in rows:
        y = _to_date(r.date).year
        m = _to_date(r.date).month
        agg.setdefault((y, m), []).append(r)

    by_month: list[SeasonalityMonth] = []
    for (y, mth) in sorted(agg.keys()):
        xs = agg[(y, mth)]
        n = len(xs)
        by_month.append(
            SeasonalityMonth(
                year=y,
                month=mth,
                avg_occupancy=sum(float(x.occupancy_pct or 0) for x in xs) / n,
                avg_adr=sum(float(x.adr or 0) for x in xs) / n,
                avg_revpar=sum(float(x.revpar or 0) for x in xs) / n,
                total_revenue=sum(float(x.total_revenue or 0) for x in xs),
            )
        )
    return SeasonalityResponse(property_id=property_id, by_month=by_month)


@router.get("/dow-patterns", response_model=DowPatternsResponse)
def dow_patterns(
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> DowPatternsResponse:
    stmt = select(DailyOccupancy).where(DailyOccupancy.property_id == property_id)
    rows = db.scalars(stmt).all()
    buckets: dict[int, list[DailyOccupancy]] = {i: [] for i in range(7)}
    for r in rows:
        dow = int(r.day_of_week) if r.day_of_week is not None else _to_date(r.date).weekday()
        buckets[dow].append(r)

    patterns: list[DowPattern] = []
    for dow in range(7):
        xs = buckets[dow]
        if not xs:
            continue
        n = len(xs)
        patterns.append(
            DowPattern(
                day_of_week=dow,
                label=_DOW_LABELS[dow],
                avg_occupancy=sum(float(x.occupancy_pct or 0) for x in xs) / n,
                avg_adr=sum(float(x.adr or 0) for x in xs) / n,
                avg_revpar=sum(float(x.revpar or 0) for x in xs) / n,
                sample_days=n,
            )
        )
    return DowPatternsResponse(property_id=property_id, patterns=patterns)
