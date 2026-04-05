"""Insights API schemas."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class ExplainPriceBody(BaseModel):
    property_id: int
    date: date
    room_type_code: str


class ExplainPriceResponse(BaseModel):
    explanation: str


class DailyBriefResponse(BaseModel):
    brief: str


class MarketAnalysisBody(BaseModel):
    property_id: int
    start_date: date
    end_date: date


class MarketAnalysisResponse(BaseModel):
    analysis: dict[str, Any]
