"""
Generate 3 years of synthetic hotel data for a 200-room Dubrovnik hotel.

Implements Section 7 of the TouristFlow technical spec: daily occupancy,
bookings, competitors, weather, flights, and Croatian event catalog.
"""

from __future__ import annotations

import os
import random
import uuid
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from database import SessionLocal, init_db
from models.booking import Booking, BookingSource, BookingStatus, DailyOccupancy
from models.property import Property, PropertyType, RoomType, SeasonType
from models.signal import Competitor, CompetitorRate, ExternalSignal

# ─── HOTEL CONFIGURATION ─────────────────────────────────
PROPERTY = {
    "name": "Hotel Adriatic Palace",
    "chain": None,
    "type": "resort",
    "stars": 4,
    "city": "Dubrovnik",
    "region": "Dalmatia",
    "total_rooms": 200,
    "lat": 42.6507,
    "lng": 18.0944,
    "min_rate": 60,
    "max_rate": 450,
    "target_occupancy": 0.80,
}

ROOM_TYPES = [
    {
        "name": "Standard Double",
        "code": "STD_DBL",
        "count": 80,
        "base_rate": 100,
        "multiplier": 1.0,
        "floor": 60,
        "ceiling": 250,
        "amenities": ["wifi", "ac", "minibar"],
    },
    {
        "name": "Superior Double Sea View",
        "code": "SUP_DBL_SV",
        "count": 50,
        "base_rate": 140,
        "multiplier": 1.4,
        "floor": 80,
        "ceiling": 350,
        "amenities": ["wifi", "ac", "minibar", "sea_view", "balcony"],
    },
    {
        "name": "Deluxe Suite",
        "code": "DLX_SUITE",
        "count": 30,
        "base_rate": 220,
        "multiplier": 2.2,
        "floor": 120,
        "ceiling": 450,
        "amenities": ["wifi", "ac", "minibar", "sea_view", "balcony", "living_room"],
    },
    {
        "name": "Family Room",
        "code": "FAM_RM",
        "count": 25,
        "base_rate": 160,
        "multiplier": 1.6,
        "floor": 90,
        "ceiling": 320,
        "amenities": ["wifi", "ac", "minibar", "extra_bed", "kids_corner"],
    },
    {
        "name": "Economy Single",
        "code": "ECO_SGL",
        "count": 15,
        "base_rate": 70,
        "multiplier": 0.7,
        "floor": 45,
        "ceiling": 180,
        "amenities": ["wifi", "ac"],
    },
]

COMPETITORS = [
    {"name": "Hotel Dubrovnik Palace", "stars": 5, "rooms": 308, "rate_premium": 1.35, "is_primary": True},
    {"name": "Hotel Excelsior", "stars": 5, "rooms": 158, "rate_premium": 1.50, "is_primary": True},
    {"name": "Hotel Kompas", "stars": 4, "rooms": 173, "rate_premium": 0.95, "is_primary": True},
    {"name": "Rixos Premium", "stars": 5, "rooms": 323, "rate_premium": 1.60, "is_primary": True},
    {"name": "Hotel Lero", "stars": 4, "rooms": 155, "rate_premium": 0.80, "is_primary": False},
    {"name": "Hotel Lapad", "stars": 4, "rooms": 163, "rate_premium": 0.70, "is_primary": False},
]

EVENTS_HR = [
    {"name": "Dubrovnik Summer Festival", "region": "Dubrovnik", "start": "07-10", "end": "08-25", "type": "cultural", "impact": 30, "attendees": 50000},
    {"name": "Ultra Europe", "region": "Split", "start": "07-11", "end": "07-13", "type": "festival", "impact": 45, "attendees": 150000},
    {"name": "Outlook Festival", "region": "Pula", "start": "08-06", "end": "08-10", "type": "festival", "impact": 25, "attendees": 30000},
    {"name": "Advent u Zagrebu", "region": "Zagreb", "start": "11-29", "end": "12-31", "type": "cultural", "impact": 20, "attendees": 1000000},
    {"name": "INmusic Festival", "region": "Zagreb", "start": "06-22", "end": "06-24", "type": "festival", "impact": 15, "attendees": 50000},
    {"name": "Dubrovnik Wine Festival", "region": "Dubrovnik", "start": "04-18", "end": "04-20", "type": "food", "impact": 55, "attendees": 5000},
    {"name": "Pula Film Festival", "region": "Pula", "start": "07-14", "end": "07-22", "type": "cultural", "impact": 12, "attendees": 30000},
    {"name": "Easter Weekend", "region": "all", "start": "04-03", "end": "04-06", "type": "holiday", "impact": 20, "attendees": 0},
    {"name": "Sinjska Alka", "region": "Split", "start": "08-03", "end": "08-03", "type": "cultural", "impact": 8, "attendees": 10000},
]

SOURCE_COUNTRIES = {
    "DE": 0.22,
    "HR": 0.15,
    "GB": 0.12,
    "FR": 0.08,
    "US": 0.07,
    "IT": 0.06,
    "AT": 0.05,
    "PL": 0.04,
    "CZ": 0.04,
    "NL": 0.03,
    "SE": 0.03,
    "KR": 0.02,
    "Other": 0.09,
}

BOOKING_SOURCES = {
    "booking_com": 0.35,
    "direct": 0.25,
    "expedia": 0.12,
    "travel_agent": 0.10,
    "corporate": 0.08,
    "group": 0.05,
    "airbnb": 0.03,
    "walk_in": 0.02,
}

_SOURCE_ENUM = {
    "booking_com": BookingSource.BOOKING_COM,
    "direct": BookingSource.DIRECT,
    "expedia": BookingSource.EXPEDIA,
    "travel_agent": BookingSource.TRAVEL_AGENT,
    "corporate": BookingSource.CORPORATE,
    "group": BookingSource.GROUP,
    "airbnb": BookingSource.AIRBNB,
    "walk_in": BookingSource.WALK_IN,
}


def _normalize_mix(d: dict[str, float]) -> dict[str, float]:
    vals = {k: max(0.0, float(v)) for k, v in d.items()}
    s = sum(vals.values())
    if s <= 0:
        n = len(vals)
        return {k: round(1.0 / n, 4) for k in vals}
    return {k: round(v / s, 4) for k, v in vals.items()}


def _get_season(month: int) -> SeasonType:
    if month in (7, 8):
        return SeasonType.PEAK
    if month in (6, 9):
        return SeasonType.HIGH
    if month in (4, 5, 10):
        return SeasonType.SHOULDER
    return SeasonType.LOW


def _season_str_to_enum(s: str) -> SeasonType:
    return SeasonType(s)


def generate_daily_occupancy(
    start_date: datetime,
    end_date: datetime,
) -> pd.DataFrame:
    """Generate realistic daily occupancy for a Dubrovnik 4★ hotel."""
    dates = pd.date_range(start_date, end_date, freq="D")
    records = []

    for date in dates:
        month = int(date.month)
        dow = int(date.dayofweek)

        monthly_base = {
            1: 0.18,
            2: 0.20,
            3: 0.30,
            4: 0.45,
            5: 0.60,
            6: 0.80,
            7: 0.93,
            8: 0.95,
            9: 0.75,
            10: 0.50,
            11: 0.25,
            12: 0.22,
        }
        base_occ = monthly_base[month]

        day_in_month = int(date.day)
        if month in (6, 7):
            base_occ += (day_in_month / 30) * 0.08
        elif month in (8, 9):
            base_occ -= (day_in_month / 30) * 0.08

        if dow in (4, 5):
            base_occ += 0.06
        elif dow == 6:
            base_occ += 0.02
        elif dow == 0:
            base_occ -= 0.03

        years_from_start = (date.to_pydatetime().replace(tzinfo=None) - start_date).days / 365.25
        growth = years_from_start * 0.025
        base_occ += growth

        for event in EVENTS_HR:
            if event["region"] in ("Dubrovnik", "all"):
                ev_start = datetime.strptime(f"{date.year}-{event['start']}", "%Y-%m-%d")
                ev_end = datetime.strptime(f"{date.year}-{event['end']}", "%Y-%m-%d")
                d = date.to_pydatetime().replace(tzinfo=None)
                if ev_start <= d <= ev_end:
                    base_occ += event["impact"] / 100
                elif ev_start - timedelta(days=3) <= d < ev_start:
                    base_occ += (event["impact"] / 100) * 0.3

        # Regional spillover (Split/Zagreb/Pula) — smaller effect on Dubrovnik
        d = date.to_pydatetime().replace(tzinfo=None)
        for event in EVENTS_HR:
            if event["region"] not in ("Dubrovnik", "all"):
                ev_start = datetime.strptime(f"{date.year}-{event['start']}", "%Y-%m-%d")
                ev_end = datetime.strptime(f"{date.year}-{event['end']}", "%Y-%m-%d")
                if ev_start <= d <= ev_end:
                    base_occ += (event["impact"] / 100) * 0.08

        # COVID recovery tail (early 2023)
        if d.year == 2023 and d.month <= 3:
            base_occ -= 0.04

        if random.random() < 0.12:
            if month in (6, 7, 8, 9):
                base_occ -= random.uniform(0.03, 0.08)

        noise = random.gauss(0, 0.04)
        base_occ += noise

        occupancy = max(0.05, min(0.98, base_occ))

        base_adr = ROOM_TYPES[0]["base_rate"]
        adr_seasonal = {
            1: 0.55,
            2: 0.55,
            3: 0.65,
            4: 0.80,
            5: 0.90,
            6: 1.10,
            7: 1.45,
            8: 1.50,
            9: 1.05,
            10: 0.80,
            11: 0.60,
            12: 0.60,
        }
        adr = base_adr * adr_seasonal[month]
        adr += random.gauss(0, 5)
        adr = max(PROPERTY["min_rate"], min(PROPERTY["max_rate"], adr))

        revpar = occupancy * adr
        rooms_sold = int(round(occupancy * PROPERTY["total_rooms"]))
        total_revenue = rooms_sold * adr

        source_mix = _normalize_mix({k: v + random.gauss(0, 0.03) for k, v in BOOKING_SOURCES.items()})
        guest_mix = _normalize_mix({k: v + random.gauss(0, 0.02) for k, v in SOURCE_COUNTRIES.items()})

        season_str = _get_season(month).value

        records.append(
            {
                "date": date,
                "occupancy": round(occupancy, 4),
                "adr": round(adr, 2),
                "revpar": round(revpar, 2),
                "rooms_available": PROPERTY["total_rooms"],
                "rooms_sold": rooms_sold,
                "total_revenue": round(total_revenue, 2),
                "day_of_week": dow,
                "month": month,
                "is_weekend": dow >= 4,
                "season": season_str,
                "source_mix": source_mix,
                "guest_country_mix": guest_mix,
            }
        )

    return pd.DataFrame(records)


def generate_competitor_rates(daily_data: pd.DataFrame) -> list[dict]:
    """Generate competitor rates based on our hotel's pricing + premium/discount."""
    rates = []
    for _, row in daily_data.iterrows():
        for comp in COMPETITORS:
            rate = row["adr"] * comp["rate_premium"]
            rate += random.gauss(0, 8)
            rate = max(40, round(rate, 2))
            rates.append(
                {
                    "competitor_name": comp["name"],
                    "date": row["date"],
                    "rate": rate,
                    "available": random.random() > 0.15,
                }
            )
    return rates


def generate_weather_data(start_date: datetime, end_date: datetime, region: str = "Dubrovnik") -> list[dict]:
    """Generate realistic weather data for Croatian coast."""
    dates = pd.date_range(start_date, end_date, freq="D")
    weather = []

    monthly_temp = {
        1: (5, 12),
        2: (6, 13),
        3: (8, 15),
        4: (11, 19),
        5: (15, 23),
        6: (19, 28),
        7: (22, 31),
        8: (22, 31),
        9: (18, 27),
        10: (14, 22),
        11: (9, 17),
        12: (6, 13),
    }

    for date in dates:
        low_base, high_base = monthly_temp[int(date.month)]
        temp_high = high_base + random.gauss(0, 2)
        temp_low = low_base + random.gauss(0, 2)

        rain_prob = {
            1: 0.35,
            2: 0.35,
            3: 0.30,
            4: 0.25,
            5: 0.18,
            6: 0.10,
            7: 0.05,
            8: 0.05,
            9: 0.12,
            10: 0.25,
            11: 0.35,
            12: 0.38,
        }
        precip = 0.0
        if random.random() < rain_prob[int(date.month)]:
            precip = random.uniform(1, 25)

        weather_score = min(
            100,
            max(
                0,
                40 + temp_high * 1.5 - precip * 2 + (10 if int(date.month) in (6, 7, 8, 9) else 0),
            ),
        )

        weather.append(
            {
                "date": date,
                "region": region,
                "temperature_high": round(temp_high, 1),
                "temperature_low": round(temp_low, 1),
                "precipitation_mm": round(precip, 1),
                "weather_score": round(weather_score, 1),
            }
        )

    return weather


def generate_flight_data(start_date: datetime, end_date: datetime, airport: str = "DBV") -> list[dict]:
    """Generate synthetic flight arrival data for Dubrovnik airport."""
    dates = pd.date_range(start_date, end_date, freq="D")
    flights = []

    monthly_pax = {
        1: 200,
        2: 250,
        3: 800,
        4: 3000,
        5: 8000,
        6: 15000,
        7: 22000,
        8: 23000,
        9: 14000,
        10: 6000,
        11: 500,
        12: 400,
    }

    for date in dates:
        base_pax = monthly_pax[int(date.month)]
        if int(date.dayofweek) in (4, 5, 6):
            base_pax *= 1.3

        pax = int(base_pax * random.uniform(0.8, 1.2))
        yoy_change = random.uniform(-0.05, 0.15)

        origins = [
            {"country": "DE", "pax": int(pax * 0.20)},
            {"country": "GB", "pax": int(pax * 0.18)},
            {"country": "FR", "pax": int(pax * 0.10)},
            {"country": "HR", "pax": int(pax * 0.08)},
            {"country": "US", "pax": int(pax * 0.07)},
        ]

        flights.append(
            {
                "date": date,
                "airport": airport,
                "arrivals": pax,
                "yoy_change": round(yoy_change, 3),
                "top_origins": origins,
            }
        )

    return flights


def generate_bookings_from_occupancy(
    daily_data: pd.DataFrame,
    room_types: list[dict],
) -> list[dict]:
    """Generate individual booking records from daily occupancy aggregates."""
    bookings = []
    booking_id = 1

    for _, day in daily_data.iterrows():
        rooms_to_fill = int(day["rooms_sold"])
        date = day["date"]
        if hasattr(date, "to_pydatetime"):
            date = date.to_pydatetime()
        if date.tzinfo is not None:
            date = date.replace(tzinfo=None)
        date = date.replace(hour=15, minute=0, second=0, microsecond=0)

        filled = 0
        while filled < rooms_to_fill:
            rt = random.choices(room_types, weights=[r["count"] for r in room_types], k=1)[0]

            if day["season"] in ("peak", "high"):
                los = max(1, int(random.gauss(4.5, 2.0)))
            else:
                los = max(1, int(random.gauss(2.0, 1.0)))
            los = min(los, 14)

            if day["season"] == "peak":
                lead_time = max(0, int(random.gauss(45, 25)))
            elif day["season"] == "high":
                lead_time = max(0, int(random.gauss(30, 20)))
            else:
                lead_time = max(0, int(random.gauss(14, 10)))

            rate = day["adr"] * rt["multiplier"]
            rate += random.gauss(0, rate * 0.05)
            rate = max(rt["floor"], min(rt["ceiling"], round(rate, 2)))

            source = random.choices(list(BOOKING_SOURCES.keys()), weights=list(BOOKING_SOURCES.values()), k=1)[0]
            country = random.choices(list(SOURCE_COUNTRIES.keys()), weights=list(SOURCE_COUNTRIES.values()), k=1)[0]

            cancel_prob = 0.12 if source == "booking_com" else 0.06
            if random.random() < cancel_prob:
                status = "cancelled"
            else:
                status = "confirmed"

            bookings.append(
                {
                    "id": booking_id,
                    "room_type": rt["code"],
                    "check_in": date,
                    "check_out": date + timedelta(days=los),
                    "nights": los,
                    "rate_per_night": rate,
                    "total_revenue": round(rate * los, 2),
                    "source": source,
                    "guest_country": country,
                    "lead_time_days": lead_time,
                    "booking_date": date - timedelta(days=lead_time),
                    "status": status,
                    "guests": random.choice([1, 2, 2, 2, 3, 4]),
                    "is_repeat": random.random() < 0.15,
                }
            )

            booking_id += 1
            filled += 1

    return bookings


def _event_for_date(d: datetime) -> dict | None:
    """Return primary Dubrovnik/all-region event for signal row if any."""
    best = None
    for event in EVENTS_HR:
        if event["region"] not in ("Dubrovnik", "all"):
            continue
        ev_start = datetime.strptime(f"{d.year}-{event['start']}", "%Y-%m-%d")
        ev_end = datetime.strptime(f"{d.year}-{event['end']}", "%Y-%m-%d")
        if ev_start <= d <= ev_end:
            if best is None or event["impact"] > best["impact"]:
                best = event
    return best


def _apply_demo_april_2026_signals(db: Session, property_id: int) -> None:
    """Apr 6, 2026: warm spring weather + strong German flight YoY for demo narrative."""
    from datetime import date as ddate

    d_apr6 = ddate(2026, 4, 6)
    db.execute(
        update(ExternalSignal)
        .where(
            ExternalSignal.property_id == property_id,
            ExternalSignal.signal_type == "weather",
            func.date(ExternalSignal.date) == d_apr6,
        )
        .values(
            weather_score=84.0,
            temperature_high=21.0,
            temperature_low=14.0,
            precipitation_mm=0.0,
        )
    )
    db.execute(
        update(ExternalSignal)
        .where(
            ExternalSignal.property_id == property_id,
            ExternalSignal.signal_type == "flight",
            func.date(ExternalSignal.date) == d_apr6,
        )
        .values(
            flight_yoy_change=0.15,
            flight_arrivals=4200,
            top_origin_countries=[
                {"country": "DE", "pax": 1240},
                {"country": "GB", "pax": 890},
                {"country": "FR", "pax": 520},
            ],
        )
    )


def _apply_demo_competitor_lag(db: Session, property_id: int) -> None:
    """Wine Festival window: comp set BAR slightly stale vs TouristFlow lift."""
    from datetime import date as ddate

    stmt = (
        select(CompetitorRate)
        .join(Competitor, CompetitorRate.competitor_id == Competitor.id)
        .where(
            Competitor.property_id == property_id,
            func.date(CompetitorRate.date) >= ddate(2026, 4, 18),
            func.date(CompetitorRate.date) <= ddate(2026, 4, 20),
        )
    )
    for r in db.scalars(stmt).all():
        r.rate = round(float(r.rate) * 0.94, 2)


def seed_database(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> None:
    """Create property, 3 years of daily data, bookings, signals, competitors."""
    random.seed(42)
    np.random.seed(42)

    if start_date is None:
        start_date = datetime(2023, 1, 1)
    if end_date is None:
        end_date = datetime(2026, 12, 31)

    prop = Property(
        name=PROPERTY["name"],
        chain=PROPERTY["chain"],
        property_type=PropertyType.RESORT,
        stars=PROPERTY["stars"],
        city=PROPERTY["city"],
        region=PROPERTY["region"],
        latitude=PROPERTY["lat"],
        longitude=PROPERTY["lng"],
        total_rooms=PROPERTY["total_rooms"],
        address="Ul. Kardinala Stepinca 21",
        currency="EUR",
        min_rate=float(PROPERTY["min_rate"]),
        max_rate=float(PROPERTY["max_rate"]),
        target_occupancy=PROPERTY["target_occupancy"],
    )
    db.add(prop)
    db.flush()

    code_to_room: dict[str, RoomType] = {}
    for rt in ROOM_TYPES:
        row = RoomType(
            property_id=prop.id,
            name=rt["name"],
            code=rt["code"],
            capacity=2,
            count=rt["count"],
            base_rate=float(rt["base_rate"]),
            amenities=rt["amenities"],
            floor_rate=float(rt["floor"]),
            ceiling_rate=float(rt["ceiling"]),
            rate_multiplier=float(rt["multiplier"]),
        )
        db.add(row)
        db.flush()
        code_to_room[rt["code"]] = row

    for c in COMPETITORS:
        db.add(
            Competitor(
                property_id=prop.id,
                competitor_name=c["name"],
                competitor_stars=c["stars"],
                competitor_rooms=c["rooms"],
                is_primary=c["is_primary"],
            )
        )
    db.flush()

    competitors = db.scalars(select(Competitor).where(Competitor.property_id == prop.id)).all()
    name_to_comp: dict[str, Competitor] = {c.competitor_name: c for c in competitors}

    daily_df = generate_daily_occupancy(start_date, end_date)

    occ_maps: list[dict] = []
    for _, row in daily_df.iterrows():
        d = row["date"]
        if hasattr(d, "to_pydatetime"):
            d = d.to_pydatetime()
        d = d.replace(hour=0, minute=0, second=0, microsecond=0)
        occ = float(row["occupancy"])
        rooms_avail = int(row["rooms_available"])
        rooms_sold = int(row["rooms_sold"])
        season_enum = _season_str_to_enum(str(row["season"]))

        bookings_recv = max(0, int(random.gauss(rooms_sold * 0.4, rooms_sold * 0.15)))
        cancellations = max(0, int(random.gauss(rooms_sold * 0.08, rooms_sold * 0.03)))
        avg_lead = 45.0 if season_enum == SeasonType.PEAK else 28.0 if season_enum == SeasonType.HIGH else 14.0
        avg_lead += random.gauss(0, 8)

        occ_maps.append(
            {
                "property_id": prop.id,
                "date": d,
                "rooms_available": rooms_avail,
                "rooms_sold": rooms_sold,
                "rooms_remaining": max(0, rooms_avail - rooms_sold),
                "occupancy_pct": occ,
                "adr": float(row["adr"]),
                "revpar": float(row["revpar"]),
                "total_revenue": float(row["total_revenue"]),
                "bookings_received": bookings_recv,
                "cancellations": cancellations,
                "avg_lead_time": round(avg_lead, 1),
                "source_mix": row["source_mix"],
                "guest_country_mix": row["guest_country_mix"],
                "day_of_week": int(row["day_of_week"]),
                "month": int(row["month"]),
                "is_weekend": bool(row["is_weekend"]),
                "season": season_enum,
            }
        )
    db.bulk_insert_mappings(DailyOccupancy, occ_maps)

    booking_rows = generate_bookings_from_occupancy(daily_df, ROOM_TYPES)
    booking_maps: list[dict] = []
    for b in booking_rows:
        rt = code_to_room[b["room_type"]]
        st = BookingStatus.CANCELLED if b["status"] == "cancelled" else BookingStatus.CONFIRMED
        booking_maps.append(
            {
                "property_id": prop.id,
                "room_type_id": rt.id,
                "booking_ref": f"BK-{b['id']:09d}-{uuid.uuid4().hex[:8].upper()}",
                "guest_country": b["guest_country"],
                "check_in": b["check_in"],
                "check_out": b["check_out"],
                "nights": b["nights"],
                "rooms_booked": 1,
                "guests": b["guests"],
                "rate_per_night": b["rate_per_night"],
                "total_revenue": b["total_revenue"],
                "source": _SOURCE_ENUM[b["source"]],
                "status": st,
                "booking_date": b["booking_date"],
                "lead_time_days": b["lead_time_days"],
                "cancellation_date": b["booking_date"] if st == BookingStatus.CANCELLED else None,
                "is_repeat_guest": b["is_repeat"],
            }
        )
    _chunk = 10_000
    for i in range(0, len(booking_maps), _chunk):
        db.bulk_insert_mappings(Booking, booking_maps[i : i + _chunk])

    weather_maps: list[dict] = []
    for w in generate_weather_data(start_date, end_date):
        dt = w["date"]
        if hasattr(dt, "to_pydatetime"):
            dt = dt.to_pydatetime()
        dt = dt.replace(hour=12, minute=0, second=0, microsecond=0)
        weather_maps.append(
            {
                "property_id": prop.id,
                "signal_type": "weather",
                "date": dt,
                "region": w["region"],
                "temperature_high": w["temperature_high"],
                "temperature_low": w["temperature_low"],
                "precipitation_mm": w["precipitation_mm"],
                "weather_score": w["weather_score"],
            }
        )
    db.bulk_insert_mappings(ExternalSignal, weather_maps)

    flight_maps: list[dict] = []
    for f in generate_flight_data(start_date, end_date):
        dt = f["date"]
        if hasattr(dt, "to_pydatetime"):
            dt = dt.to_pydatetime()
        dt = dt.replace(hour=12, minute=0, second=0, microsecond=0)
        flight_maps.append(
            {
                "property_id": prop.id,
                "signal_type": "flight",
                "date": dt,
                "region": "Dubrovnik",
                "flight_arrivals": f["arrivals"],
                "flight_yoy_change": f["yoy_change"],
                "top_origin_countries": f["top_origins"],
            }
        )
    db.bulk_insert_mappings(ExternalSignal, flight_maps)

    event_maps: list[dict] = []
    d0 = start_date
    while d0 <= end_date:
        ev = _event_for_date(d0)
        if ev:
            event_maps.append(
                {
                    "property_id": prop.id,
                    "signal_type": "event",
                    "date": d0.replace(hour=12, minute=0, second=0),
                    "region": "Dubrovnik",
                    "event_name": ev["name"],
                    "event_type": ev["type"],
                    "event_impact_score": float(ev["impact"]),
                    "event_attendees": ev["attendees"],
                }
            )
        d0 += timedelta(days=1)
    if event_maps:
        db.bulk_insert_mappings(ExternalSignal, event_maps)

    rate_maps: list[dict] = []
    for r in generate_competitor_rates(daily_df):
        comp = name_to_comp[r["competitor_name"]]
        dt = r["date"]
        if hasattr(dt, "to_pydatetime"):
            dt = dt.to_pydatetime()
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        rate_maps.append(
            {
                "competitor_id": comp.id,
                "date": dt,
                "room_type": "standard_double",
                "rate": float(r["rate"]),
                "source": "booking_com",
                "availability": bool(r["available"]),
                "scraped_at": datetime.now(timezone.utc),
            }
        )
    db.bulk_insert_mappings(CompetitorRate, rate_maps)

    _apply_demo_april_2026_signals(db, prop.id)
    _apply_demo_competitor_lag(db, prop.id)

    db.commit()


def _is_managed_host() -> bool:
    """True when running on a cloud host where we should not wipe SQLite every boot."""
    from config import settings

    if (settings.touristflow_managed_host or "").strip() == "1":
        return True
    return (
        os.environ.get("RENDER", "").lower() == "true"
        or os.environ.get("RAILWAY_PROJECT_ID") is not None
        or os.environ.get("FLY_APP_NAME") is not None
        or os.environ.get("K_SERVICE") is not None  # Google Cloud Run
        or os.environ.get("KOYEB_DEPLOYMENT_ID") is not None
        or os.environ.get("KOYEB_APP_NAME") is not None
    )


def main() -> None:
    """Populate SQLite.

    - **Local:** removes existing DB file each run (same as before), then seeds.
    - **Managed hosts** (Render, Railway, Koyeb, Fly, Cloud Run) or `TOURISTFLOW_MANAGED_HOST=1`:
      keeps the DB file; skips seed if data already exists unless `FORCE_RESEED=1`.
    """
    from config import settings

    managed = _is_managed_host()
    force = os.environ.get("FORCE_RESEED", "").strip() == "1"
    p = settings.sqlite_path

    if force and p is not None and p.exists():
        p.unlink()
    elif not managed and p is not None and p.exists():
        p.unlink()

    init_db()
    db = SessionLocal()
    try:
        if managed:
            n_existing = db.scalar(select(func.count()).select_from(DailyOccupancy)) or 0
            if n_existing > 0 and not force:
                print(
                    f"Database already seeded ({n_existing} daily rows); "
                    "skipping. Set FORCE_RESEED=1 to wipe and reseed."
                )
                return

        seed_database(db)
        n_occ = db.scalar(select(func.count()).select_from(DailyOccupancy)) or 0
        n_book = db.scalar(select(func.count()).select_from(Booking)) or 0
        print(f"Seeded SQLite: daily_occupancy={n_occ}, bookings={n_book}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
