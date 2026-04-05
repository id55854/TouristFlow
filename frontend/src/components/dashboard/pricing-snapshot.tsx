"use client";

import { ArrowUpRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

export type PricingRow = {
  roomType: string;
  recommended: number;
  changePct: number;
};

export function PricingSnapshot({
  rows,
  loading,
}: {
  rows: PricingRow[];
  loading: boolean;
}) {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle>Pricing snapshot</CardTitle>
        <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[85%]" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Room type</TableHead>
                <TableHead className="text-right">Rec. rate</TableHead>
                <TableHead className="text-right">Δ</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.roomType}>
                  <TableCell className="font-medium">{r.roomType}</TableCell>
                  <TableCell className="text-right">€{r.recommended.toFixed(0)}</TableCell>
                  <TableCell
                    className={`text-right tabular-nums ${
                      r.changePct >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {r.changePct >= 0 ? "▲" : "▼"} {Math.abs(r.changePct).toFixed(0)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
