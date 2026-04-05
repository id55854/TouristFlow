"use client";

import { Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";

export function AiBriefCard({
  brief,
  loading,
  error,
}: {
  brief: string | null;
  loading: boolean;
  error?: string | null;
}) {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-amber-400" />
          AI daily brief
        </CardTitle>
        <Button variant="outline" size="sm" className="text-xs" disabled>
          Full brief
        </Button>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[92%]" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[80%]" />
          </div>
        ) : error ? (
          <p className="text-sm text-rose-400">{error}</p>
        ) : (
          <ScrollArea className="h-[220px] pr-3">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
              {brief ?? "No brief available."}
            </p>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
