"""Hotel property and room type models."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from database import Base


class PropertyType(str, enum.Enum):
    HOTEL = "hotel"
    RESORT = "resort"
    BOUTIQUE = "boutique"
    APARTHOTEL = "aparthotel"
    HOSTEL = "hostel"


class SeasonType(str, enum.Enum):
    PEAK = "peak"
    HIGH = "high"
    SHOULDER = "shoulder"
    LOW = "low"


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    chain = Column(String, nullable=True)
    property_type = Column(Enum(PropertyType, values_callable=lambda x: [e.value for e in x]))
    stars = Column(Integer)
    city = Column(String, nullable=False)
    region = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    total_rooms = Column(Integer, nullable=False)
    address = Column(String)
    currency = Column(String, default="EUR")
    min_rate = Column(Float, default=50.0)
    max_rate = Column(Float, default=500.0)
    target_occupancy = Column(Float, default=0.80)
    created_at = Column(DateTime, default=datetime.utcnow)

    room_types = relationship("RoomType", back_populates="property")
    bookings = relationship("Booking", back_populates="property")
    forecasts = relationship("ForecastResult", back_populates="property")
    price_recommendations = relationship("PriceRecommendation", back_populates="property")


class RoomType(Base):
    __tablename__ = "room_types"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    capacity = Column(Integer, default=2)
    count = Column(Integer, nullable=False)
    base_rate = Column(Float, nullable=False)
    description = Column(String)
    amenities = Column(JSON)
    floor_rate = Column(Float)
    ceiling_rate = Column(Float)
    rate_multiplier = Column(Float, default=1.0)

    property = relationship("Property", back_populates="room_types")
    bookings = relationship("Booking", back_populates="room_type")
