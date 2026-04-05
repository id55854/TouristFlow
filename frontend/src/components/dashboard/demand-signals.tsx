"use client";

import { Building2, CalendarDays, Plane, Search, Sun } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export type SignalRow = {
  key: string;
  label: string;
  value: number;
  hint: string;
  icon: "weather" | "flight" | "event" | "trend" | "comp";
};

function Bar({ value }: { value: number }) {
  const v = Math.min(100, Math.max(0, value));
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
      <div
        className="h-full rounded-full bg-primary transition-[width] duration-700 ease-out"
        style={{ width: `${v}%` }}
      />
    </div>
  );
}

const iconMap = {
  weather: Sun,
  flight: Plane,
  event: CalendarDays,
  trend: Search,
  comp: Building2,
};

export function DemandSignals({
  rows,
  loading,
}: {
  rows: SignalRow[];
  loading: boolean;
}) {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle>Demand signals</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : (
          rows.map((row) => {
            const Ico = iconMap[row.icon];
            return (
              <div key={row.key} className="flex items-start gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary text-muted-foreground">
                  <Ico className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center justify-between gap-2 text-sm">
                    <span className="font-medium">{row.label}</span>
                    <span className="tabular-nums text-muted-foreground">
                      {row.value.toFixed(0)}/100
                    </span>
                  </div>
                  <Bar value={row.value} />
                  <p className="text-xs text-muted-foreground">{row.hint}</p>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
