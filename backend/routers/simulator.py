"""What-if simulator API — Section 5."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.pricing import WhatIfScenario
from models.property import Property
from routers.deps import get_property_or_404
from schemas.simulator import CompareBody, DailyBreakdown, ScenarioSummary, WhatIfInput, WhatIfResult
from services.simulator_service import run_whatif_simulation

router = APIRouter(prefix="/simulator", tags=["simulator"])


def _to_whatif_result(data: dict) -> WhatIfResult:
    db_rows = [
        DailyBreakdown(
            date=x["date"],
            baseline_revenue=x["baseline_revenue"],
            scenario_revenue=x["scenario_revenue"],
            baseline_occupancy=x["baseline_occupancy"],
            scenario_occupancy=x["scenario_occupancy"],
        )
        for x in data["daily_breakdown"]
    ]
    return WhatIfResult(
        scenario_id=data.get("scenario_id"),
        baseline_revenue=data["baseline_revenue"],
        scenario_revenue=data["scenario_revenue"],
        revenue_delta=data["revenue_delta"],
        revenue_delta_pct=data["revenue_delta_pct"],
        baseline_occupancy=data["baseline_occupancy"],
        scenario_occupancy=data["scenario_occupancy"],
        baseline_revpar=data["baseline_revpar"],
        scenario_revpar=data["scenario_revpar"],
        daily_breakdown=db_rows,
        days_modelled=data["days_modelled"],
    )


@router.post("/run", response_model=WhatIfResult)
def run_simulator(
    body: WhatIfInput,
    db: Session = Depends(get_db),
) -> WhatIfResult:
    if db.get(Property, body.property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")
    if body.date_range_end < body.date_range_start:
        raise HTTPException(status_code=400, detail="Invalid date range")
    try:
        data = run_whatif_simulation(
            db,
            body.property_id,
            body.date_range_start,
            body.date_range_end,
            body.price_adjustments,
            name=body.name,
            description=body.description,
            save=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_whatif_result(data)


@router.get("/scenarios", response_model=list[ScenarioSummary])
def list_scenarios(
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> list[ScenarioSummary]:
    stmt = (
        select(WhatIfScenario)
        .where(WhatIfScenario.property_id == property_id)
        .order_by(WhatIfScenario.created_at.desc())
    )
    rows = db.scalars(stmt).all()
    out: list[ScenarioSummary] = []
    for r in rows:
        ds = r.date_range_start.date() if r.date_range_start else None
        de = r.date_range_end.date() if r.date_range_end else None
        ca = r.created_at.isoformat() if r.created_at else None
        out.append(
            ScenarioSummary(
                id=r.id,
                name=r.name,
                date_range_start=ds,
                date_range_end=de,
                baseline_revenue=r.baseline_revenue,
                revenue_delta=r.revenue_delta,
                created_at=ca,
            )
        )
    return out


@router.get("/scenarios/{scenario_id}", response_model=WhatIfResult)
def get_scenario(
    scenario_id: int,
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> WhatIfResult:
    r = db.get(WhatIfScenario, scenario_id)
    if r is None or r.property_id != property_id:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if r.date_range_start is None or r.date_range_end is None or r.price_adjustments is None:
        raise HTTPException(status_code=400, detail="Incomplete scenario")
    data = run_whatif_simulation(
        db,
        property_id,
        r.date_range_start.date(),
        r.date_range_end.date(),
        dict(r.price_adjustments),
        name=r.name,
        description=r.description,
        save=False,
    )
    data["scenario_id"] = r.id
    return _to_whatif_result(data)


@router.post("/compare")
def compare_scenarios(
    body: CompareBody,
    property_id: int = Query(...),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not body.scenario_ids:
        raise HTTPException(status_code=400, detail="scenario_ids required")
    results = []
    for sid in body.scenario_ids:
        r = db.get(WhatIfScenario, sid)
        if r is None or r.property_id != property_id:
            continue
        if r.date_range_start and r.date_range_end and r.price_adjustments:
            data = run_whatif_simulation(
                db,
                property_id,
                r.date_range_start.date(),
                r.date_range_end.date(),
                dict(r.price_adjustments),
                save=False,
            )
            data["scenario_id"] = r.id
            data["name"] = r.name
            results.append(data)
    return {"property_id": property_id, "scenarios": results}
