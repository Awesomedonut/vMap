import { GeoJSONSource, Map as MLMap, MapMouseEvent } from "maplibre-gl";
import { MutableRefObject, useRef, useState } from "react";
import { WorldManifest } from "../api";
import { distanceKm } from "../lib/geo";

export interface MeasureState {
  points: [number, number][]; // lnglat
  km: number | null;
}

const EMPTY: MeasureState = { points: [], km: null };

/**
 * The straight-line measure tool: toggled on, it turns map clicks into a
 * two-point distance (drawn via the map's "measure" source).
 */
export function useMeasure(
  mapRef: MutableRefObject<MLMap | undefined>,
  world: WorldManifest | null
) {
  const [measuring, setMeasuring] = useState(false);
  const measuringRef = useRef(false);
  const [measure, setMeasure] = useState<MeasureState>(EMPTY);
  const measureRef = useRef<MeasureState>(EMPTY);

  function apply(next: MeasureState): void {
    measureRef.current = next;
    setMeasure(next);
    const src = mapRef.current?.getSource("measure") as GeoJSONSource | undefined;
    src?.setData({
      type: "FeatureCollection",
      features:
        next.points.length === 2
          ? [{ type: "Feature", geometry: { type: "LineString", coordinates: next.points }, properties: {} }]
          : [],
    });
  }

  function handleMapClick(e: MapMouseEvent): void {
    if (!measuringRef.current || !world) return;
    const clicked: [number, number] = [e.lngLat.lng, e.lngLat.lat];
    const prev = measureRef.current.points;
    const points = prev.length >= 2 ? [clicked] : [...prev, clicked];
    const km =
      points.length === 2 ? distanceKm(points[0], points[1], world.settings.world_km) : null;
    apply({ points, km });
  }

  function toggle(): void {
    const on = !measuring;
    setMeasuring(on);
    measuringRef.current = on;
    if (!on) apply(EMPTY);
  }

  return { measuring, measuringRef, measure, toggle, handleMapClick };
}
