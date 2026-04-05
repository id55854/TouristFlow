"""Competitor intelligence API — Section 5."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models.booking import DailyOccupancy
from models.property import Property
from models.signal import Competitor, CompetitorRate
from routers.deps import get_property_or_404
from schemas.competitors import (
    CompetitorRatePoint,
    CompetitorRatesResponse,
    CompetitorsListResponse,
    CompetitorWithRate,
    PositionResponse,
)

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("", response_model=CompetitorsListResponse)
def list_competitors(
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> CompetitorsListResponse:
    comps = db.scalars(select(Competitor).where(Competitor.property_id == property_id)).all()
    out: list[CompetitorWithRate] = []
    for c in comps:
        stmt = (
            select(CompetitorRate)
            .where(CompetitorRate.competitor_id == c.id)
            .order_by(CompetitorRate.date.desc())
            .limit(1)
        )
        lr = db.scalars(stmt).first()
        rd = lr.date.date() if lr and hasattr(lr.date, "date") else (lr.date if lr else None)
        if isinstance(rd, datetime):
            rd = rd.date()
        out.append(
            CompetitorWithRate(
                id=c.id,
                name=c.competitor_name,
                stars=c.competitor_stars,
                rooms=c.competitor_rooms,
                is_primary=bool(c.is_primary),
                latest_rate_eur=float(lr.rate) if lr else None,
                rate_date=rd,
                available=lr.availability if lr else None,
            )
        )
    return CompetitorsListResponse(property_id=property_id, competitors=out)


@router.get("/rates", response_model=CompetitorRatesResponse)
def competitor_rates(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> CompetitorRatesResponse:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="Invalid date range")
    stmt = (
        select(CompetitorRate, Competitor)
        .join(Competitor, CompetitorRate.competitor_id == Competitor.id)
        .where(
            Competitor.property_id == property_id,
            func.date(CompetitorRate.date) >= start_date,
            func.date(CompetitorRate.date) <= end_date,
        )
        .order_by(CompetitorRate.date, Competitor.competitor_name)
    )
    rows = db.execute(stmt).all()
    points: list[CompetitorRatePoint] = []
    for cr, comp in rows:
        dd = cr.date.date() if hasattr(cr.date, "date") else cr.date
        if isinstance(dd, datetime):
            dd = dd.date()
        points.append(
            CompetitorRatePoint(
                date=dd,
                competitor_id=comp.id,
                competitor_name=comp.competitor_name,
                rate=float(cr.rate),
                available=bool(cr.availability),
            )
        )
    return CompetitorRatesResponse(
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        points=points,
    )


@router.get("/position", response_model=PositionResponse)
def rate_position(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> PositionResponse:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="Invalid date range")
    our_avg = db.scalar(
        select(func.avg(DailyOccupancy.adr)).where(
            DailyOccupancy.property_id == property_id,
            func.date(DailyOccupancy.date) >= start_date,
            func.date(DailyOccupancy.date) <= end_date,
        )
    )
    our_avg = float(our_avg or 0)

    comp_avg = db.scalar(
        select(func.avg(CompetitorRate.rate))
        .join(Competitor, CompetitorRate.competitor_id == Competitor.id)
        .where(
            Competitor.property_id == property_id,
            func.date(CompetitorRate.date) >= start_date,
            func.date(CompetitorRate.date) <= end_date,
        )
    )
    comp_avg = float(comp_avg or 0)

    pos = ((our_avg - comp_avg) / comp_avg * 100) if comp_avg > 0 else 0.0

    return PositionResponse(
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        our_avg_adr=round(our_avg, 2),
        comp_avg_rate=round(comp_avg, 2),
        position_pct_vs_comp=round(pos, 1),
    )
