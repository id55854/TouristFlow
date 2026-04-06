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
import Link from "next/link";
import { useProperty } from "@/components/providers/property-context";
import { fetchJson } from "@/lib/api";
import { appNow } from "@/lib/demo";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

async function loadCalendar(propertyId: number, monthAnchor: Date) {
  const monthStr = format(monthAnchor, "yyyy-MM");
  return fetchJson<CalendarResponse>(
    `/api/v1/pricing/calendar?property_id=${propertyId}&month=${monthStr}`
  );
}

export default function CalendarPage() {
  const { propertyId } = useProperty();
  const [monthAnchor, setMonthAnchor] = React.useState(() => startOfMonth(appNow()));
  const monthStr = format(monthAnchor, "yyyy-MM");

  const { data, error, isLoading } = useSWR(
    ["calendar-page", propertyId, monthStr],
    () => loadCalendar(propertyId, monthAnchor),
    { revalidateOnFocus: false }
  );

  const demandByDay = React.useMemo(() => {
    const m = new Map<string, CalendarDay>();
    for (const d of data?.days ?? []) {
      m.set(toDayKey(d.date), d);
    }
    return m;
  }, [data?.days]);

  const monthDays = React.useMemo(
    () =>
      eachDayOfInterval({
        start: startOfMonth(monthAnchor),
        end: endOfMonth(monthAnchor),
      }),
    [monthAnchor]
  );

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

  const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Calendar</h1>
        <p className="text-sm text-muted-foreground">
          Demand heatmap by day with season and event labels. Pair with{" "}
          <Link href="/pricing" className="text-primary underline-offset-4 hover:underline">
            Pricing
          </Link>{" "}
          for nightly rates by room type.
        </p>
      </div>

      <Card className="border-border bg-card">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Events &amp; demand</CardTitle>
            <CardDescription>
              Color intensity reflects blended demand (seasonality + events + signals).
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
            {(Object.keys(DEMAND_LABEL) as Array<keyof typeof DEMAND_LABEL>).map((level) => (
              <div key={level} className="flex items-center gap-2">
                <span
                  className={cn("h-3 w-6 rounded-sm", DEMAND_CELL[level] ?? "bg-muted")}
                />
                <span className="text-muted-foreground">{DEMAND_LABEL[level]}</span>
              </div>
            ))}
          </div>

          {isLoading ? (
            <Skeleton className="h-[280px] w-full rounded-lg" />
          ) : error ? (
            <p className="text-sm text-destructive">
              Could not load calendar. Enable NEXT_PUBLIC_MOCK_API=1 or start the API.
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
                      info?.events?.length ? `Events: ${info.events.join(", ")}` : null,
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
                          {info?.events?.[0] ?? info?.season ?? "—"}
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
    </div>
  );
}
