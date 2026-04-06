/**
 * Client-side mock responses when NEXT_PUBLIC_MOCK_API=1 (Vercel demo without FastAPI).
 * Shapes mirror backend Pydantic models under backend/schemas/.
 */
import {
  addDays,
  differenceInCalendarDays,
  eachDayOfInterval,
  endOfMonth,
  format,
  parseISO,
  startOfMonth,
  subDays,
} from "date-fns";
import { appNow } from "@/lib/demo";

export function isMockApiEnabled(): boolean {
  return process.env.NEXT_PUBLIC_MOCK_API === "1";
}

function parsePath(path: string): { pathname: string; searchParams: URLSearchParams } {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(normalized, "http://localhost/");
  return { pathname: url.pathname, searchParams: url.searchParams };
}

const ROOM_TYPES = [
  { id: 1, code: "STD_DBL", name: "Standard Double", base: 120 },
  { id: 2, code: "SUP_DBL_SV", name: "Superior Double Sea View", base: 168 },
  { id: 3, code: "DLX_SUITE", name: "Deluxe Suite", base: 285 },
  { id: 4, code: "FAM_RM", name: "Family Room", base: 205 },
  { id: 5, code: "ECO_SGL", name: "Economy Single", base: 88 },
] as const;

function isWineWindow(d: Date): boolean {
  return d.getMonth() === 3 && d.getDate() >= 18 && d.getDate() <= 20;
}

function hashDayRoom(dayStr: string, code: string): number {
  let h = 0;
  const s = dayStr + code;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h) % 1000;
}

function demandLevelForDate(d: Date): string {
  if (isWineWindow(d)) return "very_high";
  const dow = d.getDay();
  if (dow === 0 || dow === 6) return "high";
  if (dow === 5) return "high";
  return "medium";
}

function seasonLabel(d: Date): string {
  if (isWineWindow(d)) return "Event peak";
  return "Spring shoulder";
}

function eventsForDate(d: Date): string[] {
  if (isWineWindow(d)) return ["Dubrovnik Wine Festival"];
  return [];
}

function changePctFor(d: Date, code: string): number {
  if (isWineWindow(d)) {
    if (code === "SUP_DBL_SV") return 12;
    if (code === "DLX_SUITE") return 9;
    if (code === "FAM_RM") return 6;
    if (code === "STD_DBL") return 5;
    return 4;
  }
  const h = hashDayRoom(format(d, "yyyy-MM-dd"), code);
  return 2 + (h % 5);
}

function baseRateForRoom(
  rt: (typeof ROOM_TYPES)[number],
  d: Date
): number {
  let r = rt.base;
  const dow = d.getDay();
  if (dow === 5 || dow === 6) r *= 1.06;
  if (isWineWindow(d)) r *= 1.04;
  const h = hashDayRoom(format(d, "yyyy-MM-dd"), rt.code);
  r += (h % 7) - 3;
  return Math.round(r);
}

function buildOccupancyTrend() {
  const now = appNow();
  const start = subDays(now, 89);
  const points: Array<{
    date: string;
    occupancy: number;
    adr: number;
    revpar: number;
  }> = [];
  for (let i = 0; i < 90; i++) {
    const d = addDays(start, i);
    const ds = format(d, "yyyy-MM-dd");
    const t = i / 90;
    const occ = Math.min(0.92, 0.48 + t * 0.18 + Math.sin(i * 0.12) * 0.04);
    const adr = 135 + i * 0.35 + Math.sin(i * 0.08) * 6;
    const revpar = occ * adr;
    points.push({
      date: ds,
      occupancy: Math.round(occ * 1000) / 1000,
      adr: Math.round(adr * 10) / 10,
      revpar: Math.round(revpar * 10) / 10,
    });
  }
  return { points };
}

function buildForecastOcc() {
  const now = appNow();
  const points: Array<{
    date: string;
    predicted: number;
    lower_bound: number;
    upper_bound: number;
  }> = [];
  for (let i = 1; i <= 30; i++) {
    const d = addDays(now, i);
    const ds = format(d, "yyyy-MM-dd");
    const base = 0.56 + Math.sin(i * 0.15) * 0.08;
    const wf = isWineWindow(d) ? 0.14 : 0;
    const pred = Math.min(0.94, base + wf);
    points.push({
      date: ds,
      predicted: Math.round(pred * 1000) / 1000,
      lower_bound: Math.round((pred - 0.06) * 1000) / 1000,
      upper_bound: Math.round((pred + 0.05) * 1000) / 1000,
    });
  }
  return { points };
}

function buildDemand() {
  const now = appNow();
  const points: Array<{
    demand_score: number;
    weather_score: number;
    flight_index: number;
    event_impact: number;
    search_trend: number;
    season: string;
  }> = [];
  for (let i = 0; i < 7; i++) {
    const d = addDays(now, i);
    const wine = isWineWindow(d) ? 0.55 : 0.08;
    points.push({
      demand_score: 62 + wine * 15 + (i % 3) * 2,
      weather_score: 68 + (i % 4),
      flight_index: 71,
      event_impact: wine * 80 + 5,
      search_trend: 58 + wine * 10,
      season: "spring",
    });
  }
  return { points };
}

function buildPricingSummary(startStr: string, endStr: string) {
  const start = parseISO(startStr);
  const end = parseISO(endStr);
  const days = differenceInCalendarDays(end, start) + 1;
  return {
    property_id: 1,
    start_date: startStr,
    end_date: endStr,
    total_estimated_revpar_uplift_eur_per_night: 12400,
    recommendation_count: Math.max(1, days) * ROOM_TYPES.length,
  };
}

function buildRecItem(d: Date, rt: (typeof ROOM_TYPES)[number]) {
  const dayStr = format(d, "yyyy-MM-dd");
  const chp = changePctFor(d, rt.code);
  const current = baseRateForRoom(rt, d);
  const recommended = Math.round(current * (1 + chp / 100));
  const occC = 0.58 + (hashDayRoom(dayStr, rt.code) % 8) / 100;
  const occR = Math.min(0.94, occC + chp * 0.0015);
  const revC = current * occC;
  const revR = recommended * occR;
  return {
    date: dayStr,
    room_type_id: rt.id,
    room_type_code: rt.code,
    room_type_name: rt.name,
    current_rate: current,
    recommended_rate: recommended,
    change_pct: chp,
    confidence: 0.72 + (hashDayRoom(dayStr, rt.code) % 25) / 100,
    predicted_occupancy_current: Math.round(occC * 1000) / 1000,
    predicted_occupancy_recommended: Math.round(occR * 1000) / 1000,
    revpar_current: Math.round(revC * 10) / 10,
    revpar_recommended: Math.round(revR * 10) / 10,
    revpar_uplift: Math.round((revR - revC) * 10) / 10,
    demand_level: demandLevelForDate(d),
    rationale: isWineWindow(d)
      ? "Festival cluster — lift sea-view and suites ahead of comp set."
      : "Shoulder-season uplift from blended demand signals.",
  };
}

function buildRecommendations(startStr: string, endStr: string) {
  const start = parseISO(startStr);
  const end = parseISO(endStr);
  const days = eachDayOfInterval({ start, end });
  const recommendations = [];
  for (const d of days) {
    for (const rt of ROOM_TYPES) {
      recommendations.push(buildRecItem(d, rt));
    }
  }
  return {
    property_id: 1,
    start_date: startStr,
    end_date: endStr,
    recommendations,
  };
}

function buildCalendarMonth(monthStr: string) {
  const [y, m] = monthStr.split("-").map(Number);
  const anchor = new Date(y, m - 1, 1);
  const start = startOfMonth(anchor);
  const end = endOfMonth(anchor);
  const days = eachDayOfInterval({ start, end }).map((dt) => ({
    date: format(dt, "yyyy-MM-dd"),
    demand_level: demandLevelForDate(dt),
    season: seasonLabel(dt),
    events: eventsForDate(dt),
  }));
  return { property_id: 1, month: monthStr, days };
}

function buildBrief() {
  const d = format(appNow(), "yyyy-MM-dd");
  return {
    brief: `## Dubrovnik — ${d}

**Market snapshot:** Occupancy is firming into late April with search demand ahead of the Dubrovnik Wine Festival (Apr 18–20). Sea-view inventory (Superior Double Sea View) should lead price lifts before the comp set recalibrates.

**Recommendation:** Apply +8–12% on premium room types for the festival window; hold standard double for volume on shoulder nights.

**Competitors:** Primary set is ~€185 ARR; you are positioned about +4% on rate with room to push on sea-view upsell.

*(Demo brief — TouristFlow showcase)*`,
  };
}

function buildPosition(startStr: string, endStr: string) {
  return {
    property_id: 1,
    start_date: startStr,
    end_date: endStr,
    our_avg_adr: 172,
    comp_avg_rate: 185,
    position_pct_vs_comp: 4.2,
  };
}

function buildCompetitorsList(propertyId: number) {
  return {
    property_id: propertyId,
    competitors: [
      {
        id: 101,
        name: "Rixos Premium Dubrovnik",
        stars: 5,
        rooms: 136,
        is_primary: true,
        latest_rate_eur: 198,
        rate_date: "2026-04-05",
        available: true,
      },
      {
        id: 102,
        name: "Hilton Imperial Dubrovnik",
        stars: 5,
        rooms: 147,
        is_primary: false,
        latest_rate_eur: 210,
        rate_date: "2026-04-05",
        available: true,
      },
      {
        id: 103,
        name: "Hotel Excelsior Dubrovnik",
        stars: 5,
        rooms: 158,
        is_primary: false,
        latest_rate_eur: 225,
        rate_date: "2026-04-04",
        available: true,
      },
      {
        id: 104,
        name: "Hotel Lapad",
        stars: 4,
        rooms: 173,
        is_primary: false,
        latest_rate_eur: 142,
        rate_date: "2026-04-05",
        available: true,
      },
      {
        id: 105,
        name: "Valamar Lacroma Dubrovnik",
        stars: 4,
        rooms: 385,
        is_primary: false,
        latest_rate_eur: 128,
        rate_date: "2026-04-05",
        available: true,
      },
    ],
  };
}

function mockSimulatorRun(body: unknown) {
  const b = body as {
    date_range_start: string;
    date_range_end: string;
    price_adjustments: Record<string, number>;
  };
  const start = parseISO(b.date_range_start);
  const end = parseISO(b.date_range_end);
  const days = Math.max(1, differenceInCalendarDays(end, start) + 1);
  const adjustments = b.price_adjustments ?? {};
  const vals = Object.values(adjustments);
  const avgAdj = vals.length ? vals.reduce((a, x) => a + x, 0) / vals.length : 0;

  const dailyBase = 5100;
  const baselineRevenue = days * dailyBase;
  const elasticity = 0.42;
  const scenarioMult = 1 + (avgAdj / 100) * elasticity;
  const scenarioRevenue = baselineRevenue * scenarioMult;
  const revenue_delta = scenarioRevenue - baselineRevenue;
  const revenue_delta_pct = (revenue_delta / baselineRevenue) * 100;

  const roomNights = days * 48;
  const baseline_revpar = baselineRevenue / roomNights;
  const scenario_revpar = scenarioRevenue / roomNights;
  const baseline_occ = 0.68;
  const scenario_occ = Math.max(
    0.45,
    Math.min(0.92, baseline_occ - avgAdj * 0.002)
  );

  const daily_breakdown = [];
  for (let i = 0; i < days; i++) {
    const d = addDays(start, i);
    const jitter = 1 + Math.sin(i * 0.7) * 0.04;
    const br = (baselineRevenue / days) * jitter;
    const sr = br * scenarioMult;
    daily_breakdown.push({
      date: format(d, "yyyy-MM-dd"),
      baseline_revenue: Math.round(br),
      scenario_revenue: Math.round(sr),
      baseline_occupancy: Math.round((baseline_occ + Math.sin(i * 0.3) * 0.02) * 1000) / 1000,
      scenario_occupancy: Math.round((scenario_occ + Math.sin(i * 0.3) * 0.02) * 1000) / 1000,
    });
  }

  return {
    scenario_id: null,
    baseline_revenue: Math.round(baselineRevenue),
    scenario_revenue: Math.round(scenarioRevenue),
    revenue_delta: Math.round(revenue_delta),
    revenue_delta_pct: Math.round(revenue_delta_pct * 10) / 10,
    baseline_occupancy: Math.round(baseline_occ * 1000) / 1000,
    scenario_occupancy: Math.round(scenario_occ * 1000) / 1000,
    baseline_revpar: Math.round(baseline_revpar * 10) / 10,
    scenario_revpar: Math.round(scenario_revpar * 10) / 10,
    daily_breakdown,
    days_modelled: days,
  };
}

export function mockFetchJson(path: string): unknown {
  const { pathname, searchParams } = parsePath(path);
  const prop = searchParams.get("property_id") ?? "1";

  switch (pathname) {
    case "/api/v1/analytics/occupancy-trend":
      return buildOccupancyTrend();
    case "/api/v1/forecast/occupancy":
      return buildForecastOcc();
    case "/api/v1/forecast/demand":
      return buildDemand();
    case "/api/v1/pricing/summary": {
      const sd = searchParams.get("start_date");
      const ed = searchParams.get("end_date");
      if (!sd || !ed) throw new Error("Mock: pricing/summary needs dates");
      return buildPricingSummary(sd, ed);
    }
    case "/api/v1/pricing/recommendations": {
      const sd = searchParams.get("start_date");
      const ed = searchParams.get("end_date");
      if (!sd || !ed) throw new Error("Mock: recommendations need dates");
      return buildRecommendations(sd, ed);
    }
    case "/api/v1/pricing/calendar": {
      const month = searchParams.get("month");
      if (!month) throw new Error("Mock: calendar needs month");
      return buildCalendarMonth(month);
    }
    case "/api/v1/insights/daily-brief":
      return buildBrief();
    case "/api/v1/competitors/position": {
      const sd = searchParams.get("start_date");
      const ed = searchParams.get("end_date");
      if (!sd || !ed) throw new Error("Mock: position needs dates");
      return buildPosition(sd, ed);
    }
    case "/api/v1/competitors":
      return buildCompetitorsList(Number(prop));
    default:
      throw new Error(`Mock API: unknown GET ${pathname}`);
  }
}

export function mockPostJson(path: string, body: unknown): unknown {
  const { pathname } = parsePath(path);
  if (pathname === "/api/v1/simulator/run") {
    return mockSimulatorRun(body);
  }
  throw new Error(`Mock API: unknown POST ${pathname}`);
}
