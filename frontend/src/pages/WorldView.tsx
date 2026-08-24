import maplibregl, { Map as MLMap, MapMouseEvent, Popup } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, WorldManifest } from "../api";

/** lon/lat -> normalized world coords (the same [0,1]^2 square the backend uses) */
function toNorm(lng: number, lat: number): [number, number] {
  const x = (lng + 180) / 360;
  const rad = (lat * Math.PI) / 180;
  const y = (1 - Math.asinh(Math.tan(rad)) / Math.PI) / 2;
  return [x, y];
}

const MODES = [
  { label: "on foot", kmPerDay: 30 },
  { label: "by horse", kmPerDay: 60 },
  { label: "by ship", kmPerDay: 150 },
];

interface MeasureState {
  points: [number, number][]; // lnglat
  km: number | null;
}

export default function WorldView() {
  const { slug = "" } = useParams();
  const mapDiv = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap>();
  const [world, setWorld] = useState<WorldManifest | null>(null);
  const [measuring, setMeasuring] = useState(false);
  const measuringRef = useRef(false);
  const [measure, setMeasure] = useState<MeasureState>({ points: [], km: null });
  const measureRef = useRef<MeasureState>({ points: [], km: null });
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GeoJSON.Feature[]>([]);

  useEffect(() => {
    api.getWorld(slug).then(setWorld);
  }, [slug]);

  // --- map setup -----------------------------------------------------------
  useEffect(() => {
    if (!world || !mapDiv.current) return;
    const map = new maplibregl.Map({
      container: mapDiv.current,
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
          terrain: {
            type: "raster",
            tiles: [`${location.origin}/tiles/${slug}/{z}/{x}/{y}.png`],
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
    mapRef.current = map;
    map.fitBounds([[-179, -78], [179, 78]], { padding: 24, duration: 0 });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    map.on("load", async () => {
      const features = await api.getFeatures(slug);
      map.addSource("settlements", { type: "geojson", data: features });
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
      map.addLayer({
        id: "settlement-dots",
        type: "circle",
        source: "settlements",
        paint: {
          "circle-radius": [
            "match", ["get", "kind"],
            "capital", 7, "town", 5, 3.5,
          ],
          "circle-color": [
            "match", ["get", "kind"],
            "capital", "#c2452d", "town", "#1e2733", "#5a6472",
          ],
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

      map.on("click", "settlement-dots", (e) => {
        if (measuringRef.current) return;
        const f = e.features?.[0];
        if (!f) return;
        const p = f.properties as { name: string; kind: string; population: number };
        new Popup({ closeButton: false })
          .setLngLat((f.geometry as GeoJSON.Point).coordinates as [number, number])
          .setHTML(
            `<strong>${p.name}</strong><div>${p.kind} · pop. ${Number(
              p.population
            ).toLocaleString()}</div>`
          )
          .addTo(map);
      });
      map.on("mouseenter", "settlement-dots", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "settlement-dots", () => (map.getCanvas().style.cursor = ""));
      map.on("click", onMapClick);
    });

    return () => {
      map.remove();
      mapRef.current = undefined;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [world?.slug]);

  // --- measure tool --------------------------------------------------------
  function onMapClick(e: MapMouseEvent) {
    if (!measuringRef.current || !mapRef.current) return;
    const prev = measureRef.current;
    const pts: [number, number][] =
      prev.points.length >= 2 ? [[e.lngLat.lng, e.lngLat.lat]] : [...prev.points, [e.lngLat.lng, e.lngLat.lat]];

    let km: number | null = null;
    if (pts.length === 2 && world) {
      const [ax, ay] = toNorm(pts[0][0], pts[0][1]);
      const [bx, by] = toNorm(pts[1][0], pts[1][1]);
      km = Math.hypot(bx - ax, by - ay) * world.settings.world_km;
    }
    const next = { points: pts, km };
    measureRef.current = next;
    setMeasure(next);

    const src = mapRef.current.getSource("measure") as maplibregl.GeoJSONSource;
    src?.setData({
      type: "FeatureCollection",
      features:
        pts.length === 2
          ? [{ type: "Feature", geometry: { type: "LineString", coordinates: pts }, properties: {} }]
          : [],
    });
  }

  function toggleMeasure() {
    const on = !measuring;
    setMeasuring(on);
    measuringRef.current = on;
    if (!on) {
      const empty = { points: [], km: null } as MeasureState;
      measureRef.current = empty;
      setMeasure(empty);
      (mapRef.current?.getSource("measure") as maplibregl.GeoJSONSource | undefined)?.setData({
        type: "FeatureCollection",
        features: [],
      });
    }
  }

  // --- search --------------------------------------------------------------
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    const t = window.setTimeout(
      () => api.search(slug, query).then((fc) => setResults(fc.features)),
      200
    );
    return () => window.clearTimeout(t);
  }, [query, slug]);

  function flyTo(f: GeoJSON.Feature) {
    const [lng, lat] = (f.geometry as GeoJSON.Point).coordinates;
    mapRef.current?.flyTo({ center: [lng, lat], zoom: 5.2 });
    setResults([]);
    setQuery("");
  }

  return (
    <div className="viewer">
      <div ref={mapDiv} className="map" />
      <div className="topbar">
        <Link to="/" className="back">← vMap</Link>
        <div className="title">
          {world?.name ?? slug}
          <small>seed {world?.seed}</small>
        </div>
        <button className={`measure-btn${measuring ? " active" : ""}`} onClick={toggleMeasure}>
          📏 Measure
        </button>
        <div className="searchbox">
          <input
            placeholder="Search places…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {results.length > 0 && (
            <div className="results">
              {results.map((f, i) => (
                <button key={i} onClick={() => flyTo(f)}>
                  {(f.properties as { name: string }).name}
                  <span>{(f.properties as { kind: string }).kind}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {measuring && (
        <div className="measure-readout">
          {measure.km === null ? (
            <div className="hint">Click two points to measure the distance between them</div>
          ) : (
            <>
              <strong>{Math.round(measure.km).toLocaleString()} km</strong>
              <div className="hint">
                {MODES.map((m) => `${Math.ceil(measure.km! / m.kmPerDay)} days ${m.label}`).join(" · ")}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
