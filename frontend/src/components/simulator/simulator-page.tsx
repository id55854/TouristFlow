"use client";

import * as React from "react";
import useSWR from "swr";
import { addDays, format } from "date-fns";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useProperty } from "@/components/providers/property-context";
import { fetchJson, postJson } from "@/lib/api";
import { appNow } from "@/lib/demo";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Skeleton } from "@/components/ui/skeleton";

type RecItem = {
  room_type_code: string;
  room_type_name: string;
};

type RecResponse = {
  recommendations: RecItem[];
};

type WhatIfResult = {
  scenario_id: number | null;
  baseline_revenue: number;
  scenario_revenue: number;
  revenue_delta: number;
  revenue_delta_pct: number;
  baseline_occupancy: number;
  scenario_occupancy: number;
  baseline_revpar: number;
  scenario_revpar: number;
  days_modelled: number;
};

function extractRoomTypes(recs: RecItem[]) {
  const m = new Map<string, string>();
  for (const r of recs) {
    if (!m.has(r.room_type_code)) {
      m.set(r.room_type_code, r.room_type_name);
    }
  }
  return Array.from(m.entries())
    .map(([code, name]) => ({ code, name }))
    .sort((a, b) => a.code.localeCompare(b.code));
}

async function loadRoomTypes(propertyId: number) {
  const start = format(appNow(), "yyyy-MM-dd");
  const end = format(addDays(appNow(), 120), "yyyy-MM-dd");
  const res = await fetchJson<RecResponse>(
    `/api/v1/pricing/recommendations?property_id=${propertyId}&start_date=${start}&end_date=${end}`
  );
  return extractRoomTypes(res.recommendations);
}

export function SimulatorPage() {
  const { propertyId } = useProperty();
  const [rangeStart, setRangeStart] = React.useState(() =>
    format(appNow(), "yyyy-MM-dd")
  );
  const [rangeEnd, setRangeEnd] = React.useState(() =>
    format(addDays(appNow(), 30), "yyyy-MM-dd")
  );
  const [adjustments, setAdjustments] = React.useState<Record<string, number>>({});
  const [result, setResult] = React.useState<WhatIfResult | null>(null);
  const [running, setRunning] = React.useState(false);
  const [runError, setRunError] = React.useState<string | null>(null);

  const { data: roomTypes, error: rtError, isLoading: rtLoading } = useSWR(
    ["sim-room-types", propertyId],
    () => loadRoomTypes(propertyId)
  );

  React.useEffect(() => {
    if (!roomTypes?.length) return;
    setAdjustments((prev) => {
      const next = { ...prev };
      for (const rt of roomTypes) {
        if (next[rt.code] === undefined) next[rt.code] = 0;
      }
      return next;
    });
  }, [roomTypes]);

  const setPct = (code: string, value: number) => {
    setAdjustments((prev) => ({ ...prev, [code]: value }));
  };

  async function runScenario() {
    setRunError(null);
    setRunning(true);
    try {
      const price_adjustments: Record<string, number> = {};
      for (const rt of roomTypes ?? []) {
        const v = adjustments[rt.code] ?? 0;
        if (v !== 0) price_adjustments[rt.code] = v;
      }
      const res = await postJson<WhatIfResult>("/api/v1/simulator/run", {
        property_id: propertyId,
        date_range_start: rangeStart,
        date_range_end: rangeEnd,
        price_adjustments,
        name: `UI scenario ${format(appNow(), "yyyy-MM-dd HH:mm")}`,
        description: "Run from TouristFlow dashboard",
      });
      setResult(res);
    } catch (e) {
      setRunError(e instanceof Error ? e.message : "Request failed");
      setResult(null);
    } finally {
      setRunning(false);
    }
  }

  const chartData = result
    ? [
        { name: "Baseline", revenue: result.baseline_revenue },
        { name: "Scenario", revenue: result.scenario_revenue },
      ]
    : [];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">What-if simulator</h1>
        <p className="text-sm text-muted-foreground">
          Adjust rates by room type and compare projected revenue to the baseline for a date
          range.
        </p>
      </div>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Scenario setup</CardTitle>
          <CardDescription>
            Price change per room type: −30% to +30%. Unchanged types count as 0%.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="range-start">Start date</Label>
              <Input
                id="range-start"
                type="date"
                value={rangeStart}
                onChange={(e) => setRangeStart(e.target.value)}
                className="bg-background"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="range-end">End date</Label>
              <Input
                id="range-end"
                type="date"
                value={rangeEnd}
                onChange={(e) => setRangeEnd(e.target.value)}
                className="bg-background"
              />
            </div>
          </div>

          <Separator />

          {rtLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : rtError ? (
            <p className="text-sm text-destructive">
              Could not load room types. Is the API running?
            </p>
          ) : !roomTypes?.length ? (
            <p className="text-sm text-muted-foreground">
              No room types found from recommendations. Seed data may be required.
            </p>
          ) : (
            <div className="space-y-6">
              {roomTypes.map((rt) => {
                const v = adjustments[rt.code] ?? 0;
                return (
                  <div key={rt.code} className="space-y-3">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium leading-none">{rt.name}</p>
                        <p className="text-xs text-muted-foreground">{rt.code}</p>
                      </div>
                      <span
                        className={cn(
                          "tabular-nums text-sm font-medium",
                          v > 0 && "text-primary",
                          v < 0 && "text-amber-500"
                        )}
                      >
                        {v > 0 ? "+" : ""}
                        {v}%
                      </span>
                    </div>
                    <Slider
                      min={-30}
                      max={30}
                      step={1}
                      value={[v]}
                      onValueChange={(nv) => {
                        const next = Array.isArray(nv) ? nv[0] : nv;
                        setPct(rt.code, typeof next === "number" ? next : 0);
                      }}
                      className="w-full"
                    />
                  </div>
                );
              })}
            </div>
          )}

          <Button
            type="button"
            className="w-full sm:w-auto"
            disabled={running || !roomTypes?.length}
            onClick={() => void runScenario()}
          >
            {running ? "Running…" : "Run scenario"}
          </Button>
          {runError ? (
            <p className="text-sm text-destructive">{runError}</p>
          ) : null}
        </CardContent>
      </Card>

      {result ? (
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>
              {result.days_modelled} day(s) with occupancy data · Baseline vs scenario
              revenue
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <p className="text-xs text-muted-foreground">Baseline revenue</p>
                <p className="text-xl font-semibold tabular-nums">
                  €{result.baseline_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <p className="text-xs text-muted-foreground">Scenario revenue</p>
                <p className="text-xl font-semibold tabular-nums text-primary">
                  €{result.scenario_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <p className="text-xs text-muted-foreground">Δ Revenue</p>
                <p
                  className={cn(
                    "text-xl font-semibold tabular-nums",
                    result.revenue_delta >= 0 ? "text-emerald-500" : "text-destructive"
                  )}
                >
                  {result.revenue_delta >= 0 ? "+" : ""}
                  €{result.revenue_delta.toLocaleString(undefined, { maximumFractionDigits: 0 })}{" "}
                  <span className="text-sm font-normal text-muted-foreground">
                    ({result.revenue_delta_pct >= 0 ? "+" : ""}
                    {result.revenue_delta_pct}%)
                  </span>
                </p>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <p className="text-xs text-muted-foreground">RevPAR (base / scen.)</p>
                <p className="text-lg font-semibold tabular-nums">
                  €{result.baseline_revpar.toFixed(0)} → €{result.scenario_revpar.toFixed(0)}
                </p>
              </div>
            </div>

            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={11}
                    tickFormatter={(v) => `€${v}`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--popover))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                    formatter={(value) => [
                      typeof value === "number"
                        ? `€${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                        : String(value),
                      "Revenue",
                    ]}
                  />
                  <Bar
                    dataKey="revenue"
                    radius={[6, 6, 0, 0]}
                    name="Revenue"
                    isAnimationActive
                    animationDuration={1200}
                    animationEasing="ease-out"
                  >
                    {chartData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={
                          i === 0
                            ? "hsl(var(--chart-2))"
                            : "hsl(var(--chart-1))"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
