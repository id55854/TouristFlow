"use client";

import useSWR from "swr";
import { useProperty } from "@/components/providers/property-context";
import { fetchJson } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

type CompetitorsListResponse = {
  property_id: number;
  competitors: Array<{
    id: number;
    name: string;
    stars: number | null;
    rooms: number | null;
    is_primary: boolean;
    latest_rate_eur: number | null;
    rate_date: string | null;
    available: boolean | null;
  }>;
};

async function loadCompetitors(propertyId: number) {
  return fetchJson<CompetitorsListResponse>(
    `/api/v1/competitors?property_id=${propertyId}`
  );
}

export default function CompetitorsPage() {
  const { propertyId } = useProperty();
  const { data, error, isLoading } = useSWR(
    ["competitors-list", propertyId],
    () => loadCompetitors(propertyId),
    { revalidateOnFocus: false }
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Competitors</h1>
        <p className="text-sm text-muted-foreground">
          Competitive set snapshot with latest scraped or partner rates (demo data when mock mode is on).
        </p>
      </div>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Competitive set</CardTitle>
          <CardDescription>
            Primary comp is highlighted. Rates are indicative nightly BAR in EUR.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <p className="text-sm text-destructive">
              Could not load competitors. Enable NEXT_PUBLIC_MOCK_API=1 or start the API.
            </p>
          ) : !data?.competitors?.length ? (
            <p className="text-sm text-muted-foreground">No competitors configured.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Property</TableHead>
                  <TableHead className="text-center">Stars</TableHead>
                  <TableHead className="text-right">Rooms</TableHead>
                  <TableHead className="text-right">Latest rate</TableHead>
                  <TableHead className="text-right">As of</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.competitors.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">
                      <div className="flex flex-wrap items-center gap-2">
                        {c.name}
                        {c.is_primary ? (
                          <Badge variant="secondary" className="text-[10px]">
                            Primary
                          </Badge>
                        ) : null}
                      </div>
                    </TableCell>
                    <TableCell className="text-center tabular-nums">
                      {c.stars != null ? `${c.stars}★` : "—"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {c.rooms != null ? c.rooms : "—"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {c.latest_rate_eur != null
                        ? `€${c.latest_rate_eur.toFixed(0)}`
                        : "—"}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {c.rate_date ?? "—"}
                    </TableCell>
                    <TableCell className="text-center">
                      {c.available === false ? (
                        <span className="text-amber-500">Limited</span>
                      ) : (
                        <span className="text-emerald-500">Open</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
