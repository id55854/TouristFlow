import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CompetitorsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Competitors</h1>
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Competitive set</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Rate comparison and positioning views will be added here.
        </CardContent>
      </Card>
    </div>
  );
}
