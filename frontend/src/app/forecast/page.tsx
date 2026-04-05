import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ForecastPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Forecast</h1>
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Occupancy &amp; ADR forecasts</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Detailed forecast views will connect here. Use the Dashboard for the 30-day occupancy chart.
        </CardContent>
      </Card>
    </div>
  );
}
