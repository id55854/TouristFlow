"""What-if simulator aggregation over date range and room types."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.pricing import WhatIfScenario
from models.property import Property, RoomType
from services.pricing_context import estimated_room_rate, get_daily_occupancy, season_str
from services.pricing_optimizer import pricing_optimizer


def run_whatif_simulation(
    db: Session,
    property_id: int,
    start_date: date,
    end_date: date,
    price_adjustments_pct: dict[str, float],
    name: str | None = None,
    description: str | None = None,
    save: bool = True,
) -> dict[str, Any]:
    prop = db.get(Property, property_id)
    if prop is None:
        raise ValueError("Property not found")

    room_types = db.scalars(select(RoomType).where(RoomType.property_id == property_id)).all()
    if not room_types:
        raise ValueError("No room types")

    total_rooms = sum(int(rt.count) for rt in room_types)

    total_baseline = 0.0
    total_scenario = 0.0
    baseline_occ_sum = 0.0
    scenario_occ_sum = 0.0
    daily_breakdown: list[dict[str, Any]] = []

    d = start_date
    num_days = 0
    while d <= end_date:
        daily = get_daily_occupancy(db, property_id, d)
        if daily is None:
            d += timedelta(days=1)
            continue

        num_days += 1
        occ = float(daily.occupancy_pct or 0)
        season = season_str(daily)
        adr = float(daily.adr or 0)

        day_base = 0.0
        day_scen = 0.0
        weighted_scen_occ = 0.0

        for rt in room_types:
            base_rate = estimated_room_rate(adr, rt)
            pct = float(price_adjustments_pct.get(rt.code, 0.0))
            w = pricing_optimizer.run_whatif(
                base_rate,
                pct,
                occ,
                season,
                rt.count,
                1,
            )
            day_base += w["baseline"]["total_revenue"]
            day_scen += w["scenario"]["total_revenue"]
            weighted_scen_occ += float(w["scenario"]["occupancy"]) * int(rt.count)

        avg_scen_occ_day = weighted_scen_occ / total_rooms if total_rooms else occ

        total_baseline += day_base
        total_scenario += day_scen
        baseline_occ_sum += occ
        scenario_occ_sum += avg_scen_occ_day

        daily_breakdown.append(
            {
                "date": d.isoformat(),
                "baseline_revenue": round(day_base, 2),
                "scenario_revenue": round(day_scen, 2),
                "baseline_occupancy": occ,
                "scenario_occupancy": round(avg_scen_occ_day, 4),
            }
        )

        d += timedelta(days=1)

    rooms = int(prop.total_rooms)
    baseline_occ_avg = baseline_occ_sum / num_days if num_days else 0.0
    scenario_occ_avg = scenario_occ_sum / num_days if num_days else 0.0
    baseline_revpar = (total_baseline / (rooms * num_days)) if rooms and num_days else 0.0
    scenario_revpar = (total_scenario / (rooms * num_days)) if rooms and num_days else 0.0

    revenue_delta = total_scenario - total_baseline
    revenue_delta_pct = (revenue_delta / total_baseline * 100) if total_baseline > 0 else 0.0

    result: dict[str, Any] = {
        "baseline_revenue": round(total_baseline, 2),
        "scenario_revenue": round(total_scenario, 2),
        "revenue_delta": round(revenue_delta, 2),
        "revenue_delta_pct": round(revenue_delta_pct, 1),
        "baseline_occupancy": round(baseline_occ_avg, 3),
        "scenario_occupancy": round(scenario_occ_avg, 3),
        "baseline_revpar": round(baseline_revpar, 2),
        "scenario_revpar": round(scenario_revpar, 2),
        "daily_breakdown": daily_breakdown,
        "days_modelled": num_days,
    }

    scenario_id: int | None = None
    if save and num_days > 0:
        row = WhatIfScenario(
            property_id=property_id,
            name=name or f"What-if {start_date} → {end_date}",
            description=description,
            date_range_start=datetime.combine(start_date, datetime.min.time()),
            date_range_end=datetime.combine(end_date, datetime.min.time()),
            price_adjustments=price_adjustments_pct,
            predicted_occupancy=scenario_occ_avg,
            predicted_revenue=total_scenario,
            predicted_revpar=scenario_revpar,
            baseline_revenue=total_baseline,
            revenue_delta=revenue_delta,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        scenario_id = row.id

    result["scenario_id"] = scenario_id
    return result
