# vMap — Tech Stack & Implementation Plan (Broad)

Frontend: React. Backend: Python. This is a directional plan — each phase locks decisions only when we reach it.

## Core Architecture Insight

vMap is not a drawing app; it's a **mapping stack applied to fictional worlds**. The real-world geo ecosystem (tiles, vector rendering, spatial DBs, routing engines) already solves navigable maps at scale — OpenGeofiction proved it works for fictional worlds. We reuse that stack instead of reinventing it, and add the fictional-world layer on top: procedural generation, custom units, per-world hosting.

```
React app (MapLibre GL)  ←  tiles + API  ←  FastAPI  ←  PostGIS + object storage
        ↑                                      ↑
  *.vmap.com routing                 Python worldgen engine (seeded)
```

## Tech Stack

### Frontend (React)

| Concern | Choice | Why |
|---|---|---|
| Framework | **Next.js (App Router) + TypeScript** | Subdomain-per-world routing via middleware (one app serves `*.vmap.com`), SSR for shareable/SEO-friendly world pages. Vite+React fallback if we stay SPA-only. |
| Map rendering | **MapLibre GL JS** | Open-source Mapbox fork; smooth Google-Maps-feel pan/zoom, vector tiles, rotation, custom styles per world. Leaflet is the simpler fallback for raster-only MVP. |
| Server state | TanStack Query | Caching tile metadata, markers, world config. |
| Styling/UI | TailwindCSS + Radix | Fast, consistent. |
| Forms/validation | react-hook-form + Zod | Matches existing conventions. |

### Backend (Python)

| Concern | Choice | Why |
|---|---|---|
| API | **FastAPI + Uvicorn** | Async, Pydantic v2 models, OpenAPI for free. |
| Database | **PostgreSQL + PostGIS** | The industry-standard spatial DB: geometry types, spatial indexes, distance queries. Fictional worlds use a flat/custom CRS — PostGIS doesn't care that the planet isn't Earth. |
| Worldgen engine | Python package (`vmap-worldgen`): numpy + scipy (Voronoi) + OpenSimplex noise | Azgaar-style pipeline: seed → heightmap → coastlines → rivers → biomes → settlements → roads. Deterministic from (seed, settings). Runs as background jobs. |
| Tile pipeline | Raster tiles (XYZ scheme) rendered from world data / uploaded images; **PMTiles** single-file archives on object storage | Serverless-friendly tile serving: no tile server to run, CDN-cacheable. Vector tiles later for dynamic styling. |
| Routing/distance | **networkx** graph over the world's road/path network; straight-line via PostGIS | Per-world unit system (leagues, days-on-horseback) is a config-level conversion on top of graph distance. pgRouting if graphs get big. |
| Jobs | Background worker (arq or Celery + Redis) | World generation and tiling are seconds-to-minutes tasks — never in a request cycle. |
| Storage | S3-compatible object storage | Tiles, uploaded map images, assets. |
| Auth | Managed auth (Clerk/Auth0) or FastAPI + JWT | Not a differentiator; buy, don't build. |

### Hosting model

- Wildcard DNS `*.vmap.com` → one Next.js app; middleware resolves subdomain → world.
- Tiles served from CDN in front of object storage (PMTiles range requests) — the map stays fast even if the API is cold.
- Deploy: frontend on Vercel; API + workers containerized (Fly.io/Railway/AWS); managed Postgres with PostGIS.

## Data Model (first cut)

- **World** — id, slug (subdomain), owner, seed + generation settings, unit system (name, km-per-unit, travel speeds), visibility (public/community/private).
- **Layer** — political / terrain / climate / custom; zoom-range visibility.
- **Feature** — PostGIS geometry (point/line/polygon): cities, roads, rivers, borders, labels; linked lore text.
- **TileSet** — versioned PMTiles archive per world (regenerate on edit, atomic swap).
- **User / Membership** — ownership, collaborators, community roles.

## Implementation Phases

### Phase 0 — Spike (validate the fun part)
Prove the pipeline end-to-end with zero product around it: seeded Python worldgen → render raster tiles → view in MapLibre in a throwaway React page. If this feels like "Google Maps for a world that didn't exist a minute ago," everything else is product work.

### Phase 1 — MVP: hosted navigable maps
- Upload a map image **or** generate a world from seed + presets.
- Auto-tile it; publish at `myworld.vmap.com` with pan/zoom, markers, labels, search.
- Accounts, world dashboard, public/private toggle.
- This alone matches fictionalmaps.com's whole product, plus generation.

### Phase 2 — Measurement & navigation (the differentiator)
- Per-world unit and scale calibration.
- Straight-line distance tool; then road-network routing with travel time by mode (foot, horse, ship) — "Winterfell → King's Landing: 34 days by horse."
- Draw/edit roads, cities, borders on the map (feature editing, not pixel editing).

### Phase 3 — Depth & community
- Layers (political/terrain/climate), zoom-dependent detail, map-to-map linking (world → city).
- Community worlds directory, sharing/embedding, collaborator roles.
- Lore panels on features (or integrations with World Anvil/LegendKeeper rather than competing on wikis).

### Phase 4 — Street view (moonshot, keep decoupled)
- Options in ascending ambition: AI-generated location panoramas → 360° viewer at pinned spots → real-time 3D ground-level rendering from terrain data.
- Nothing in Phases 0–3 should depend on this.

## Key Risks

1. **Worldgen quality** is the make-or-break; Azgaar sets a high free bar (open source, MIT — study it, or build on it). Phase 0 exists to de-risk this first.
2. **Tile regeneration cost** on every edit — mitigate with region-scoped re-tiling and versioned archives.
3. **Scope creep toward VTT/wiki features** — vMap wins on *navigability*, not on out-competing Inkarnate's art tools or World Anvil's wikis.
