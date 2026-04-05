"""Pydantic schemas for forecast APIs."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    date: date
    predicted: float
    lower_bound: float
    upper_bound: float


class OccupancyForecastResponse(BaseModel):
    property_id: int
    forecast_horizon: int
    points: list[ForecastPoint]
    model_confidence: float
    last_updated: datetime = Field(description="UTC timestamp")


class DemandPoint(BaseModel):
    date: date
    demand_score: float = Field(ge=0, le=100)
    occupancy_forecast: float
    weather_score: float
    flight_index: float
    event_impact: float
    search_trend: float = 0.0
    season: str


class DemandForecastResponse(BaseModel):
    property_id: int
    forecast_horizon: int
    points: list[DemandPoint]
    model_confidence: float
    last_updated: datetime


class AdrForecastResponse(BaseModel):
    property_id: int
    forecast_horizon: int
    points: list[ForecastPoint]
    model_confidence: float
    last_updated: datetime


class RevparForecastResponse(BaseModel):
    property_id: int
    forecast_horizon: int
    points: list[ForecastPoint]
    model_confidence: float
    last_updated: datetime


class RefreshResponse(BaseModel):
    property_id: int | None
    status: str
    message: str
