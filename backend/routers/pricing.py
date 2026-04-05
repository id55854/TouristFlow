"""Dynamic pricing API — Section 5."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models.pricing import PriceRecommendation
from models.property import Property, RoomType
from models.signal import ExternalSignal
from routers.deps import get_property_or_404
from schemas.pricing import (
    AcceptPricingBody,
    CalendarDay,
    CalendarResponse,
    HistoryItem,
    OverridePricingBody,
    PriceRecommendationItem,
    PricingActionResponse,
    PricingHistoryResponse,
    PricingSummaryResponse,
    RecommendationsResponse,
)
from services.pricing_context import build_demand_signals, list_daily_in_range
from services.pricing_optimizer import pricing_optimizer
from services.pricing_service import generate_recommendations, summarize_uplift

router = APIRouter(prefix="/pricing", tags=["pricing"])


def _parse_month(month: str) -> tuple[date, date]:
    try:
        y, m = month.split("-")
        yi, mi = int(y), int(m)
        _, last = calendar.monthrange(yi, mi)
        start = date(yi, mi, 1)
        end = date(yi, mi, last)
        return start, end
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid month (use YYYY-MM): {e}") from e


def _to_items(rows: list[dict[str, Any]]) -> list[PriceRecommendationItem]:
    out: list[PriceRecommendationItem] = []
    for r in rows:
        out.append(
            PriceRecommendationItem(
                date=r["date"],
                room_type_id=r["room_type_id"],
                room_type_code=r["room_type_code"],
                room_type_name=r["room_type_name"],
                current_rate=r["current_rate"],
                recommended_rate=r["recommended_rate"],
                change_pct=r["change_pct"],
                confidence=r["confidence"],
                predicted_occupancy_current=r["predicted_occupancy_current"],
                predicted_occupancy_recommended=r["predicted_occupancy_recommended"],
                revpar_current=r["revpar_current"],
                revpar_recommended=r["revpar_recommended"],
                revpar_uplift=r["revpar_uplift"],
                demand_level=r["demand_level"],
                rationale=r["rationale"],
            )
        )
    return out


@router.get("/recommendations", response_model=RecommendationsResponse)
def get_recommendations(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> RecommendationsResponse:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")
    rows = generate_recommendations(db, property_id, start_date, end_date, persist=True)
    return RecommendationsResponse(
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        recommendations=_to_items(rows),
    )


@router.get("/calendar", response_model=CalendarResponse)
def get_pricing_calendar(
    property_id: int = Query(...),
    month: str = Query(..., description="YYYY-MM"),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> CalendarResponse:
    start, end = _parse_month(month)
    days_out: list[CalendarDay] = []
    for daily in list_daily_in_range(db, property_id, start, end):
        dd = daily.date
        if isinstance(dd, datetime):
            d = dd.date()
        elif hasattr(dd, "date"):
            d = dd.date()
        else:
            d = dd
        sigs = build_demand_signals(db, property_id, d)
        score = pricing_optimizer._aggregate_demand_signals(sigs)
        level = pricing_optimizer._classify_demand(score)
        season = daily.season.value if daily.season else "shoulder"
        events: list[str] = []
        ev_rows = db.scalars(
            select(ExternalSignal).where(
                ExternalSignal.property_id == property_id,
                func.date(ExternalSignal.date) == d,
                ExternalSignal.signal_type == "event",
            )
        ).all()
        for e in ev_rows:
            if e.event_name:
                events.append(e.event_name)
        days_out.append(
            CalendarDay(date=d, demand_level=level, season=season, events=events)
        )
    return CalendarResponse(property_id=property_id, month=month, days=days_out)


@router.get("/summary", response_model=PricingSummaryResponse)
def get_pricing_summary(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> PricingSummaryResponse:
    rows = generate_recommendations(db, property_id, start_date, end_date, persist=False)
    s = summarize_uplift(rows, db, property_id)
    return PricingSummaryResponse(
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        total_estimated_revpar_uplift_eur_per_night=s["total_estimated_revpar_uplift_eur_per_night"],
        recommendation_count=s["recommendation_count"],
    )


@router.get("/history", response_model=PricingHistoryResponse)
def get_pricing_history(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> PricingHistoryResponse:
    stmt = (
        select(PriceRecommendation)
        .where(
            PriceRecommendation.property_id == property_id,
            func.date(PriceRecommendation.date) >= start_date,
            func.date(PriceRecommendation.date) <= end_date,
        )
        .order_by(PriceRecommendation.date, PriceRecommendation.room_type_id)
    )
    rows = db.scalars(stmt).all()
    items = [
        HistoryItem(
            date=r.date,
            room_type_id=r.room_type_id,
            current_rate=r.current_rate,
            recommended_rate=r.recommended_rate,
            rate_change_pct=r.rate_change_pct,
            confidence=r.confidence,
            rationale=r.rationale,
        )
        for r in rows
    ]
    return PricingHistoryResponse(property_id=property_id, items=items)


@router.post("/accept", response_model=PricingActionResponse)
def accept_pricing(
    body: AcceptPricingBody,
    db: Session = Depends(get_db),
) -> PricingActionResponse:
    if db.get(Property, body.property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")
    rt = db.get(RoomType, body.room_type_id)
    if rt is None or rt.property_id != body.property_id:
        raise HTTPException(status_code=400, detail="Invalid room_type_id")
    db.add(
        PriceRecommendation(
            property_id=body.property_id,
            room_type_id=body.room_type_id,
            date=datetime.combine(body.date, datetime.min.time()).replace(hour=12),
            current_rate=body.accepted_rate,
            recommended_rate=body.accepted_rate,
            rate_change_pct=0.0,
            confidence=1.0,
            predicted_occupancy_at_current=None,
            predicted_occupancy_at_recommended=None,
            predicted_revpar_current=None,
            predicted_revpar_recommended=None,
            revpar_uplift_eur=0.0,
            rationale="Accepted by revenue manager.",
            demand_signals={"status": "accepted"},
        )
    )
    db.commit()
    return PricingActionResponse(status="ok", message="Accepted rate recorded.")


@router.post("/override", response_model=PricingActionResponse)
def override_pricing(
    body: OverridePricingBody,
    db: Session = Depends(get_db),
) -> PricingActionResponse:
    if db.get(Property, body.property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")
    rt = db.get(RoomType, body.room_type_id)
    if rt is None or rt.property_id != body.property_id:
        raise HTTPException(status_code=400, detail="Invalid room_type_id")
    db.add(
        PriceRecommendation(
            property_id=body.property_id,
            room_type_id=body.room_type_id,
            date=datetime.combine(body.date, datetime.min.time()).replace(hour=12),
            current_rate=body.override_rate,
            recommended_rate=body.override_rate,
            rate_change_pct=0.0,
            confidence=1.0,
            predicted_occupancy_at_current=None,
            predicted_occupancy_at_recommended=None,
            predicted_revpar_current=None,
            predicted_revpar_recommended=None,
            revpar_uplift_eur=0.0,
            rationale=f"Manual override: {body.reason}",
            demand_signals={"status": "override", "reason": body.reason},
        )
    )
    db.commit()
    return PricingActionResponse(status="ok", message="Override recorded.")
