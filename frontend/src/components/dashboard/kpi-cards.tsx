"use client";

import { TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCountUp } from "@/hooks/use-count-up";

export type KpiData = {
  occupancy: number;
  adr: number;
  revpar: number;
  uplift: number;
  occupancyDeltaPp?: number;
  adrDeltaPct?: number;
  revparDeltaPct?: number;
};

function Delta({
  value,
  suffix,
  invert,
}: {
  value?: number;
  suffix: string;
  invert?: boolean;
}) {
  if (value == null || Number.isNaN(value)) {
    return <span className="text-xs text-muted-foreground">—</span>;
  }
  const good = invert ? value < 0 : value > 0;
  const Icon = good ? TrendingUp : TrendingDown;
  return (
    <span
      className={`inline-flex items-center gap-0.5 text-xs ${
        good ? "text-emerald-400" : "text-rose-400"
      }`}
    >
      <Icon className="h-3 w-3" />
      {value > 0 ? "+" : ""}
      {value.toFixed(1)}
      {suffix}
    </span>
  );
}

export function KpiCards({
  data,
  loading,
}: {
  data: KpiData | null;
  loading: boolean;
}) {
  if (loading || !data) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="border-border bg-card">
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-28" />
            </CardHeader>
            <CardContent className="space-y-2">
              <Skeleton className="h-9 w-24" />
              <Skeleton className="h-3 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCardOccupancy data={data} />
      <KpiCardAdr data={data} />
      <KpiCardRevpar data={data} />
      <KpiCardUplift data={data} />
    </div>
  );
}

function KpiCardOccupancy({ data }: { data: KpiData }) {
  const target = data.occupancy * 100;
  const v = useCountUp(target, 1200);
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Today · Occupancy
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-3xl font-semibold tracking-tight tabular-nums">
          {v.toFixed(1)}%
        </p>
        <Delta value={data.occupancyDeltaPp} suffix="pp" />
      </CardContent>
    </Card>
  );
}

function KpiCardAdr({ data }: { data: KpiData }) {
  const v = useCountUp(data.adr, 1200);
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Today · ADR
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-3xl font-semibold tracking-tight tabular-nums">
          €{v.toFixed(0)}
        </p>
        <Delta value={data.adrDeltaPct} suffix="%" />
      </CardContent>
    </Card>
  );
}

function KpiCardRevpar({ data }: { data: KpiData }) {
  const v = useCountUp(data.revpar, 1200);
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Today · RevPAR
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-3xl font-semibold tracking-tight tabular-nums">
          €{v.toFixed(0)}
        </p>
        <Delta value={data.revparDeltaPct} suffix="%" />
      </CardContent>
    </Card>
  );
}

function KpiCardUplift({ data }: { data: KpiData }) {
  const v = useCountUp(data.uplift, 1400);
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Revenue uplift (est.)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-3xl font-semibold tracking-tight tabular-nums text-emerald-400">
          +€{Math.round(v).toLocaleString("en-US")}
        </p>
        <span className="text-xs text-muted-foreground">this month · model</span>
      </CardContent>
    </Card>
  );
}
