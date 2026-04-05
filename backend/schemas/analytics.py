"""Pydantic schemas for analytics APIs."""

from datetime import date

from pydantic import BaseModel, Field


class TrendPoint(BaseModel):
    date: date
    occupancy: float | None = None
    adr: float | None = None
    revpar: float | None = None
    total_revenue: float | None = None


class OccupancyTrendResponse(BaseModel):
    property_id: int
    period_days: int
    points: list[TrendPoint]


class RevenueTrendResponse(BaseModel):
    property_id: int
    period_days: int
    points: list[TrendPoint]


class PickupBucket(BaseModel):
    lead_time_label: str
    lead_time_min: int
    lead_time_max: int | None
    booking_count: int
    room_nights: int


class PickupResponse(BaseModel):
    property_id: int
    stay_date: date
    buckets: list[PickupBucket]
    total_bookings: int


class SourceMixItem(BaseModel):
    source: str
    count: int
    share: float


class SourceMixResponse(BaseModel):
    property_id: int
    total_bookings: int
    items: list[SourceMixItem]


class GuestMixItem(BaseModel):
    country: str
    count: int
    share: float


class GuestMixResponse(BaseModel):
    property_id: int
    total_guest_stays: int
    items: list[GuestMixItem]


class SeasonalityMonth(BaseModel):
    year: int
    month: int
    avg_occupancy: float
    avg_adr: float
    avg_revpar: float
    total_revenue: float


class SeasonalityResponse(BaseModel):
    property_id: int
    by_month: list[SeasonalityMonth]


class DowPattern(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Monday")
    label: str
    avg_occupancy: float
    avg_adr: float
    avg_revpar: float
    sample_days: int


class DowPatternsResponse(BaseModel):
    property_id: int
    patterns: list[DowPattern]
