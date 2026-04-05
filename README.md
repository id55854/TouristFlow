# TouristFlow

Hotel revenue dashboard (Next.js) + FastAPI backend with forecasting and pricing APIs.

## Repository

Remote: [github.com/id55854/TouristFlow](https://github.com/id55854/TouristFlow)

## Frontend (Vercel)

1. Import this repo in [Vercel](https://vercel.com/new).
2. Set **Root Directory** to `frontend`.
3. **Environment variables** (optional):
   - `NEXT_PUBLIC_API_URL` — URL of your deployed FastAPI backend (e.g. `https://api.example.com`). If unset, the app defaults to `http://localhost:8000`.
   - For the Dubrovnik demo story: `NEXT_PUBLIC_APP_DATE=2026-04-06` (see `frontend/.env.local.example`).

Build: `npm run build` (default for Next.js).

## Backend

Run locally from `backend/` (Python venv, `uvicorn`, SQLite seed). The API is not deployed by this repo; host it on Railway, Render, Fly.io, or similar, then set `NEXT_PUBLIC_API_URL` on Vercel.
