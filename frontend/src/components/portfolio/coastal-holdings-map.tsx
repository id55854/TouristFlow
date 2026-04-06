"use client";

import * as React from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import type { CoastalProperty } from "@/lib/portfolio-fusion-mock";
import "leaflet/dist/leaflet.css";

function markerColor(occ: number): string {
  if (occ >= 0.7) return "#10b981";
  if (occ >= 0.6) return "#38bdf8";
  return "#f59e0b";
}

export function CoastalHoldingsMap({ properties }: { properties: CoastalProperty[] }) {
  const center: [number, number] = [43.65, 16.25];

  return (
    <div className="relative z-0 h-[420px] w-full overflow-hidden rounded-lg border border-border">
      <MapContainer
        center={center}
        zoom={7}
        className="h-full w-full"
        scrollWheelZoom
        aria-label="Coastal holdings map — OpenStreetMap"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {properties.map((p) => (
          <CircleMarker
            key={p.id}
            center={[p.lat, p.lng]}
            radius={9}
            pathOptions={{
              color: "#0f172a",
              weight: 2,
              fillColor: markerColor(p.occPct),
              fillOpacity: 0.85,
            }}
          >
            <Popup>
              <div className="min-w-[200px] text-sm">
                <p className="font-semibold text-foreground">{p.name}</p>
                <p className="text-muted-foreground">
                  {p.city} · {p.region}
                </p>
                <p className="mt-1 tabular-nums">
                  {p.rooms} rooms · ADR €{p.adrEur} · Occ {(p.occPct * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-muted-foreground">
                  RevPAR €{p.revparEur} · PMS {p.pmsHealth}
                </p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
