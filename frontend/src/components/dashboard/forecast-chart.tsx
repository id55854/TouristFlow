"use client";

import {
  CartesianGrid,
  ComposedChart,
  Area,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { format, parseISO } from "date-fns";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export type ForecastPoint = {
  date: string;
  predicted: number;
  lower_bound: number;
  upper_bound: number;
};

export function ForecastChart({
  points,
  loading,
  eventNote,
  weatherNote,
}: {
  points: ForecastPoint[];
  loading: boolean;
  eventNote?: string;
  weatherNote?: string;
}) {
  const data = points.map((p) => ({
    ...p,
    lower: p.lower_bound,
    upper: p.upper_bound,
    range: Math.max(0, p.upper_bound - p.lower_bound),
    label: p.date,
  }));

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle>30-day occupancy forecast</CardTitle>
        <CardDescription>
          Prophet model with 80% confidence band · RevPAR optimization context
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <Skeleton className="h-[320px] w-full rounded-lg" />
        ) : (
          <div className="h-[320px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis
                  dataKey="label"
                  tickFormatter={(v) => {
                    try {
                      return format(parseISO(v), "MMM d");
                    } catch {
                      return v;
                    }
                  }}
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={11}
                />
                <YAxis
                  domain={[0, 1]}
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={11}
                  width={44}
                />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  labelFormatter={(v) => {
                    try {
                      return format(parseISO(String(v)), "PP");
                    } catch {
                      return String(v);
                    }
                  }}
                  formatter={(value, name) => {
                    if (value === undefined || value === null) {
                      return ["—", String(name)];
                    }
                    const num =
                      typeof value === "number" ? value : Number(value);
                    if (!Number.isFinite(num)) {
                      return [String(value), String(name)];
                    }
                    if (name === "predicted") {
                      return [`${(num * 100).toFixed(1)}%`, "Forecast"];
                    }
                    return [num, String(name)];
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  stackId="band"
                  stroke="none"
                  fill="hsl(var(--background))"
                  fillOpacity={1}
                  isAnimationActive
                  animationDuration={1400}
                  animationEasing="ease-out"
                />
                <Area
                  type="monotone"
                  dataKey="range"
                  stackId="band"
                  stroke="none"
                  fill="hsl(var(--chart-1))"
                  fillOpacity={0.35}
                  isAnimationActive
                  animationDuration={1400}
                  animationEasing="ease-out"
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={false}
                  name="predicted"
                  isAnimationActive
                  animationDuration={1400}
                  animationEasing="ease-out"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
        {(eventNote || weatherNote) && (
          <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
            {eventNote ? <p>{eventNote}</p> : null}
            {weatherNote ? <p>{weatherNote}</p> : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
