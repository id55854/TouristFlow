"""Booking and daily occupancy models."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from database import Base
from models.property import SeasonType


class BookingSource(str, enum.Enum):
    DIRECT = "direct"
    BOOKING_COM = "booking_com"
    EXPEDIA = "expedia"
    AIRBNB = "airbnb"
    TRAVEL_AGENT = "travel_agent"
    CORPORATE = "corporate"
    GROUP = "group"
    WALK_IN = "walk_in"


class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    room_type_id = Column(Integer, ForeignKey("room_types.id"))
    booking_ref = Column(String, unique=True)
    guest_country = Column(String)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    nights = Column(Integer, nullable=False)
    rooms_booked = Column(Integer, default=1)
    guests = Column(Integer, default=2)
    rate_per_night = Column(Float, nullable=False)
    total_revenue = Column(Float, nullable=False)
    source = Column(Enum(BookingSource, values_callable=lambda x: [e.value for e in x]))
    status = Column(Enum(BookingStatus, values_callable=lambda x: [e.value for e in x]), default=BookingStatus.CONFIRMED)
    booking_date = Column(DateTime, nullable=False)
    lead_time_days = Column(Integer)
    cancellation_date = Column(DateTime, nullable=True)
    is_repeat_guest = Column(Boolean, default=False)
    special_requests = Column(String, nullable=True)

    property = relationship("Property", back_populates="bookings")
    room_type = relationship("RoomType", back_populates="bookings")


class DailyOccupancy(Base):
    __tablename__ = "daily_occupancy"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    date = Column(DateTime, nullable=False, index=True)
    rooms_available = Column(Integer)
    rooms_sold = Column(Integer)
    rooms_remaining = Column(Integer)
    occupancy_pct = Column(Float)
    adr = Column(Float)
    revpar = Column(Float)
    total_revenue = Column(Float)
    bookings_received = Column(Integer)
    cancellations = Column(Integer)
    avg_lead_time = Column(Float)
    source_mix = Column(JSON)
    guest_country_mix = Column(JSON)
    day_of_week = Column(Integer)
    month = Column(Integer)
    is_weekend = Column(Boolean)
    season = Column(Enum(SeasonType, values_callable=lambda x: [e.value for e in x]))
