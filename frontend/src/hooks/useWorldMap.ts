import maplibregl, { Map as MLMap, MapMouseEvent, Popup } from "maplibre-gl";
import { MutableRefObject, RefObject, useEffect, useRef } from "react";
import { api, WorldManifest } from "../api";

const GLYPHS_URL = "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf";
const WORLD_BOUNDS: [[number, number], [number, number]] = [[-179, -78], [179, 78]];

/**
 * Creates the MapLibre map for a world: terrain raster source, settlement
 * dot + label layers, click popups, and an empty "measure" line source.
 * Returns a ref to the live map instance.
 */
export function useWorldMap(
  container: RefObject<HTMLDivElement>,
  world: WorldManifest | null,
  onClick: MutableRefObject<(e: MapMouseEvent) => void>,
  suppressPopups: MutableRefObject<boolean>
): MutableRefObject<MLMap | undefined> {
  const mapRef = useRef<MLMap>();

  useEffect(() => {
    if (!world || !container.current) return;
    const map = createBaseMap(container.current, world);
    mapRef.current = map;

    map.on("load", async () => {
      addMeasureLayer(map);
      await addSettlementLayers(map, world.slug);
      wireSettlementPopups(map, suppressPopups);
      map.on("click", (e) => onClick.current(e));
    });

    return () => {
      map.remove();
      mapRef.current = undefined;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [world?.slug]);

  return mapRef;
}

function createBaseMap(container: HTMLDivElement, world: WorldManifest): MLMap {
  const map = new maplibregl.Map({
    container,
    style: {
      version: 8,
      glyphs: GLYPHS_URL,
      sources: {
        terrain: {
          type: "raster",
          tiles: [`${location.origin}/tiles/${world.slug}/{z}/{x}/{y}.png`],
          tileSize: 256,
          minzoom: 0,
          maxzoom: world.max_zoom ?? 7,
        },
      },
      layers: [{ id: "terrain", type: "raster", source: "terrain" }],
    },
    center: [0, 0],
    zoom: 1.5,
    renderWorldCopies: false,
    attributionControl: false,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
  map.fitBounds(WORLD_BOUNDS, { padding: 24, duration: 0 });
  return map;
}

function addMeasureLayer(map: MLMap): void {
  map.addSource("measure", {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] },
  });
  map.addLayer({
    id: "measure-line",
    type: "line",
    source: "measure",
    paint: { "line-color": "#c2452d", "line-width": 3, "line-dasharray": [1.5, 1.2] },
  });
}

async function addSettlementLayers(map: MLMap, slug: string): Promise<void> {
  const features = await api.getFeatures(slug);
  map.addSource("settlements", { type: "geojson", data: features });
  map.addLayer({
    id: "settlement-dots",
    type: "circle",
    source: "settlements",
    paint: {
      "circle-radius": ["match", ["get", "kind"], "capital", 7, "town", 5, 3.5],
      "circle-color": ["match", ["get", "kind"], "capital", "#c2452d", "town", "#1e2733", "#5a6472"],
      "circle-stroke-color": "#f5f1e8",
      "circle-stroke-width": 1.5,
    },
  });
  map.addLayer({
    id: "settlement-labels",
    type: "symbol",
    source: "settlements",
    layout: {
      "text-field": ["get", "name"],
      "text-font": ["Noto Sans Regular"],
      "text-size": ["match", ["get", "kind"], "capital", 15, "town", 12.5, 11],
      "text-offset": [0, 1.1],
      "text-anchor": "top",
    },
    paint: {
      "text-color": "#1e2733",
      "text-halo-color": "#f5f1e8",
      "text-halo-width": 1.4,
    },
  });
}

function wireSettlementPopups(map: MLMap, suppress: MutableRefObject<boolean>): void {
  map.on("click", "settlement-dots", (e) => {
    if (suppress.current) return;
    const f = e.features?.[0];
    if (!f) return;
    const p = f.properties as { name: string; kind: string; population: number };
    new Popup({ closeButton: false })
      .setLngLat((f.geometry as GeoJSON.Point).coordinates as [number, number])
      .setHTML(
        `<strong>${p.name}</strong><div>${p.kind} · pop. ${Number(p.population).toLocaleString()}</div>`
      )
      .addTo(map);
  });
  map.on("mouseenter", "settlement-dots", () => (map.getCanvas().style.cursor = "pointer"));
  map.on("mouseleave", "settlement-dots", () => (map.getCanvas().style.cursor = ""));
}
