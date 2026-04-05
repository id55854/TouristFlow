"use client";

import * as React from "react";
import useSWR from "swr";
import {
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  format,
  getISODay,
  startOfMonth,
  subMonths,
} from "date-fns";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useProperty } from "@/components/providers/property-context";
import { fetchJson } from "@/lib/api";
import { appNow } from "@/lib/demo";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";

type CalendarDay = {
  date: string;
  demand_level: string;
  season: string;
  events: string[];
};

type CalendarResponse = {
  property_id: number;
  month: string;
  days: CalendarDay[];
};

type RecItem = {
  date: string;
  room_type_code: string;
  room_type_name: string;
  current_rate: number;
  recommended_rate: number;
};

type RecResponse = {
  recommendations: RecItem[];
};

const DEMAND_CELL: Record<string, string> = {
  very_low: "bg-slate-700/90 border border-border text-foreground",
  low: "bg-sky-900/85 border border-sky-800/60 text-foreground",
  medium: "bg-amber-600/55 border border-amber-500/40 text-foreground",
  high: "bg-orange-600/65 border border-orange-500/45 text-foreground",
  very_high: "bg-rose-600/70 border border-rose-500/50 text-foreground",
};

const DEMAND_LABEL: Record<string, string> = {
  very_low: "Very low",
  low: "Low",
  medium: "Medium",
  high: "High",
  very_high: "Very high",
};

function toDayKey(d: string | Date): string {
  if (typeof d === "string") return d.slice(0, 10);
  return format(d, "yyyy-MM-dd");
}

async function loadPricingMonth(propertyId: number, monthAnchor: Date) {
  const monthStr = format(monthAnchor, "yyyy-MM");
  const start = format(startOfMonth(monthAnchor), "yyyy-MM-dd");
  const end = format(endOfMonth(monthAnchor), "yyyy-MM-dd");
  const [cal, recs] = await Promise.all([
    fetchJson<CalendarResponse>(
      `/api/v1/pricing/calendar?property_id=${propertyId}&month=${monthStr}`
    ),
    fetchJson<RecResponse>(
      `/api/v1/pricing/recommendations?property_id=${propertyId}&start_date=${start}&end_date=${end}`
    ),
  ]);
  return { cal, recs };
}

export function PricingPage() {
  const { propertyId } = useProperty();
  const [monthAnchor, setMonthAnchor] = React.useState(() => startOfMonth(appNow()));
  const monthStr = format(monthAnchor, "yyyy-MM");

  const { data, error, isLoading } = useSWR(
    ["pricing-month", propertyId, monthStr],
    () => loadPricingMonth(propertyId, monthAnchor)
  );

  const demandByDay = React.useMemo(() => {
    const m = new Map<string, CalendarDay>();
    for (const d of data?.cal.days ?? []) {
      m.set(toDayKey(d.date), d);
    }
    return m;
  }, [data?.cal.days]);

  const monthDays = React.useMemo(
    () =>
      eachDayOfInterval({
        start: startOfMonth(monthAnchor),
        end: endOfMonth(monthAnchor),
      }),
    [monthAnchor]
  );

  const { roomTypes, priceMap } = React.useMemo(() => {
    const recs = data?.recs.recommendations ?? [];
    const rt = new Map<string, { code: string; name: string }>();
    const pmap = new Map<string, { current: number; rec: number }>();
    for (const r of recs) {
      const dk = toDayKey(r.date);
      if (!rt.has(r.room_type_code)) {
        rt.set(r.room_type_code, {
          code: r.room_type_code,
          name: r.room_type_name,
        });
      }
      pmap.set(`${dk}|${r.room_type_code}`, {
        current: r.current_rate,
        rec: r.recommended_rate,
      });
    }
    const roomTypesSorted = Array.from(rt.values()).sort((a, b) =>
      a.code.localeCompare(b.code)
    );
    return { roomTypes: roomTypesSorted, priceMap: pmap };
  }, [data?.recs.recommendations]);

  const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const pad = getISODay(startOfMonth(monthAnchor)) - 1;
  const cells: (Date | null)[] = [
    ...Array.from({ length: pad }, () => null),
    ...monthDays.map((d) => d),
  ];
  while (cells.length % 7 !== 0) cells.push(null);
  const rows: (Date | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) {
    rows.push(cells.slice(i, i + 7));
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Pricing</h1>
        <p className="text-sm text-muted-foreground">
          Demand calendar and recommended rates by room type for the selected month.
        </p>
      </div>

      <Card className="border-border bg-card">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Demand calendar</CardTitle>
            <CardDescription>
              Daily demand level from signals and seasonality (color-coded).
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setMonthAnchor(subMonths(monthAnchor, 1))}
              aria-label="Previous month"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="min-w-[9rem] text-center text-sm font-medium tabular-nums">
              {format(monthAnchor, "MMMM yyyy")}
            </span>
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setMonthAnchor(addMonths(monthAnchor, 1))}
              aria-label="Next month"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-3 text-xs">
            {(Object.keys(DEMAND_LABEL) as Array<keyof typeof DEMAND_LABEL>).map(
              (level) => (
                <div key={level} className="flex items-center gap-2">
                  <span
                    className={cn(
                      "h-3 w-6 rounded-sm",
                      DEMAND_CELL[level] ?? "bg-muted"
                    )}
                  />
                  <span className="text-muted-foreground">
                    {DEMAND_LABEL[level]}
                  </span>
                </div>
              )
            )}
          </div>

          {isLoading ? (
            <Skeleton className="h-[280px] w-full rounded-lg" />
          ) : error ? (
            <p className="text-sm text-destructive">
              Could not load calendar. Is the API running?
            </p>
          ) : (
            <div className="overflow-hidden rounded-lg border border-border">
              <div className="grid grid-cols-7 border-b border-border bg-muted/40 text-center text-xs font-medium text-muted-foreground">
                {weekDays.map((w) => (
                  <div key={w} className="border-r border-border py-2 last:border-r-0">
                    {w}
                  </div>
                ))}
              </div>
              {rows.map((row, ri) => (
                <div key={ri} className="grid grid-cols-7 border-b border-border last:border-b-0">
                  {row.map((day, di) => {
                    if (!day) {
                      return (
                        <div
                          key={`empty-${ri}-${di}`}
                          className="min-h-[72px] border-r border-border bg-muted/20 last:border-r-0"
                        />
                      );
                    }
                    const key = format(day, "yyyy-MM-dd");
                    const info = demandByDay.get(key);
                    const level = info?.demand_level ?? "medium";
                    const title = [
                      format(day, "PPP"),
                      info?.season ? `Season: ${info.season}` : null,
                      info?.events?.length
                        ? `Events: ${info.events.join(", ")}`
                        : null,
                      DEMAND_LABEL[level] ?? level,
                    ]
                      .filter(Boolean)
                      .join(" · ");

                    return (
                      <div
                        key={key}
                        title={title}
                        className={cn(
                          "flex min-h-[72px] flex-col items-center justify-start border-r border-border p-1.5 last:border-r-0",
                          DEMAND_CELL[level] ?? DEMAND_CELL.medium
                        )}
                      >
                        <span className="text-sm font-semibold tabular-nums">
                          {format(day, "d")}
                        </span>
                        <span className="mt-0.5 line-clamp-2 text-center text-[10px] leading-tight opacity-90">
                          {info?.season ?? "—"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Price grid</CardTitle>
          <CardDescription>
            Current rate vs recommended rate (EUR) for each night and room type.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-[320px] w-full rounded-lg" />
          ) : error ? (
            <p className="text-sm text-destructive">
              Could not load recommendations.
            </p>
          ) : roomTypes.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No recommendations for this month. Try another month or ensure seed
              data exists.
            </p>
          ) : (
            <ScrollArea className="w-full">
              <div className="min-w-[720px]">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/40">
                      <th className="sticky left-0 z-10 border-r border-border bg-card px-3 py-2 text-left font-medium">
                        Room type
                      </th>
                      {monthDays.map((d) => (
                        <th
                          key={format(d, "yyyy-MM-dd")}
                          className="border-r border-border px-1.5 py-2 text-center text-xs font-medium text-muted-foreground last:border-r-0"
                        >
                          <div>{format(d, "EEE")}</div>
                          <div className="tabular-nums text-foreground">
                            {format(d, "d")}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {roomTypes.map((rt) => (
                      <tr key={rt.code} className="border-b border-border last:border-b-0">
                        <td className="sticky left-0 z-10 border-r border-border bg-card px-3 py-2 text-left">
                          <div className="font-medium leading-tight">{rt.name}</div>
                          <div className="text-xs text-muted-foreground">{rt.code}</div>
                        </td>
                        {monthDays.map((d) => {
                          const dk = format(d, "yyyy-MM-dd");
                          const cell = priceMap.get(`${dk}|${rt.code}`);
                          return (
                            <td
                              key={`${rt.code}-${dk}`}
                              className="border-r border-border px-1 py-1.5 text-center align-top text-xs last:border-r-0"
                            >
                              {cell ? (
                                <div className="flex flex-col gap-0.5 tabular-nums">
                                  <span className="text-muted-foreground">
                                    €{cell.current.toFixed(0)}
                                  </span>
                                  <span className="font-medium text-primary">
                                    €{cell.rec.toFixed(0)}
                                  </span>
                                </div>
                              ) : (
                                <span className="text-muted-foreground">—</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
