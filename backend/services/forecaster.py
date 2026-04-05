"""
Demand forecasting using Facebook Prophet (Section 6.1).

Trains on daily_occupancy from SQLite; optional weather regressor from external_signals.
"""

from __future__ import annotations

import warnings
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
import pandas as pd
from prophet import Prophet
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.booking import DailyOccupancy
from models.property import SeasonType
from models.signal import ExternalSignal

# Suppress Stan/changepoint noise in logs for prototype
warnings.filterwarnings("ignore", category=FutureWarning)


def _croatian_holidays_df(years: range) -> pd.DataFrame:
    """Build Prophet holidays DataFrame using Croatian public holidays."""
    import holidays as holidays_lib

    rows: list[dict[str, Any]] = []
    yr_list = list(years)
    hr = holidays_lib.country_holidays("HR", years=yr_list)
    for d, name in sorted(hr.items()):
        rows.append(
            {
                "holiday": str(name)[:80],
                "ds": pd.Timestamp(d),
                "lower_window": 0,
                "upper_window": 1,
            }
        )
    return pd.DataFrame(rows)


def _german_school_holidays_df(years: range) -> pd.DataFrame:
    """Approximate German school-holiday windows (largest source market)."""
    rows: list[dict[str, Any]] = []
    for y in years:
        rows.extend(
            [
                {"holiday": "DE_Summer_Bavaria", "ds": f"{y}-07-27", "lower_window": 0, "upper_window": 42},
                {"holiday": "DE_Summer_NRW", "ds": f"{y}-07-06", "lower_window": 0, "upper_window": 42},
                {"holiday": "DE_Summer_Berlin", "ds": f"{y}-07-09", "lower_window": 0, "upper_window": 42},
                {"holiday": "DE_Autumn", "ds": f"{y}-10-19", "lower_window": 0, "upper_window": 14},
            ]
        )
    df = pd.DataFrame(rows)
    df["ds"] = pd.to_datetime(df["ds"])
    return df


def _get_combined_holidays(years: range) -> pd.DataFrame:
    ch = _croatian_holidays_df(years)
    de = _german_school_holidays_df(years)
    return pd.concat([ch, de], ignore_index=True)


def _season_from_month(month: int) -> str:
    if month in (7, 8):
        return SeasonType.PEAK.value
    if month in (6, 9):
        return SeasonType.HIGH.value
    if month in (4, 5, 10):
        return SeasonType.SHOULDER.value
    return SeasonType.LOW.value


def load_daily_series(
    db: Session,
    property_id: int,
    value_column: str,
) -> pd.DataFrame:
    """Load training series: columns ds (datetime), y (float)."""
    stmt = (
        select(DailyOccupancy)
        .where(DailyOccupancy.property_id == property_id)
        .order_by(DailyOccupancy.date)
    )
    rows = db.scalars(stmt).all()
    if not rows:
        return pd.DataFrame(columns=["ds", "y"])

    data: list[dict[str, Any]] = []
    for r in rows:
        d = r.date
        if hasattr(d, "replace"):
            d = d.replace(tzinfo=None) if d.tzinfo else d
        val = getattr(r, value_column, None)
        if val is None:
            continue
        data.append({"ds": pd.Timestamp(d).normalize(), "y": float(val)})

    return pd.DataFrame(data)


def load_weather_regressor(db: Session, property_id: int) -> pd.DataFrame:
    """Daily weather_score for regressors (aligned to ds)."""
    stmt = (
        select(ExternalSignal)
        .where(
            ExternalSignal.property_id == property_id,
            ExternalSignal.signal_type == "weather",
        )
        .order_by(ExternalSignal.date)
    )
    sigs = db.scalars(stmt).all()
    rows = []
    for s in sigs:
        d = s.date
        if hasattr(d, "replace"):
            d = d.replace(tzinfo=None) if d.tzinfo else d
        score = s.weather_score if s.weather_score is not None else 50.0
        rows.append({"ds": pd.Timestamp(d).normalize(), "weather_score": float(score)})
    return pd.DataFrame(rows)


def load_signal_frame(
    db: Session,
    property_id: int,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    """Weather, flight, event rows merged on ds for demand scoring."""
    stmt = select(ExternalSignal).where(ExternalSignal.property_id == property_id).order_by(ExternalSignal.date)
    sigs = db.scalars(stmt).all()
    weather: dict[pd.Timestamp, float] = {}
    flight: dict[pd.Timestamp, float] = {}
    event_impact: dict[pd.Timestamp, float] = {}

    for s in sigs:
        d = s.date
        if hasattr(d, "replace"):
            d = d.replace(tzinfo=None) if d.tzinfo else d
        ts = pd.Timestamp(d).normalize()
        if ts < start or ts > end:
            continue
        if s.signal_type == "weather" and s.weather_score is not None:
            weather[ts] = float(s.weather_score)
        elif s.signal_type == "flight" and s.flight_arrivals is not None:
            flight[ts] = min(100.0, float(s.flight_arrivals) / 250.0 * 100.0)
        elif s.signal_type == "event" and s.event_impact_score is not None:
            event_impact[ts] = float(s.event_impact_score)

    all_ts = sorted(set(weather) | set(flight) | set(event_impact))
    rows = []
    for ts in all_ts:
        rows.append(
            {
                "ds": ts,
                "weather_score": weather.get(ts, np.nan),
                "flight_index": flight.get(ts, np.nan),
                "event_impact": event_impact.get(ts, np.nan),
            }
        )
    return pd.DataFrame(rows)


class DemandForecaster:
    """
    Prophet-based occupancy, ADR, and RevPAR forecasts with 80% intervals.
    Models cached per property and target until refresh.
    """

    def __init__(self) -> None:
        self.models: dict[str, Prophet] = {}
        self._last_train_cutoff: dict[str, pd.Timestamp] = {}

    def clear_cache(self, property_id: int | None = None) -> None:
        if property_id is None:
            self.models.clear()
            self._last_train_cutoff.clear()
            return
        keys = [k for k in self.models if k.endswith(f"_{property_id}")]
        for k in keys:
            del self.models[k]
            self._last_train_cutoff.pop(k, None)

    def forecast_occupancy(
        self,
        property_id: int,
        historical_data: pd.DataFrame,
        horizon_days: int = 30,
        external_signals: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        if historical_data.empty or len(historical_data) < 14:
            return pd.DataFrame(columns=["ds", "yhat", "yhat_lower", "yhat_upper"])

        hist = historical_data[["ds", "y"]].copy()
        years = range(int(hist["ds"].dt.year.min()), int(hist["ds"].dt.year.max()) + 2)
        holidays_df = _get_combined_holidays(years)

        use_weather = (
            external_signals is not None
            and not external_signals.empty
            and "weather_score" in external_signals.columns
        )
        if use_weather:
            hist = hist.merge(external_signals[["ds", "weather_score"]], on="ds", how="left")
            med = hist["weather_score"].median()
            hist["weather_score"] = hist["weather_score"].fillna(med if pd.notna(med) else 50.0)

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.80,
            uncertainty_samples=1000,
            holidays=holidays_df,
        )
        model.add_seasonality(name="summer_peak", period=365.25, fourier_order=8)
        if use_weather:
            model.add_regressor("weather_score", standardize=True)

        model.fit(hist)

        key = f"occ_{property_id}"
        self.models[key] = model
        self._last_train_cutoff[key] = hist["ds"].max()

        future = model.make_future_dataframe(periods=horizon_days, freq="D")
        if use_weather:
            mean_w = float(hist["weather_score"].mean())
            future = future.merge(external_signals[["ds", "weather_score"]], on="ds", how="left")
            future["weather_score"] = future["weather_score"].fillna(mean_w)

        forecast = model.predict(future)
        for c in ("yhat", "yhat_lower", "yhat_upper"):
            forecast[c] = forecast[c].clip(0.0, 1.0)

        cutoff = hist["ds"].max()
        return forecast[forecast["ds"] > cutoff][["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

    def forecast_value(
        self,
        property_id: int,
        key_prefix: str,
        historical_data: pd.DataFrame,
        horizon_days: int,
        y_clip: tuple[float, float],
    ) -> pd.DataFrame:
        if historical_data.empty or len(historical_data) < 14:
            return pd.DataFrame(columns=["ds", "yhat", "yhat_lower", "yhat_upper"])

        years = range(int(historical_data["ds"].dt.year.min()), int(historical_data["ds"].dt.year.max()) + 2)
        holidays_df = _get_combined_holidays(years)

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.1,
            seasonality_prior_scale=5.0,
            interval_width=0.80,
            uncertainty_samples=1000,
            holidays=holidays_df,
        )
        model.fit(historical_data[["ds", "y"]])

        key = f"{key_prefix}_{property_id}"
        self.models[key] = model
        self._last_train_cutoff[key] = historical_data["ds"].max()

        future = model.make_future_dataframe(periods=horizon_days, freq="D")
        forecast = model.predict(future)
        for c in ("yhat", "yhat_lower", "yhat_upper"):
            forecast[c] = forecast[c].clip(y_clip[0], y_clip[1])

        cutoff = historical_data["ds"].max()
        return forecast[forecast["ds"] > cutoff][["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

    def forecast_adr(
        self,
        property_id: int,
        historical_data: pd.DataFrame,
        horizon_days: int = 30,
    ) -> pd.DataFrame:
        return self.forecast_value(property_id, "adr", historical_data, horizon_days, (30.0, 1000.0))

    def forecast_revpar(
        self,
        property_id: int,
        historical_data: pd.DataFrame,
        horizon_days: int = 30,
    ) -> pd.DataFrame:
        return self.forecast_value(property_id, "revpar", historical_data, horizon_days, (0.0, 5000.0))

    def get_decomposition(self, property_id: int, forecast_type: str = "occ") -> dict[str, Any]:
        key = f"{forecast_type}_{property_id}"
        model = self.models.get(key)
        if model is None:
            return {}
        future = model.make_future_dataframe(periods=30, freq="D")
        forecast = model.predict(future)
        out: dict[str, Any] = {
            "trend": forecast[["ds", "trend"]].to_dict("records"),
            "yearly": forecast[["ds", "yearly"]].to_dict("records") if "yearly" in forecast.columns else [],
            "weekly": forecast[["ds", "weekly"]].to_dict("records") if "weekly" in forecast.columns else [],
        }
        if "holidays" in forecast.columns:
            out["holidays"] = forecast[["ds", "holidays"]].to_dict("records")
        return out


def estimate_model_confidence(horizon_days: int, n_train: int) -> float:
    """Heuristic confidence 0–1 from data size and horizon."""
    base = min(0.95, 0.65 + min(n_train, 1000) / 4000.0)
    horizon_penalty = min(0.1, horizon_days / 300.0)
    return round(max(0.5, base - horizon_penalty), 3)


forecaster = DemandForecaster()


def run_occupancy_forecast(
    db: Session,
    property_id: int,
    horizon_days: int = 30,
) -> tuple[pd.DataFrame, float]:
    hist = load_daily_series(db, property_id, "occupancy_pct")
    weather = load_weather_regressor(db, property_id)
    ext = None if weather.empty else weather
    df = forecaster.forecast_occupancy(property_id, hist, horizon_days, ext)
    conf = estimate_model_confidence(horizon_days, len(hist))
    return df, conf


def run_adr_forecast(db: Session, property_id: int, horizon_days: int = 30) -> tuple[pd.DataFrame, float]:
    hist = load_daily_series(db, property_id, "adr")
    df = forecaster.forecast_adr(property_id, hist, horizon_days)
    conf = estimate_model_confidence(horizon_days, len(hist))
    return df, conf


def run_revpar_forecast(db: Session, property_id: int, horizon_days: int = 30) -> tuple[pd.DataFrame, float]:
    hist = load_daily_series(db, property_id, "revpar")
    df = forecaster.forecast_revpar(property_id, hist, horizon_days)
    conf = estimate_model_confidence(horizon_days, len(hist))
    return df, conf


def build_demand_forecast(
    db: Session,
    property_id: int,
    occ_df: pd.DataFrame,
    horizon_days: int,
) -> pd.DataFrame:
    """Merge occupancy forecast with signals into composite demand_score 0–100."""
    if occ_df.empty:
        return pd.DataFrame()

    start = pd.Timestamp(occ_df["ds"].min()).normalize()
    end = pd.Timestamp(occ_df["ds"].max()).normalize()
    sig = load_signal_frame(db, property_id, start, end)
    if not sig.empty:
        sig = sig.copy()
        sig["_dsn"] = pd.to_datetime(sig["ds"]).dt.normalize()

    rows = []
    for _, row in occ_df.iterrows():
        ds = row["ds"]
        occ = float(row["yhat"])
        ds_norm = pd.Timestamp(ds).normalize()
        if not sig.empty:
            m = sig[sig["_dsn"] == ds_norm]
        else:
            m = pd.DataFrame()
        w = float(m["weather_score"].iloc[0]) if not m.empty and pd.notna(m["weather_score"].iloc[0]) else 55.0
        f_idx = float(m["flight_index"].iloc[0]) if not m.empty and pd.notna(m["flight_index"].iloc[0]) else 50.0
        ev = float(m["event_impact"].iloc[0]) if not m.empty and pd.notna(m["event_impact"].iloc[0]) else 0.0

        demand = 0.45 * (occ * 100.0) + 0.22 * w + 0.23 * f_idx + 0.10 * ev
        demand = float(np.clip(demand, 0.0, 100.0))

        month = int(pd.Timestamp(ds).month)
        rows.append(
            {
                "ds": ds,
                "demand_score": demand,
                "occupancy_forecast": occ,
                "weather_score": w,
                "flight_index": f_idx,
                "event_impact": ev,
                "season": _season_from_month(month),
            }
        )
    return pd.DataFrame(rows)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
