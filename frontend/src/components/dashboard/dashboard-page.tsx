"use client";

import * as React from "react";
import useSWR from "swr";
import {
  differenceInCalendarDays,
  endOfMonth,
  format,
  startOfMonth,
} from "date-fns";
import { useProperty } from "@/components/providers/property-context";
import { fetchJson } from "@/lib/api";
import { appNow, isDemoApril2026 } from "@/lib/demo";
import { KpiCards, type KpiData } from "@/components/dashboard/kpi-cards";
import { ForecastChart, type ForecastPoint } from "@/components/dashboard/forecast-chart";
import { DemandSignals, type SignalRow } from "@/components/dashboard/demand-signals";
import { PricingSnapshot, type PricingRow } from "@/components/dashboard/pricing-snapshot";
import { AiBriefCard } from "@/components/dashboard/ai-brief-card";

type TrendResponse = {
  points: Array<{
    date: string;
    occupancy: number | null;
    adr: number | null;
    revpar: number | null;
  }>;
};

type ForecastOccResponse = {
  points: Array<{
    date: string;
    predicted: number;
    lower_bound: number;
    upper_bound: number;
  }>;
};

type DemandResponse = {
  points: Array<{
    demand_score: number;
    weather_score: number;
    flight_index: number;
    event_impact: number;
    search_trend: number;
    season: string;
  }>;
};

type SummaryResponse = {
  total_estimated_revpar_uplift_eur_per_night: number;
};

type RecResponse = {
  recommendations: Array<{
    date: string;
    room_type_name: string;
    room_type_code?: string;
    recommended_rate: number;
    change_pct: number;
  }>;
};

type BriefResponse = { brief: string };

async function loadAll(propertyId: number) {
  const now = appNow();
  const ms = startOfMonth(now);
  const me = endOfMonth(now);
  const startStr = format(ms, "yyyy-MM-dd");
  const endStr = format(me, "yyyy-MM-dd");
  const recEnd = format(
    new Date(now.getTime() + 7 * 86400000),
    "yyyy-MM-dd"
  );

  const settled = await Promise.allSettled([
    fetchJson<TrendResponse>(
      `/api/v1/analytics/occupancy-trend?property_id=${propertyId}&period=90d`
    ),
    fetchJson<ForecastOccResponse>(
      `/api/v1/forecast/occupancy?property_id=${propertyId}&horizon=30`
    ),
    fetchJson<DemandResponse>(
      `/api/v1/forecast/demand?property_id=${propertyId}&horizon=7`
    ),
    fetchJson<SummaryResponse>(
      `/api/v1/pricing/summary?property_id=${propertyId}&start_date=${startStr}&end_date=${endStr}`
    ),
    fetchJson<RecResponse>(
      `/api/v1/pricing/recommendations?property_id=${propertyId}&start_date=${startStr}&end_date=${recEnd}`
    ),
    fetchJson<BriefResponse>(
      `/api/v1/insights/daily-brief?property_id=${propertyId}`
    ),
    fetchJson<{ position_pct_vs_comp: number; comp_avg_rate: number }>(
      `/api/v1/competitors/position?property_id=${propertyId}&start_date=${startStr}&end_date=${endStr}`
    ),
  ]);

  const val = <T,>(i: number, fallback: T): T =>
    settled[i]?.status === "fulfilled" ? (settled[i] as PromiseFulfilledResult<T>).value : fallback;

  return {
    trend: val<TrendResponse>(0, { points: [] }),
    forecast: val<ForecastOccResponse>(1, { points: [] }),
    demand: val<DemandResponse>(2, { points: [] }),
    summary: val<SummaryResponse>(3, {
      total_estimated_revpar_uplift_eur_per_night: 0,
    }),
    recs: val<RecResponse>(4, { recommendations: [] }),
    brief: val<BriefResponse>(5, { brief: "" }),
    position: val(6, { position_pct_vs_comp: 0, comp_avg_rate: 0 }),
  };
}

function buildKpi(trend: TrendResponse): KpiData {
  const pts = trend.points;
  const last = pts[pts.length - 1];
  const prev = pts.length > 1 ? pts[pts.length - 2] : null;
  const occ = last?.occupancy ?? 0;
  const adr = last?.adr ?? 0;
  const revpar = last?.revpar ?? 0;
  const occPrev = prev?.occupancy ?? occ;
  const adrPrev = prev?.adr ?? adr;
  const revPrev = prev?.revpar ?? revpar;

  return {
    occupancy: occ,
    adr,
    revpar,
    uplift: 0,
    occupancyDeltaPp: (occ - occPrev) * 100,
    adrDeltaPct: adrPrev ? ((adr - adrPrev) / adrPrev) * 100 : 0,
    revparDeltaPct: revPrev ? ((revpar - revPrev) / revPrev) * 100 : 0,
  };
}

function buildSignals(
  demand: DemandResponse,
  position: { position_pct_vs_comp: number; comp_avg_rate: number }
): SignalRow[] {
  const pts = demand.points;
  if (!pts.length) {
    const fallback: SignalRow[] = [
      { key: "w", label: "Weather", value: 55, hint: "—", icon: "weather" },
      { key: "f", label: "Flights", value: 50, hint: "—", icon: "flight" },
      { key: "e", label: "Events", value: 0, hint: "—", icon: "event" },
      { key: "t", label: "Trends", value: 58, hint: "—", icon: "trend" },
      {
        key: "c",
        label: "Competitors",
        value: 65,
        hint: "€— avg",
        icon: "comp",
      },
    ];
    if (isDemoApril2026()) {
      const festival = new Date(2026, 3, 18);
      const daysTo = differenceInCalendarDays(festival, appNow());
      fallback[0].hint = "Warm spring — beach season ramping";
      fallback[1].hint = "German arrivals +15% YoY (DBV)";
      fallback[2].hint =
        daysTo >= 0
          ? `Dubrovnik Wine Festival in ${daysTo} days (Apr 18–20)`
          : "Dubrovnik Wine Festival window";
      fallback[4].hint = "Comp set lagging festival demand";
    }
    return fallback;
  }
  const avg = (k: keyof (typeof pts)[0]) =>
    pts.reduce((a, p) => a + (Number(p[k]) || 0), 0) / pts.length;

  const weather = avg("weather_score");
  const flight = avg("flight_index");
  const event = avg("event_impact");
  const trend = avg("demand_score");
  const compScore = Math.min(
    100,
    50 + (position.position_pct_vs_comp || 0) / 2
  );

  const rows: SignalRow[] = [
    {
      key: "weather",
      label: "Weather",
      value: weather,
      hint: "Composite beach-day score",
      icon: "weather",
    },
    {
      key: "flight",
      label: "Flights",
      value: flight,
      hint: "Arrival pressure vs capacity",
      icon: "flight",
    },
    {
      key: "event",
      label: "Events",
      value: event,
      hint: "Regional event impact",
      icon: "event",
    },
    {
      key: "trend",
      label: "Demand index",
      value: trend,
      hint: "Blended occupancy + signals",
      icon: "trend",
    },
    {
      key: "comp",
      label: "Competitors",
      value: compScore,
      hint:
        position.comp_avg_rate > 0
          ? `€${position.comp_avg_rate.toFixed(0)} market avg`
          : "Comp set median",
      icon: "comp",
    },
  ];

  if (isDemoApril2026()) {
    const festival = new Date(2026, 3, 18);
    const daysTo = differenceInCalendarDays(festival, appNow());
    rows[0].hint = "Warm spring — beach season ramping";
    rows[1].hint = "German arrivals +15% YoY (DBV)";
    rows[2].hint =
      daysTo >= 0
        ? `Dubrovnik Wine Festival in ${daysTo} days (Apr 18–20)`
        : "Dubrovnik Wine Festival window";
    rows[4].hint =
      position.comp_avg_rate > 0
        ? `€${position.comp_avg_rate.toFixed(0)} avg — comps not yet lifted for festival`
        : "Comp set lagging festival demand";
  }

  return rows;
}

function buildPricingRows(recs: RecResponse["recommendations"]): PricingRow[] {
  const byName = new Map<string, { recommended: number; changePct: number }>();
  for (const r of recs) {
    const prev = byName.get(r.room_type_name);
    const abs = Math.abs(r.change_pct);
    const isSuperior =
      r.room_type_code === "SUP_DBL_SV" || r.room_type_name.includes("Superior");
    if (
      !prev ||
      abs > Math.abs(prev.changePct) ||
      (abs === Math.abs(prev.changePct) && isSuperior)
    ) {
      byName.set(r.room_type_name, {
        recommended: r.recommended_rate,
        changePct: r.change_pct,
      });
    }
  }
  const rows = Array.from(byName.entries()).map(([roomType, v]) => ({
    roomType,
    recommended: v.recommended,
    changePct: v.changePct,
  }));
  rows.sort((a, b) => {
    if (a.roomType.includes("Superior Double")) return -1;
    if (b.roomType.includes("Superior Double")) return 1;
    return Math.abs(b.changePct) - Math.abs(a.changePct);
  });
  return rows;
}

export function DashboardPage() {
  const { propertyId } = useProperty();
  const { data, error, isLoading } = useSWR(
    ["dashboard", propertyId],
    () => loadAll(propertyId),
    { revalidateOnFocus: false }
  );

  const kpi: KpiData | null = React.useMemo(() => {
    if (!data?.trend?.points?.length) return null;
    const base = buildKpi(data.trend);
    base.uplift = data.summary?.total_estimated_revpar_uplift_eur_per_night ?? base.uplift;
    return base;
  }, [data]);

  const forecastPoints: ForecastPoint[] = React.useMemo(() => {
    if (!data?.forecast?.points) return [];
    return data.forecast.points.map((p) => ({
      date: p.date,
      predicted: p.predicted,
      lower_bound: p.lower_bound,
      upper_bound: p.upper_bound,
    }));
  }, [data]);

  const signals = React.useMemo(() => {
    if (!data) return [];
    return buildSignals(data.demand, data.position);
  }, [data]);

  const pricingRows = React.useMemo(() => {
    if (!data?.recs?.recommendations) return [];
    return buildPricingRows(data.recs.recommendations);
  }, [data]);

  const briefText = data?.brief?.brief?.trim() ? data.brief.brief : null;
  const briefErr =
    error && !data?.brief?.brief
      ? "Could not load dashboard data (is the API running at NEXT_PUBLIC_API_URL?)"
      : null;

  return (
    <div className="mx-auto max-w-[1400px] space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Revenue overview, forecast, and pricing signals for the selected property
          {isDemoApril2026() ? (
            <span className="text-muted-foreground/90">
              {" "}
              · Demo date {format(appNow(), "MMM d, yyyy")}
            </span>
          ) : null}
          .
        </p>
      </div>

      <KpiCards data={kpi} loading={isLoading} />

      <ForecastChart
        points={forecastPoints}
        loading={isLoading}
        eventNote={
          isDemoApril2026()
            ? "Demand spike expected Apr 18–20: Dubrovnik Wine Festival — TouristFlow aligns rates early."
            : "Events overlay: check Calendar for Dubrovnik festivals."
        }
        weatherNote={
          isDemoApril2026()
            ? "Spring warming trend supports higher willingness-to-pay on sea-view inventory."
            : "Weather scores from synthetic coastal series (prototype)."
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PricingSnapshot rows={pricingRows} loading={isLoading} />
        <AiBriefCard
          brief={briefText}
          loading={isLoading}
          error={briefErr}
        />
      </div>

      <DemandSignals rows={signals} loading={isLoading} />
    </div>
  );
}
