"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import type { MapPoint } from "./leaflet-inner";

const LeafletHeatMap = dynamic(() => import("./leaflet-inner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[420px] w-full items-center justify-center rounded-lg border bg-muted text-sm text-muted-foreground">
      Loading map…
    </div>
  ),
});

export type { MapPoint };

export function HeatMap({
  points,
  center = [17.69, 83.215],
}: {
  points: MapPoint[];
  center?: [number, number];
}) {
  return (
    <div className="h-[420px] w-full overflow-hidden rounded-lg border">
      {points.length === 0 ? (
        <div className="flex h-full items-center justify-center bg-muted text-sm text-muted-foreground">
          No geo-located data in the selected window.
        </div>
      ) : (
        <LeafletHeatMap points={points} center={center} />
      )}
    </div>
  );
}

export default HeatMap;
