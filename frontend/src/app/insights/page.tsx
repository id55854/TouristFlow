import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function InsightsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">AI insights</h1>
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Gemini-powered analysis</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Extended briefs, price explanations, and market analysis will be surfaced here.
        </CardContent>
      </Card>
    </div>
  );
}
