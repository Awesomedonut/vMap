export interface WorldManifest {
  slug: string;
  name: string;
  seed: number;
  settings: {
    preset: string;
    grid_n: number;
    ocean_fraction: number;
    world_km: number;
    sea_level: number;
    [k: string]: unknown;
  };
  n_settlements: number;
  n_rivers: number;
  max_zoom?: number;
}

export interface JobStatus {
  id: string;
  status: "running" | "done" | "error";
  stage: string;
  progress: number;
  slug: string | null;
  error: string | null;
}

export interface GenerateParams {
  seed?: number;
  preset: string;
  grid_n: number;
  ocean_fraction: number;
  world_km: number;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  listWorlds: () => fetch("/api/worlds").then((r) => json<WorldManifest[]>(r)),
  getWorld: (slug: string) => fetch(`/api/worlds/${slug}`).then((r) => json<WorldManifest>(r)),
  getFeatures: (slug: string) =>
    fetch(`/api/worlds/${slug}/features`).then((r) => json<GeoJSON.FeatureCollection>(r)),
  search: (slug: string, q: string) =>
    fetch(`/api/worlds/${slug}/search?q=${encodeURIComponent(q)}`).then((r) =>
      json<GeoJSON.FeatureCollection>(r)
    ),
  generate: (params: GenerateParams) =>
    fetch("/api/worlds", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }).then((r) => json<JobStatus>(r)),
  jobStatus: (id: string) => fetch(`/api/jobs/${id}`).then((r) => json<JobStatus>(r)),
  deleteWorld: (slug: string) => fetch(`/api/worlds/${slug}`, { method: "DELETE" }),
};
