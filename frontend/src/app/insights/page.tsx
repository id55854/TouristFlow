"use client";

import useSWR from "swr";
import { useProperty } from "@/components/providers/property-context";
import { fetchJson } from "@/lib/api";
import { AiBriefCard } from "@/components/dashboard/ai-brief-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type BriefResponse = { brief: string };

async function loadBrief(propertyId: number) {
  return fetchJson<BriefResponse>(
    `/api/v1/insights/daily-brief?property_id=${propertyId}`
  );
}

export default function InsightsPage() {
  const { propertyId } = useProperty();
  const { data, error, isLoading } = useSWR(
    ["insights-brief", propertyId],
    () => loadBrief(propertyId),
    { revalidateOnFocus: false }
  );

  const briefText = data?.brief?.trim() ? data.brief : null;
  const briefErr =
    error && !data?.brief
      ? "Could not load insights. Enable NEXT_PUBLIC_MOCK_API=1 or start the API."
      : null;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">AI insights</h1>
        <p className="text-sm text-muted-foreground">
          Gemini-style narrative briefs grounded in your occupancy, demand, and comp positioning.
        </p>
      </div>

      <AiBriefCard brief={briefText} loading={isLoading} error={briefErr} />

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Roadmap</CardTitle>
          <CardDescription>When the backend is connected with a live LLM key:</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <ul className="list-inside list-disc space-y-1">
            <li>Explain price changes by room type with competitor context.</li>
            <li>Weekly market digests and anomaly alerts.</li>
            <li>Natural-language Q&amp;A over your property&apos;s KPI history.</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
