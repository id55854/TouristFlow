"""Simulator API schemas."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class WhatIfInput(BaseModel):
    property_id: int
    date_range_start: date
    date_range_end: date
    price_adjustments: dict[str, float] = Field(
        description="Room type code → percent change e.g. SUP_DBL_SV: -10"
    )
    name: str | None = None
    description: str | None = None


class DailyBreakdown(BaseModel):
    date: str
    baseline_revenue: float
    scenario_revenue: float
    baseline_occupancy: float
    scenario_occupancy: float


class WhatIfResult(BaseModel):
    scenario_id: int | None
    baseline_revenue: float
    scenario_revenue: float
    revenue_delta: float
    revenue_delta_pct: float
    baseline_occupancy: float
    scenario_occupancy: float
    baseline_revpar: float
    scenario_revpar: float
    daily_breakdown: list[DailyBreakdown]
    days_modelled: int


class ScenarioSummary(BaseModel):
    id: int
    name: str | None
    date_range_start: date | None
    date_range_end: date | None
    baseline_revenue: float | None
    revenue_delta: float | None
    created_at: str | None


class CompareBody(BaseModel):
    scenario_ids: list[int]
