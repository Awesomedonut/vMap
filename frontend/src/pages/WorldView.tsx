import { MapMouseEvent } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, WorldManifest } from "../api";
import MeasureReadout from "../components/MeasureReadout";
import SearchBox from "../components/SearchBox";
import { useMeasure } from "../hooks/useMeasure";
import { useWorldMap } from "../hooks/useWorldMap";

export default function WorldView() {
  const { slug = "" } = useParams();
  const mapDiv = useRef<HTMLDivElement>(null);
  const [world, setWorld] = useState<WorldManifest | null>(null);

  useEffect(() => {
    api.getWorld(slug).then(setWorld);
  }, [slug]);

  // the map calls back through refs so handlers stay current without re-creating the map
  const clickHandler = useRef<(e: MapMouseEvent) => void>(() => {});
  const suppressPopups = useRef(false);
  const mapRef = useWorldMap(mapDiv, world, clickHandler, suppressPopups);
  const { measuring, measuringRef, measure, toggle, handleMapClick } = useMeasure(mapRef, world);
  clickHandler.current = handleMapClick;
  suppressPopups.current = measuringRef.current;

  function flyTo(f: GeoJSON.Feature): void {
    const [lng, lat] = (f.geometry as GeoJSON.Point).coordinates;
    mapRef.current?.flyTo({ center: [lng, lat], zoom: 5.2 });
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
        <button className={`measure-btn${measuring ? " active" : ""}`} onClick={toggle}>
          📏 Measure
        </button>
        <SearchBox slug={slug} onPick={flyTo} />
      </div>
      {measuring && <MeasureReadout km={measure.km} />}
    </div>
  );
}
