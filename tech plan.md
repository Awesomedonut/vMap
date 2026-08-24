# vMap — Tech Stack & Implementation Plan

Frontend: React. Backend: Python. Part 1 is the broad plan; Part 2 breaks each subsystem down in detail. Decisions lock only when a phase begins.

## Core Architecture Insight

vMap is not a drawing app; it's a **mapping stack applied to fictional worlds**. The real-world geo ecosystem (tiles, vector rendering, spatial DBs, routing engines) already solves navigable maps at scale — OpenGeofiction proved it works for fictional worlds. We reuse that stack instead of reinventing it, and add the fictional-world layer on top: procedural generation, custom units, per-world hosting. What we store is a **world model**: places, distances, routes, and terrain as queryable structure, not pixels.

```
React app (MapLibre GL)  ←  tiles + API  ←  FastAPI  ←  PostGIS + object storage
        ↑                                      ↑
  *.vmap.com routing                 Python worldgen engine (seeded)
```

---

# Part 1: Broad Plan

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

| Concern          | Choice                                                                                                                   | Why                                                                                                                                                                         |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API              | **FastAPI + Uvicorn**                                                                                                    | Async, Pydantic v2 models, OpenAPI for free.                                                                                                                                |
| Database         | **PostgreSQL + PostGIS**                                                                                                 | Industry-standard spatial DB: geometry types, spatial indexes, distance queries. Fictional worlds use a flat/custom CRS — PostGIS doesn't care that the planet isn't Earth. |
| Worldgen engine  | Python package (`vmap-worldgen`): numpy + scipy (Voronoi) + OpenSimplex noise                                            | Azgaar-style pipeline: seed → heightmap → coastlines → rivers → biomes → settlements → roads. Deterministic from (seed, settings). Runs as background jobs.                 |
| Tile pipeline    | Raster tiles (XYZ scheme) rendered from world data / uploaded images; **PMTiles** single-file archives on object storage | Serverless-friendly tile serving: no tile server to run, CDN-cacheable. Vector tiles later for dynamic styling.                                                             |
| Routing/distance | **networkx** graph over the world's road/path network; straight-line via PostGIS                                         | Per-world unit system (leagues, days-on-horseback) is a config-level conversion. pgRouting if graphs get big.                                                               |
| Jobs             | Background worker (arq or Celery + Redis)                                                                                | World generation and tiling are seconds-to-minutes tasks — never in a request cycle.                                                                                        |
| Storage          | S3-compatible object storage                                                                                             | Tiles, uploaded map images, assets.                                                                                                                                         |
| Auth             | Managed auth (Clerk/Auth0) or FastAPI + JWT                                                                              | Not a differentiator; buy, don't build.                                                                                                                                     |

## Implementation Phases (summary)

- **Phase 0 — Spike:** seeded worldgen → tiles → MapLibre, throwaway UI. Go/no-go gate.
- **Phase 1 — MVP:** upload or generate a world; hosted at `myworld.vmap.com` with pan/zoom, markers, search, accounts.
- **Phase 2 — Navigation:** unit calibration, distance tool, road routing with travel time by mode. The differentiator.
- **Phase 3 — Depth & community:** layers, map-to-map linking, community directory, collaborators, lore panels.
- **Phase 4 — Street view (moonshot):** decoupled; AI panoramas → 360° viewer → real-time 3D.

## Key Risks

1. **Worldgen quality** is make-or-break; Azgaar sets a high free bar (MIT-licensed — study or build on it). Phase 0 de-risks this first.
2. **Tile regeneration cost** on every edit — mitigate with region-scoped re-tiling and versioned archives.
3. **Scope creep toward VTT/wiki features** — vMap wins on *navigability*, not out-competing Inkarnate's art tools or World Anvil's wikis. Project Deios is the cautionary tale.

---

# Part 2: Detailed Breakdowns

## 2.1 System Architecture & Request Flows

Components: **web app** (Next.js), **API** (FastAPI), **worker** (jobs), **Postgres/PostGIS**, **Redis** (queue + cache), **object storage + CDN** (tiles, images).

**Viewer flow (the hot path — must work even if the API is down):**
1. `aeloria.vmap.com` → Next.js middleware extracts slug `aeloria` → fetches world config (cached).
2. Page renders MapLibre with the world's style JSON; tiles load straight from CDN (`tiles.vmap.com/aeloria/{version}/{z}/{x}/{y}` backed by a PMTiles archive via range requests).
3. Markers/labels/features load from the API as GeoJSON, cached by TanStack Query.

**Editor flow:** authenticated app at `app.vmap.com` → edits write features to PostGIS → a re-tile job is enqueued for the affected region → on completion the world's `tileset_version` bumps and viewers pick up new tiles (cache-busted by version in the URL).

**Generation flow:** user picks preset + seed → API creates a `generation_job` → worker runs the worldgen pipeline → writes features to PostGIS + renders tiles to storage → job status streamed to the client (SSE or polling) with stage-by-stage progress ("carving rivers…", "founding cities…" — make the wait part of the magic).

## 2.2 Worldgen Pipeline (`vmap-worldgen`)

A pure Python package, deterministic from `(seed, settings)`, testable without any server. Pipeline stages, each consuming the previous stage's output:

1. **Mesh** — Poisson-disc sample ~10–100k points; Voronoi/Delaunay mesh (scipy). All later attributes live on mesh cells.
2. **Elevation** — layered OpenSimplex noise + tectonic-style uplift ridges; settings control continent count, sea level, mountain intensity.
3. **Coastline & islands** — threshold at sea level; clean up specks; trace coast polygons.
4. **Hydrology** — rainfall from latitude bands + orographic effect; flow accumulation downhill; rivers where flow exceeds threshold; lakes in depressions.
5. **Climate & biomes** — temperature (latitude + altitude) × moisture → Whittaker-style biome table (tundra/taiga/forest/grassland/desert/jungle…).
6. **Settlements** — suitability score per cell (fresh water, coast, flat land, biome); place capitals then towns with spacing constraints; size by suitability.
7. **Political regions** — grow states from capitals via weighted flood-fill (terrain-cost expansion); derive borders.
8. **Road network** — A* between neighboring settlements over a cost surface (slope, river crossings, biome); union of paths = road graph; sea routes between ports.
9. **Naming** — Markov-chain name generators trained per culture wordlist; settings pick naming styles.
10. **Export** — GeoJSON feature collections per layer (terrain polygons, rivers, roads, settlements, borders, labels) + a `world_manifest.json` (seed, settings, unit system, extents).

Design rules: every stage pure and re-runnable; fixed seeds in tests with golden-file outputs (determinism is a feature — "share your seed" like Minecraft); stage boundaries are also the future manual-editing hooks (user tweaks stage N output, later stages re-run).

Prior art to study: Azgaar (MIT), Amit Patel's Red Blob polygon map-generation essays, Undiscovered Worlds (open source).

## 2.3 Tile Pipeline

- **Scheme:** standard XYZ slippy tiles, 256px, Web-Mercator-shaped math over a flat fictional plane (zoom 0 = whole world; each zoom doubles resolution). Target z0–z10 generated worlds (~350k tiles worst case, but ocean/empty tiles dedupe to a handful of bytes in PMTiles), deeper zooms for uploaded high-res images.
- **Rendering:** worker draws tiles from the GeoJSON layers with a raster renderer — biome fills, hillshade from the heightmap, rivers/roads as styled strokes, labels placed at zoom-appropriate sizes. Start simple (matplotlib-free custom drawing via Pillow/aggdraw or mapnik if needed); art styles are per-world render themes (parchment, atlas, dark).
- **Uploaded images:** slice with GDAL (`gdal2tiles`-style) into the same XYZ scheme; user calibrates scale (see 2.5).
- **Packaging:** tiles written into a **PMTiles** archive per world per version → object storage → CDN in front. No tile server process at all.
- **Invalidation:** edits mark dirty regions (bbox); re-render only affected tiles across zooms; write a new archive version; atomic pointer swap in `worlds.tileset_version`. Full re-render only when generation settings change.
- **Later:** vector tiles (tippecanoe → PMTiles) so styling/theming happens client-side in MapLibre without re-rendering rasters.

## 2.4 Data Model (first-cut schema)

```sql
users        (id, email, handle, created_at)
worlds       (id, slug UNIQUE,           -- subdomain
              owner_id → users,
              name, description, visibility,        -- public | unlisted | private
              seed BIGINT, gen_settings JSONB,      -- null for pure uploads
              unit_system JSONB,                    -- {unit:"league", km_per_unit:4.8, modes:{...}}
              tileset_version INT, style_theme TEXT,
              extents BOX2D, created_at, updated_at)
layers       (id, world_id → worlds, kind,          -- terrain|political|climate|custom
              name, min_zoom, max_zoom, sort_order, visible_default BOOL)
features     (id, world_id, layer_id,
              geom GEOMETRY,                        -- point|line|polygon, world CRS
              kind TEXT,                            -- city|road|river|border|region|marker|label
              name TEXT, properties JSONB,          -- population, lore text, icon, style
              created_by, updated_at)
              -- GIST index on geom; GIN trgm index on name (search)
tilesets     (id, world_id, version, pmtiles_key, status, created_at)
memberships  (world_id, user_id, role)              -- owner|editor|viewer
jobs         (id, world_id, kind, status, progress, error, payload JSONB, timestamps)
```

Conventions: world-local flat CRS with coordinates in the world's base unit; all distance math done in-world units then converted for display. Lore stays a `properties.lore` markdown field until it earns its own tables — we are not building a wiki.

## 2.5 Units, Distance & Routing Engine

- **Calibration:** every world has `unit_system` — base unit name, km-equivalent (for intuition only), and travel modes: `{walk: 30/day, horse: 60/day, cart: 40/day, ship: 150/day}` in world units, all user-editable. For uploaded images: user clicks two points, types the distance → sets scale.
- **Straight-line:** `ST_Distance` in PostGIS, instant, works with zero road data. Ship this first.
- **Route:** build a networkx graph from `features.kind IN ('road','sea_route')` — nodes at endpoints/intersections (noded with `ST_Node`), edge weight = length × terrain multiplier. A* between nearest graph points to the selected pins; snap-to-network with a tolerance; fall back to straight-line with a "no route found, as the crow flies" label.
- **Output contract:** `POST /worlds/{id}/route {from, to, mode}` → `{distance_units, distance_display, duration_days, path: GeoJSON LineString, legs: [...]}`. The frontend draws the path and shows "Aeloria → Westmarch: 34 days by horse."
- Cache built graphs in Redis keyed by `(world_id, features_updated_at)`; rebuild lazily on edit.

## 2.6 API Surface (FastAPI, `/api/v1`)

```
Worlds       POST /worlds                      create (upload or generate)
             GET  /worlds/{slug}               config, style, layers, unit system
             PATCH/DELETE /worlds/{id}
             POST /worlds/{id}/generate        enqueue generation {seed, preset, settings}
             GET  /jobs/{id}                   status + progress (poll or SSE)
Features     GET  /worlds/{id}/features?bbox&layer&kind     GeoJSON
             POST/PATCH/DELETE /worlds/{id}/features[...]   editor only
Navigation   POST /worlds/{id}/route           {from, to, mode}
             GET  /worlds/{id}/measure?a&b     straight-line
Search       GET  /worlds/{id}/search?q=       trgm match on feature names
Community    GET  /worlds?visibility=public&sort=popular    directory
Members      POST/DELETE /worlds/{id}/members
```

Pydantic models for every request/response; auth via bearer token dependency; per-world role checks in a single `Depends(require_role)` helper. Public read endpoints aggressively HTTP-cached (world config, features) with `tileset_version`/`updated_at` in ETags.

## 2.7 Frontend Architecture

- **Apps/routes:** one Next.js app, three faces: marketing site (`vmap.com`), creator dashboard + editor (`app.vmap.com`), world viewer (`{slug}.vmap.com`). Middleware maps hostname → route group.
- **Viewer components:** `WorldMap` (MapLibre wrapper), `SearchBox`, `FeaturePopup` (lore/details), `RoutePanel` (pick two points → distance/time/mode), `LayerToggle`, `ScaleBar` (world units), `ShareControls`.
- **Editor components:** viewer + `DrawTools` (place marker, draw road/region — MapLibre draw plugin), `FeatureInspector` (edit name/lore/properties), `GenerationPanel` (seed, preset sliders, regenerate), `WorldSettings` (units, theme, visibility, collaborators).
- **State:** map viewport + selection in React state/context; all server data through TanStack Query; optimistic updates for feature edits with rollback.
- **Map styling:** style JSON generated server-side per world (theme + layers); MapLibre consumes it directly, so theme changes don't touch code.

## 2.8 Multi-Tenancy & Infrastructure

- **DNS/TLS:** wildcard `*.vmap.com` A record + wildcard cert. Reserved slugs list (`www`, `app`, `api`, `tiles`, `admin`…). Custom domains (creator brings `map.mynovel.com`) later via CNAME + on-demand certs.
- **Deploy:** frontend on Vercel (native wildcard-domain + middleware support); API + worker as containers (Fly.io or Railway to start); managed Postgres with PostGIS (Neon/Supabase/RDS); Cloudflare in front of R2/S3 for tiles.
- **Environments:** local via docker-compose (postgres+postgis, redis, minio); staging + prod. Migrations with Alembic.
- **Cost at MVP scale:** tens of dollars/month — tiles-on-CDN is the whole trick; there is no expensive always-on map server.

## 2.9 Testing & Quality

- **Worldgen:** pytest golden tests — fixed seed+settings must reproduce byte-identical manifests and feature counts across versions (regressions in generation are product bugs). Property tests: rivers always reach sea/lake, roads always connect, no settlement in ocean.
- **API:** pytest + httpx against a Testcontainers PostGIS; every endpoint has happy-path + authz tests.
- **Routing:** fixture worlds with known graphs → exact expected distances/durations.
- **Frontend:** Vitest for logic, Playwright smoke: load world, search, click feature, route between two pins.
- **CI:** GitHub Actions — lint (ruff/black, eslint), typecheck (mypy/tsc), tests, worldgen goldens.

## 2.10 Phase Breakdown with Milestones

**Phase 0 — Spike (1–2 weeks)** · *Gate: does it feel magical?*
- Worldgen stages 1–6 (mesh → biomes → settlements), crude Pillow tile renderer, PMTiles output, MapLibre viewer on localhost. No auth, no DB, no jobs — one script, one page.

**Phase 1 — MVP (4–8 weeks)**
- Postgres/PostGIS schema + Alembic; auth; world CRUD.
- Generation as background job with progress UI; image upload + GDAL slicing + scale calibration.
- Tile pipeline with versioning; CDN serving; wildcard subdomain viewer with markers, labels, search.
- Dashboard: my worlds, visibility, delete/regenerate. **Milestone: a stranger can generate a world and send someone a link to it.**

**Phase 2 — Navigation (3–5 weeks)**
- Unit system + calibration UI; measure tool; worldgen stages 7–9 (states, roads, names).
- Routing engine + RoutePanel; travel modes; route sharing (URL encodes from/to/mode). **Milestone: the "34 days by horse" screenshot people share.**

**Phase 3 — Depth & community (ongoing)**
- Feature editing (draw roads/regions/markers), layers with zoom rules, map-to-map linking, public directory, collaborator roles, embeds (iframe for YouTubers/blogs), lore properties on features.

**Phase 4 — Street view (renders when the platform earns it)**
- v1: AI-generated stills per location (biome/culture-conditioned prompts) in a lightbox. v2: 360° panorama viewer at pinned spots. v3: real-time 3D terrain flyover (the heightmap already exists — a Cesium/three.js terrain view is cheaper than it sounds).

## 2.11 Open Questions (decide at phase boundaries)

1. Raster-first (simpler, locked style) vs vector-first (themable, harder) tiles — Phase 0 answers this by feel.
2. Build worldgen from scratch vs fork/embed Azgaar's algorithms (MIT) behind our pipeline interface.
3. Next.js on Vercel vs self-hosted — decided by how custom subdomain TLS shakes out.
4. Flat worlds forever, or globes eventually (projection math changes everything downstream — defer, but store coordinates abstractly enough to allow it).
5. Editing granularity in Phase 3: feature-level only, or terrain re-sculpting (re-runs pipeline stages — powerful but heavy).
