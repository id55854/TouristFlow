"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Building2,
  Cloud,
  Globe2,
  Gavel,
  GitBranch,
  Plane,
  Radio,
  Road,
  Search,
  TrendingUp,
} from "lucide-react";
import { format } from "date-fns";
import { appNow } from "@/lib/demo";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  HOLDING,
  PROPERTIES,
  FUSION_LEAD,
  WEATHER_ZONES,
  FLIGHT_SIGNALS,
  ROAD_SIGNALS,
  MACRO_SIGNALS,
  EVENT_SIGNALS,
  SEARCH_TRENDS,
  COMPETITOR_PULSE,
  REGULATORY_SIGNALS,
  CORRELATION_LABELS,
  correlationMatrix,
} from "@/lib/portfolio-fusion-mock";

const CoastalHoldingsMap = dynamic(
  () =>
    import("@/components/portfolio/coastal-holdings-map").then((m) => m.CoastalHoldingsMap),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
  }
);

function heatColor(v: number): string {
  if (v >= 0.75) return "bg-emerald-500/70";
  if (v >= 0.35) return "bg-emerald-500/35";
  if (v >= 0) return "bg-slate-500/25";
  if (v >= -0.35) return "bg-rose-500/30";
  return "bg-rose-500/55";
}

const trendChartData = SEARCH_TRENDS.map((t, i) => ({
  name: `S${i + 1}`,
  full: `${t.market} — ${t.topic}`,
  index: t.index,
}));

export function PortfolioFusionPage() {
  const matrix = React.useMemo(() => correlationMatrix(), []);
  const asOf = format(appNow(), "MMM d, yyyy");

  return (
    <div className="mx-auto max-w-[1500px] space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">Portfolio fusion</h1>
            <Badge variant="secondary" className="font-normal">
              Prototype
            </Badge>
          </div>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            {HOLDING.brand} — {HOLDING.legalName}. Synthetic cross-signal layer for{" "}
            {HOLDING.portfolioRooms.toLocaleString()} keys across the Adriatic coast. Data is mocked
            for demo; map tiles © OpenStreetMap contributors.
          </p>
          <p className="mt-2 text-xs text-muted-foreground">As of {asOf} (demo clock).</p>
        </div>
      </div>

      <Card className="border-primary/30 bg-gradient-to-br from-primary/5 via-card to-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <GitBranch className="h-5 w-5 text-primary" />
            Fused decision — portfolio level
          </CardTitle>
          <CardDescription>
            Confidence {(FUSION_LEAD.confidence * 100).toFixed(0)}% · combines macro, routes,
            weather, roads, search, comps
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm font-medium leading-snug">{FUSION_LEAD.title}</p>
          <p className="text-sm leading-relaxed text-muted-foreground">{FUSION_LEAD.summary}</p>
          <ul className="list-inside list-decimal space-y-1 text-sm text-muted-foreground">
            {FUSION_LEAD.actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
          <div className="flex flex-wrap gap-1.5 pt-2">
            {FUSION_LEAD.signalRefs.map((s) => (
              <Badge key={s} variant="outline" className="font-mono text-[10px]">
                {s}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Globe2 className="h-4 w-4" />
              Coastal holdings map
            </CardTitle>
            <CardDescription>
              OpenStreetMap basemap · circle size encodes scale; colour by occupancy band
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CoastalHoldingsMap properties={PROPERTIES} />
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="h-4 w-4" />
              Property-level operations (PMS snapshot)
            </CardTitle>
            <CardDescription>ADR, occupancy, RevPAR, guest mix — illustrative blend</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full min-w-[520px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="pb-2 pr-2 font-medium">Property</th>
                  <th className="pb-2 pr-2 font-medium">Rooms</th>
                  <th className="pb-2 pr-2 font-medium">ADR</th>
                  <th className="pb-2 pr-2 font-medium">Occ</th>
                  <th className="pb-2 pr-2 font-medium">RevPAR</th>
                  <th className="pb-2 font-medium">Top markets</th>
                </tr>
              </thead>
              <tbody>
                {PROPERTIES.map((p) => (
                  <tr key={p.id} className="border-b border-border/60 last:border-0">
                    <td className="py-2 pr-2">
                      <div className="font-medium leading-tight">{p.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {p.city} · {p.region}
                      </div>
                    </td>
                    <td className="py-2 pr-2 tabular-nums">{p.rooms}</td>
                    <td className="py-2 pr-2 tabular-nums">€{p.adrEur}</td>
                    <td className="py-2 pr-2 tabular-nums">{(p.occPct * 100).toFixed(0)}%</td>
                    <td className="py-2 pr-2 tabular-nums">€{p.revparEur}</td>
                    <td className="py-2 text-xs text-muted-foreground">
                      DE {(p.guestMix.de * 100).toFixed(0)}% · UK {(p.guestMix.uk * 100).toFixed(0)}%
                      · AT {(p.guestMix.at * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Cloud className="h-4 w-4 text-sky-400" />
              Weather intelligence
            </CardTitle>
            <CardDescription>Beach-day score, storms, UV, sea</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            {WEATHER_ZONES.map((z) => (
              <div key={z.zone} className="rounded-md border border-border/80 bg-muted/20 p-2">
                <p className="font-medium text-foreground">{z.zone}</p>
                <p className="text-muted-foreground">
                  Beach {z.beachDayScore}/100 · UV {z.uvPeak} · Sea {z.seaTempC}°C · Gusts{" "}
                  {z.windGustKmh} km/h
                </p>
                <p className="mt-1">
                  Storm 72h:{" "}
                  <span
                    className={
                      z.stormRisk72h === "low"
                        ? "text-emerald-500"
                        : z.stormRisk72h === "moderate"
                          ? "text-amber-500"
                          : "text-rose-500"
                    }
                  >
                    {z.stormRisk72h}
                  </span>
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Plane className="h-4 w-4 text-violet-400" />
              Airports & routes
            </CardTitle>
            <CardDescription>Capacity proxy by route — load & YoY seats</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            {FLIGHT_SIGNALS.map((f) => (
              <div
                key={f.route}
                className="rounded-md border border-border/80 bg-muted/20 p-2 leading-relaxed"
              >
                <p className="font-medium">
                  {f.route}{" "}
                  <span className="text-muted-foreground">({f.originCountry})</span>
                </p>
                <p className="text-muted-foreground">
                  Load {f.loadFactorPct}% · Seats YoY {f.yoySeatsPct > 0 ? "+" : ""}
                  {f.yoySeatsPct}%
                </p>
                {f.alert ? <p className="mt-1 text-amber-500">{f.alert}</p> : null}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Road className="h-4 w-4 text-amber-600" />
              Roads & drive markets
            </CardTitle>
            <CardDescription>Highway pressure, borders, fuel</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              A1 index <span className="font-semibold tabular-nums">{ROAD_SIGNALS.a1ZagrebSplitIndex}</span>{" "}
              <span className="text-muted-foreground">({ROAD_SIGNALS.a1VsYA})</span>
            </p>
            <p className="text-muted-foreground">
              HR–SI border ~{ROAD_SIGNALS.borderHrSi.paxPerDay.toLocaleString()} pax/d{" "}
              {ROAD_SIGNALS.borderHrSi.wow}
            </p>
            <p className="text-muted-foreground">
              HR–BiH ~{ROAD_SIGNALS.borderHrBih.paxPerDay.toLocaleString()} pax/d{" "}
              {ROAD_SIGNALS.borderHrBih.wow}
            </p>
            <p>
              Diesel €{ROAD_SIGNALS.dieselEurL}/L — <span className="text-muted-foreground">{ROAD_SIGNALS.dieselWow}</span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              Macro & FX
            </CardTitle>
            <CardDescription>Source-market pressure</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            {MACRO_SIGNALS.map((m) => (
              <div key={m.label} className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-medium">{m.label}</span>
                <span className="tabular-nums text-muted-foreground">{m.value}</span>
                <span
                  className={
                    m.impact === "tailwind"
                      ? "text-emerald-500"
                      : m.impact === "headwind"
                        ? "text-rose-400"
                        : "text-muted-foreground"
                  }
                >
                  {m.delta}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Radio className="h-4 w-4" />
              Events & cruise pressure
            </CardTitle>
            <CardDescription>Festivals, sport, turn-day clusters</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {EVENT_SIGNALS.map((e) => (
                <li
                  key={e.name}
                  className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border/50 pb-2 last:border-0"
                >
                  <span>
                    <span className="font-medium">{e.name}</span>{" "}
                    <span className="text-muted-foreground">· {e.location}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {e.start}–{e.end} · {e.demandUplift} · {e.type}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Search className="h-4 w-4" />
              Search demand (by source market)
            </CardTitle>
            <CardDescription>Normalized interest — illustrative</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4 space-y-1 text-xs">
              {SEARCH_TRENDS.map((t) => (
                <div key={`${t.market}-${t.topic}`} className="flex justify-between gap-2">
                  <span className="text-muted-foreground">
                    {t.market}: {t.topic}
                  </span>
                  <span className="tabular-nums">
                    {t.index} <span className="text-muted-foreground">({t.wow} WoW)</span>
                  </span>
                </div>
              ))}
            </div>
            <div className="h-[200px] w-full min-w-0">
              <ResponsiveContainer width="100%" height={200} minHeight={200}>
                <BarChart data={trendChartData} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--popover))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    labelFormatter={(_label, payload) => {
                      const p = payload?.[0]?.payload as { full?: string } | undefined;
                      return p?.full ?? "";
                    }}
                    formatter={(value) => [`${value ?? ""}`, "Index"]}
                  />
                  <Bar dataKey="index" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Competitor intelligence</CardTitle>
            <CardDescription>Median BAR movement vs comp sets</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {COMPETITOR_PULSE.map((c) => (
              <div
                key={c.compSet}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border/60 bg-muted/15 px-3 py-2"
              >
                <span className="font-medium">{c.compSet}</span>
                <span className="tabular-nums">€{c.medianBarEur}</span>
                <span className={c.wowPct >= 0 ? "text-emerald-500" : "text-rose-400"}>
                  {c.wowPct >= 0 ? "+" : ""}
                  {c.wowPct}% WoW
                </span>
                <Badge variant="outline" className="text-[10px] capitalize">
                  {c.sentiment}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Gavel className="h-4 w-4" />
              Government & regulatory
            </CardTitle>
            <CardDescription>Visa, EU funds, route policy</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {REGULATORY_SIGNALS.map((g) => (
              <div key={g.topic} className="rounded-md border border-border/60 bg-muted/15 p-3">
                <p className="font-medium">{g.topic}</p>
                <p className="text-muted-foreground">{g.status}</p>
                <p className="mt-1 text-xs text-muted-foreground">Relevance: {g.relevance}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Cross-category correlation (prototype)</CardTitle>
          <CardDescription>
            Stylized correlation matrix — where fused signals reinforce each other for portfolio
            steering
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-center text-[10px]">
            <thead>
              <tr>
                <th className="border border-border bg-muted/40 p-1 text-left font-medium text-muted-foreground" />
                {CORRELATION_LABELS.map((l) => (
                  <th
                    key={l}
                    className="max-w-[3.5rem] border border-border bg-muted/40 p-1 font-normal leading-tight text-muted-foreground"
                  >
                    {l}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((row, i) => (
                <tr key={CORRELATION_LABELS[i]}>
                  <th className="border border-border bg-muted/30 p-1 text-left font-normal text-muted-foreground">
                    {CORRELATION_LABELS[i]}
                  </th>
                  {row.map((cell, j) => (
                    <td
                      key={`${i}-${j}`}
                      title={`${CORRELATION_LABELS[i]} × ${CORRELATION_LABELS[j]} = ${cell.toFixed(2)}`}
                      className={`border border-border p-1 tabular-nums ${heatColor(cell)}`}
                    >
                      {cell.toFixed(2)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-xs text-muted-foreground">
            Values are illustrative coefficients for demo storytelling only; production would use
            rolling windows and property-cluster segmentation.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
