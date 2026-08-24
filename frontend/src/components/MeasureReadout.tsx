import { TRAVEL_MODES } from "../lib/geo";

export default function MeasureReadout({ km }: { km: number | null }) {
  if (km === null) {
    return (
      <div className="measure-readout">
        <div className="hint">Click two points to measure the distance between them</div>
      </div>
    );
  }
  return (
    <div className="measure-readout">
      <strong>{Math.round(km).toLocaleString()} km</strong>
      <div className="hint">
        {TRAVEL_MODES.map((m) => `${Math.ceil(km / m.kmPerDay)} days ${m.label}`).join(" · ")}
      </div>
    </div>
  );
}
