"""Gemini-powered insights — Section 5 & 6.3."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models.booking import DailyOccupancy
from models.property import Property, RoomType
from models.signal import ExternalSignal
from routers.deps import get_property_or_404
from schemas.insights import DailyBriefResponse, ExplainPriceBody, ExplainPriceResponse, MarketAnalysisBody, MarketAnalysisResponse
from services.demo_asof import get_asof_date
from services.forecaster import run_occupancy_forecast
from services.gemini import gemini_engine
from services.pricing_context import build_demand_signals, competitor_avg_rate
from services.pricing_service import generate_recommendations, load_recommendation_from_db

router = APIRouter(prefix="/insights", tags=["insights"])


def _as_date(d: object) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if hasattr(d, "date"):
        return d.date()
    return d


@router.get("/daily-brief", response_model=DailyBriefResponse)
async def daily_brief(
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> DailyBriefResponse:
    prop = db.get(Property, property_id)
    assert prop is not None

    if db.scalar(
        select(func.max(DailyOccupancy.date)).where(DailyOccupancy.property_id == property_id)
    ) is None:
        raise HTTPException(status_code=400, detail="No occupancy data")

    today = get_asof_date(db, property_id)

    stmt = (
        select(DailyOccupancy)
        .where(
            DailyOccupancy.property_id == property_id,
            func.date(DailyOccupancy.date) == today,
        )
        .limit(1)
    )
    daily = db.scalars(stmt).first()
    occ = float(daily.occupancy_pct) if daily and daily.occupancy_pct is not None else 0.0
    adr = float(daily.adr) if daily and daily.adr is not None else 0.0
    revpar = float(daily.revpar) if daily and daily.revpar is not None else 0.0

    occ_df, _ = run_occupancy_forecast(db, property_id, 7)
    next_7: list[dict] = []
    if not occ_df.empty:
        for _, row in occ_df.iterrows():
            ds = row["ds"]
            d = pd.Timestamp(ds).date() if not hasattr(ds, "date") else ds.date()
            next_7.append({"date": str(d), "predicted_occupancy": float(row["yhat"])})

    sigs = build_demand_signals(db, property_id, today)

    forecast_data = {
        "today_occupancy": round(occ * 100, 1),
        "today_adr": round(adr, 2),
        "today_revpar": round(revpar, 2),
        "next_7_days": next_7,
    }
    property_data = {
        "name": prop.name,
        "stars": prop.stars,
        "total_rooms": prop.total_rooms,
        "city": prop.city,
    }

    text = await gemini_engine.daily_brief(property_data, forecast_data, sigs)
    return DailyBriefResponse(brief=text)


@router.post("/explain-price", response_model=ExplainPriceResponse)
async def explain_price(
    body: ExplainPriceBody,
    db: Session = Depends(get_db),
) -> ExplainPriceResponse:
    if db.get(Property, body.property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")

    rows = generate_recommendations(
        db, body.property_id, body.date, body.date, persist=False
    )
    rec = next((r for r in rows if r.get("room_type_code") == body.room_type_code), None)
    if rec is None:
        rec = load_recommendation_from_db(db, body.property_id, body.date, body.room_type_code)
    if rec is None:
        raise HTTPException(status_code=404, detail="No recommendation for that date and room type")

    comp = competitor_avg_rate(db, body.property_id, body.date)
    context = {
        "room_type": body.room_type_code,
        "date": str(body.date),
        "competitor_avg_rate": round(comp, 2) if comp is not None else None,
    }
    text = await gemini_engine.explain_price(rec, context)
    return ExplainPriceResponse(explanation=text)


@router.post("/market-analysis", response_model=MarketAnalysisResponse)
async def market_analysis(
    body: MarketAnalysisBody,
    db: Session = Depends(get_db),
) -> MarketAnalysisResponse:
    prop = db.get(Property, body.property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")

    prev_start = date(body.start_date.year - 1, body.start_date.month, body.start_date.day)
    prev_end = date(body.end_date.year - 1, body.end_date.month, body.end_date.day)

    def period_revenue(start: date, end: date) -> float:
        stmt = select(func.sum(DailyOccupancy.total_revenue)).where(
            DailyOccupancy.property_id == body.property_id,
            func.date(DailyOccupancy.date) >= start,
            func.date(DailyOccupancy.date) <= end,
        )
        v = db.scalar(stmt)
        return float(v or 0)

    cur_rev = period_revenue(body.start_date, body.end_date)
    prev_rev = period_revenue(prev_start, prev_end)
    yoy = ((cur_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0.0

    historical_comparison = {
        "period_revenue_eur": round(cur_rev, 2),
        "prior_year_revenue_eur": round(prev_rev, 2),
        "yoy_change_pct": round(yoy, 1),
    }

    ev_stmt = (
        select(ExternalSignal)
        .where(
            ExternalSignal.property_id == body.property_id,
            ExternalSignal.signal_type == "event",
            func.date(ExternalSignal.date) >= body.start_date,
            func.date(ExternalSignal.date) <= body.end_date,
        )
        .limit(20)
    )
    upcoming_events: list[dict] = []
    for e in db.scalars(ev_stmt).all():
        if e.event_name:
            upcoming_events.append(
                {
                    "name": e.event_name,
                    "date": str(e.date.date() if hasattr(e.date, "date") else e.date),
                    "impact": e.event_impact_score,
                }
            )

    property_data = {"name": prop.name, "city": prop.city}
    analysis = await gemini_engine.market_analysis(property_data, historical_comparison, upcoming_events)
    return MarketAnalysisResponse(analysis=analysis)
