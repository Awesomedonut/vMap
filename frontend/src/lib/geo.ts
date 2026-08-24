/** Geometry shared by the viewer: the backend's normalized-square world coords. */

export interface TravelMode {
  label: string;
  kmPerDay: number;
}

export const TRAVEL_MODES: TravelMode[] = [
  { label: "on foot", kmPerDay: 30 },
  { label: "by horse", kmPerDay: 60 },
  { label: "by ship", kmPerDay: 150 },
];

/** lon/lat -> normalized world coords (the same [0,1]^2 square the backend uses) */
export function lngLatToNorm(lng: number, lat: number): [number, number] {
  const x = (lng + 180) / 360;
  const rad = (lat * Math.PI) / 180;
  const y = (1 - Math.asinh(Math.tan(rad)) / Math.PI) / 2;
  return [x, y];
}

/** Straight-line distance in world km between two lon/lat points. */
export function distanceKm(
  a: [number, number],
  b: [number, number],
  worldKm: number
): number {
  const [ax, ay] = lngLatToNorm(a[0], a[1]);
  const [bx, by] = lngLatToNorm(b[0], b[1]);
  return Math.hypot(bx - ax, by - ay) * worldKm;
}
