import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CalendarPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Calendar</h1>
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Events &amp; pricing calendar</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Month view with events overlay and demand coloring will be added here.
        </CardContent>
      </Card>
    </div>
  );
}
