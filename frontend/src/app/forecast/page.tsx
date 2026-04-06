"use client";

import useSWR from "swr";
import { useProperty } from "@/components/providers/property-context";
import { fetchJson } from "@/lib/api";
import { isDemoApril2026 } from "@/lib/demo";
import { ForecastChart, type ForecastPoint } from "@/components/dashboard/forecast-chart";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ForecastOccResponse = {
  points: Array<{
    date: string;
    predicted: number;
    lower_bound: number;
    upper_bound: number;
  }>;
};

async function loadForecast(propertyId: number) {
  return fetchJson<ForecastOccResponse>(
    `/api/v1/forecast/occupancy?property_id=${propertyId}&horizon=30`
  );
}

export default function ForecastPage() {
  const { propertyId } = useProperty();
  const { data, error, isLoading } = useSWR(
    ["forecast-page", propertyId],
    () => loadForecast(propertyId),
    { revalidateOnFocus: false }
  );

  const points: ForecastPoint[] =
    data?.points?.map((p) => ({
      date: p.date,
      predicted: p.predicted,
      lower_bound: p.lower_bound,
      upper_bound: p.upper_bound,
    })) ?? [];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Forecast</h1>
        <p className="text-sm text-muted-foreground">
          Thirty-day occupancy projection with confidence band (same engine as the dashboard chart).
        </p>
      </div>

      <ForecastChart
        points={points}
        loading={isLoading}
        eventNote={
          isDemoApril2026()
            ? "Apr 18–20: Dubrovnik Wine Festival — model lifts occupancy band on event nights."
            : "Events overlay ties to regional calendars when the API is connected."
        }
        weatherNote={
          isDemoApril2026()
            ? "Spring coastal season — willingness-to-pay rises on premium room types."
            : "Weather scores blend synthetic coastal series in prototype mode."
        }
      />

      {error ? (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-base">Could not load forecast</CardTitle>
            <CardDescription>
              Check NEXT_PUBLIC_API_URL or enable NEXT_PUBLIC_MOCK_API=1 for a static demo.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>How to read this</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>
            The solid line is the point forecast; the shaded band is lower/upper bounds from the
            forecaster. Use Pricing to translate occupancy into recommended nightly rates by room
            type.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
