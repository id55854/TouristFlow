"use client";

import { format } from "date-fns";
import { Calendar } from "lucide-react";
import { appNow } from "@/lib/demo";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PROPERTIES, useProperty } from "@/components/providers/property-context";

export function Header() {
  const { propertyId, setPropertyId } = useProperty();
  const today = format(appNow(), "MMM d, yyyy");

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-card px-6">
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">Property</span>
        <Select
          value={String(propertyId)}
          onValueChange={(v) => setPropertyId(Number(v))}
        >
          <SelectTrigger className="w-[min(100vw-12rem,280px)] border-border bg-background">
            <SelectValue placeholder="Select property" />
          </SelectTrigger>
          <SelectContent>
            {PROPERTIES.map((p) => (
              <SelectItem key={p.id} value={String(p.id)}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Calendar className="h-4 w-4" />
        {today}
      </div>
    </header>
  );
}
