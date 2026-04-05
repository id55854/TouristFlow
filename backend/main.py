"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import analytics, competitors, forecast, insights, pricing, simulator

app = FastAPI(title="TouristFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(forecast.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(pricing.router, prefix="/api/v1")
app.include_router(simulator.router, prefix="/api/v1")
app.include_router(competitors.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
