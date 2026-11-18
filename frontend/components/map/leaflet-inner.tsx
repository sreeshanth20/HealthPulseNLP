"use client";

import * as React from "react";
import { MapContainer, CircleMarker, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const URGENCY_COLORS: Record<string, string> = {
  LOW: "#84cc16",
  MEDIUM: "#facc15",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export interface MapPoint {
  lat: number;
  lng: number;
  weight?: number;
  kind?: string;
  category?: string | null;
  urgency?: string | null;
  district?: string | null;
  id?: number | null;
}

export default function LeafletHeatMap({
  points,
  center,
}: {
  points: MapPoint[];
  center: [number, number];
}) {
  return (
    <MapContainer center={center} zoom={12} scrollWheelZoom className="h-full w-full">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {points.map((p, i) => {
        const color = URGENCY_COLORS[p.urgency ?? "MEDIUM"] ?? "#0d9488";
        return (
          <CircleMarker
            key={`${p.kind}-${p.id ?? i}`}
            center={[p.lat, p.lng]}
            radius={6 + (p.weight ?? 1) * 2.2}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.55, weight: 1 }}
          >
            <Tooltip direction="top">
              <div style={{ fontSize: 12 }}>
                <strong>{p.kind === "report" ? "Symptom report" : "Civic complaint"}</strong>
                {p.category ? <div>{p.category.replace(/_/g, " ")}</div> : null}
                {p.district ? <div>{p.district}</div> : null}
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
