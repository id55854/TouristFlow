"""Pricing recommendations, forecasts, and what-if scenarios."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from database import Base


class PriceRecommendation(Base):
    __tablename__ = "price_recommendations"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    room_type_id = Column(Integer, ForeignKey("room_types.id"))
    date = Column(DateTime, nullable=False, index=True)
    current_rate = Column(Float)
    recommended_rate = Column(Float, nullable=False)
    rate_change_pct = Column(Float)
    confidence = Column(Float)
    predicted_occupancy_at_current = Column(Float)
    predicted_occupancy_at_recommended = Column(Float)
    predicted_revpar_current = Column(Float)
    predicted_revpar_recommended = Column(Float)
    revpar_uplift_eur = Column(Float)
    rationale = Column(String)
    demand_signals = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="price_recommendations")


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    target_date = Column(DateTime, nullable=False, index=True)
    forecast_type = Column(String)
    predicted_value = Column(Float, nullable=False)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    actual_value = Column(Float, nullable=True)
    model_version = Column(String, default="prophet_v1")
    features_used = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="forecasts")


class WhatIfScenario(Base):
    __tablename__ = "whatif_scenarios"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    name = Column(String)
    description = Column(String)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    price_adjustments = Column(JSON)
    predicted_occupancy = Column(Float)
    predicted_revenue = Column(Float)
    predicted_revpar = Column(Float)
    baseline_revenue = Column(Float)
    revenue_delta = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
