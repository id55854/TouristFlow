"""Competitor API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class CompetitorWithRate(BaseModel):
    id: int
    name: str
    stars: int | None
    rooms: int | None
    is_primary: bool
    latest_rate_eur: float | None
    rate_date: date | None
    available: bool | None


class CompetitorsListResponse(BaseModel):
    property_id: int
    competitors: list[CompetitorWithRate]


class CompetitorRatePoint(BaseModel):
    date: date
    competitor_id: int
    competitor_name: str
    rate: float
    available: bool


class CompetitorRatesResponse(BaseModel):
    property_id: int
    start_date: date
    end_date: date
    points: list[CompetitorRatePoint]


class PositionResponse(BaseModel):
    property_id: int
    start_date: date
    end_date: date
    our_avg_adr: float
    comp_avg_rate: float
    position_pct_vs_comp: float
