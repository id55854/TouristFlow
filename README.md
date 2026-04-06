# TouristFlow

Hotel revenue dashboard (Next.js) + FastAPI backend with forecasting and pricing APIs.

## Repository

Remote: [github.com/id55854/TouristFlow](https://github.com/id55854/TouristFlow)

## Frontend (Vercel)

**Production:** [touristflow.vercel.app](https://touristflow.vercel.app)

To connect [GitHub](https://github.com/id55854/TouristFlow) for automatic deploys: Vercel → Project → **Settings → Git** → link `id55854/TouristFlow` and set **Root Directory** to `frontend`.

Manual setup:

1. Import this repo in [Vercel](https://vercel.com/new).
2. Set **Root Directory** to `frontend`.
3. **Environment variables** (optional):
   - `NEXT_PUBLIC_API_URL` — URL of your deployed FastAPI backend (e.g. `https://xxxx.up.railway.app`). If unset, the app defaults to `http://localhost:8000`.
   - For the Dubrovnik demo story: `NEXT_PUBLIC_APP_DATE=2026-04-06` (see `frontend/.env.local.example`).

Build: `npm run build` (default for Next.js).

## Backend — deploy on [Railway](https://railway.app) (recommended)

Railway offers a **[30-day trial with $5 in credits and no credit card required](https://docs.railway.com/pricing/free-trial)** (see [pricing / free trial](https://docs.railway.com/pricing/free-trial) for current terms). After the trial, accounts can move to the **Free** plan with a small monthly usage credit, or upgrade.

### One-time setup

1. Sign up at [railway.app](https://railway.app) (GitHub login works).
2. **New Project** → **Deploy from GitHub** → select this repo.
3. Add a **service** from the repo → open the service **Settings**:
   - **Root Directory** = `backend` (required for this monorepo).
   - Builder should pick up **`backend/Dockerfile`** via `backend/railway.toml` (Prophet needs the Docker build with `build-essential`).
4. **Variables** (service → **Variables**):
   - `TOURISTFLOW_DEMO_DATE` = `2026-04-06` (optional demo narrative)
   - `GEMINI_API_KEY` — optional, for live AI briefs ([Google AI Studio](https://aistudio.google.com/apikey))
5. **Networking** → **Generate Domain** (or attach your own). Copy the public `https://…` URL.
6. On **Vercel**, set **`NEXT_PUBLIC_API_URL`** to that Railway URL (no trailing slash).

### How it runs

- **`backend/Dockerfile`**: installs deps, then at runtime runs `seed.py` once per container start and starts **uvicorn** on **`PORT`** (Railway-provided).
- **`backend/railway.toml`**: Dockerfile builder + `/health` check with a long timeout (first boot can be slow while seeding).
- **`seed.py`**: detects **`RAILWAY_PROJECT_ID`** and keeps SQLite instead of wiping it on every start; skips full re-seed when data already exists.

### After the trial

See [Railway pricing](https://railway.com/pricing). Prophet and long builds can use credits quickly; scale instance size if the deploy fails or OOMs.

### Run locally

From `backend/`: `pip install -r requirements.txt`, `python seed.py`, `uvicorn main:app --reload --port 8000`.

### Other hosts

- **[Koyeb](https://www.koyeb.com)**, **[Fly.io](https://fly.io)**, **[Google Cloud Run](https://cloud.google.com/run)** — use the same Docker image or `Procfile`-style command; set **`TOURISTFLOW_MANAGED_HOST=1`** if the platform doesn’t set env vars `seed.py` recognizes (see `backend/.env.example`).
