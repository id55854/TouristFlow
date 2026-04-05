"""Pricing API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class PriceRecommendationItem(BaseModel):
    date: date
    room_type_id: int
    room_type_code: str
    room_type_name: str
    current_rate: float
    recommended_rate: float
    change_pct: float
    confidence: float
    predicted_occupancy_current: float
    predicted_occupancy_recommended: float
    revpar_current: float
    revpar_recommended: float
    revpar_uplift: float
    demand_level: str
    rationale: str


class RecommendationsResponse(BaseModel):
    property_id: int
    start_date: date
    end_date: date
    recommendations: list[PriceRecommendationItem]


class CalendarDay(BaseModel):
    date: date
    demand_level: str
    season: str
    events: list[str] = []


class CalendarResponse(BaseModel):
    property_id: int
    month: str
    days: list[CalendarDay]


class PricingSummaryResponse(BaseModel):
    property_id: int
    start_date: date
    end_date: date
    total_estimated_revpar_uplift_eur_per_night: float
    recommendation_count: int


class HistoryItem(BaseModel):
    date: datetime
    room_type_id: int
    current_rate: float | None
    recommended_rate: float
    rate_change_pct: float | None
    confidence: float | None
    rationale: str | None


class PricingHistoryResponse(BaseModel):
    property_id: int
    items: list[HistoryItem]


class AcceptPricingBody(BaseModel):
    property_id: int
    date: date
    room_type_id: int
    accepted_rate: float


class OverridePricingBody(BaseModel):
    property_id: int
    date: date
    room_type_id: int
    override_rate: float
    reason: str


class PricingActionResponse(BaseModel):
    status: str
    message: str
