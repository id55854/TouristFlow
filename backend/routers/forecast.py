"""Forecast API — Section 5."""

from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.property import Property
from routers.deps import get_property_or_404
from schemas.forecast import (
    AdrForecastResponse,
    DemandForecastResponse,
    DemandPoint,
    ForecastPoint,
    OccupancyForecastResponse,
    RefreshResponse,
    RevparForecastResponse,
)
from services.forecaster import (
    build_demand_forecast,
    forecaster,
    run_adr_forecast,
    run_occupancy_forecast,
    run_revpar_forecast,
)

router = APIRouter(prefix="/forecast", tags=["forecast"])


def _df_to_points(df: pd.DataFrame) -> list[ForecastPoint]:
    if df.empty:
        return []
    out: list[ForecastPoint] = []
    for _, row in df.iterrows():
        ds = row["ds"]
        if hasattr(ds, "date"):
            d = ds.date()
        else:
            d = pd.Timestamp(ds).date()
        out.append(
            ForecastPoint(
                date=d,
                predicted=float(row["yhat"]),
                lower_bound=float(row["yhat_lower"]),
                upper_bound=float(row["yhat_upper"]),
            )
        )
    return out


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/occupancy", response_model=OccupancyForecastResponse)
def forecast_occupancy(
    property_id: int = Query(..., description="Hotel / property id"),
    horizon: int = Query(30, ge=1, le=365, description="Days ahead"),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> OccupancyForecastResponse:
    df, conf = run_occupancy_forecast(db, property_id, horizon)
    return OccupancyForecastResponse(
        property_id=property_id,
        forecast_horizon=horizon,
        points=_df_to_points(df),
        model_confidence=conf,
        last_updated=_utc_now(),
    )


@router.get("/demand", response_model=DemandForecastResponse)
def forecast_demand(
    property_id: int = Query(...),
    horizon: int = Query(30, ge=1, le=365),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> DemandForecastResponse:
    occ_df, conf = run_occupancy_forecast(db, property_id, horizon)
    merged = build_demand_forecast(db, property_id, occ_df, horizon)
    points: list[DemandPoint] = []
    if not merged.empty:
        for _, row in merged.iterrows():
            ds = row["ds"]
            d = pd.Timestamp(ds).date() if not hasattr(ds, "date") else ds.date()
            points.append(
                DemandPoint(
                    date=d,
                    demand_score=float(row["demand_score"]),
                    occupancy_forecast=float(row["occupancy_forecast"]),
                    weather_score=float(row["weather_score"]),
                    flight_index=float(row["flight_index"]),
                    event_impact=float(row["event_impact"]),
                    search_trend=0.0,
                    season=str(row["season"]),
                )
            )
    return DemandForecastResponse(
        property_id=property_id,
        forecast_horizon=horizon,
        points=points,
        model_confidence=conf,
        last_updated=_utc_now(),
    )


@router.get("/adr", response_model=AdrForecastResponse)
def forecast_adr(
    property_id: int = Query(...),
    horizon: int = Query(30, ge=1, le=365),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> AdrForecastResponse:
    df, conf = run_adr_forecast(db, property_id, horizon)
    return AdrForecastResponse(
        property_id=property_id,
        forecast_horizon=horizon,
        points=_df_to_points(df),
        model_confidence=conf,
        last_updated=_utc_now(),
    )


@router.get("/revpar", response_model=RevparForecastResponse)
def forecast_revpar(
    property_id: int = Query(...),
    horizon: int = Query(30, ge=1, le=365),
    _: Property = Depends(get_property_or_404),
    db: Session = Depends(get_db),
) -> RevparForecastResponse:
    df, conf = run_revpar_forecast(db, property_id, horizon)
    return RevparForecastResponse(
        property_id=property_id,
        forecast_horizon=horizon,
        points=_df_to_points(df),
        model_confidence=conf,
        last_updated=_utc_now(),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh_forecast(
    property_id: int | None = Query(None, description="Clear cache for one property; omit for all"),
) -> RefreshResponse:
    forecaster.clear_cache(property_id)
    return RefreshResponse(
        property_id=property_id,
        status="ok",
        message="Forecast model cache cleared; next request will retrain Prophet.",
    )
