/**
 * Demo "today" for investor story (Apr 6, 2026 — Dubrovnik Wine Festival run-up).
 * Set `NEXT_PUBLIC_APP_DATE=2026-04-06` in `.env.local` (see `.env.local.example`).
 */
export function appNow(): Date {
  const raw = process.env.NEXT_PUBLIC_APP_DATE;
  if (raw && /^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    return new Date(`${raw}T12:00:00`);
  }
  return new Date();
}

export function isDemoApril2026(): boolean {
  const d = appNow();
  return d.getFullYear() === 2026 && d.getMonth() === 3;
}
