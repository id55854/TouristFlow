"""External signals and competitor models."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from database import Base


class ExternalSignal(Base):
    __tablename__ = "external_signals"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    signal_type = Column(String, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    region = Column(String)

    temperature_high = Column(Float, nullable=True)
    temperature_low = Column(Float, nullable=True)
    precipitation_mm = Column(Float, nullable=True)
    weather_score = Column(Float, nullable=True)

    flight_arrivals = Column(Integer, nullable=True)
    flight_yoy_change = Column(Float, nullable=True)
    top_origin_countries = Column(JSON, nullable=True)

    event_name = Column(String, nullable=True)
    event_type = Column(String, nullable=True)
    event_impact_score = Column(Float, nullable=True)
    event_attendees = Column(Integer, nullable=True)

    search_index = Column(Float, nullable=True)
    search_query = Column(String, nullable=True)


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    competitor_name = Column(String, nullable=False)
    competitor_stars = Column(Integer)
    competitor_rooms = Column(Integer)
    is_primary = Column(Boolean, default=False)

    rates = relationship("CompetitorRate", back_populates="competitor")


class CompetitorRate(Base):
    __tablename__ = "competitor_rates"

    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"))
    date = Column(DateTime, nullable=False, index=True)
    room_type = Column(String)
    rate = Column(Float, nullable=False)
    source = Column(String, default="booking_com")
    availability = Column(Boolean, default=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="rates")
