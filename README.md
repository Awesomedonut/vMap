# vMap

**Google Maps for fictional worlds.** Generate a seeded world model — terrain, biomes, rivers, named settlements — and explore it like a real place: pan, zoom, search, and measure travel distances.

Unlike 2D fantasy map makers that output a static image, vMap stores a **world model**: places, distances, and terrain as queryable structure. See [`mission statement.md`](mission%20statement.md) and [`tech plan.md`](tech%20plan.md).

## Status: Phase 0/1 MVP

- ✅ Deterministic procedural worldgen (seed + presets → same world every time)
- ✅ On-demand XYZ raster tiles, rendered server-side and cached
- ✅ MapLibre viewer: pan/zoom, settlement labels, click popups
- ✅ Place search with fly-to
- ✅ Measure tool: straight-line distance + travel time (foot / horse / ship)
- 🔜 Road routing, hosted subdomains, image upload, accounts

## Run locally

Backend (Python 3.12+):

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn vmap.api.main:app --port 8000
```

Frontend (Node 20+):

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```

Open http://localhost:5173, click **Generate world**, then explore it.

## Tests

```bash
cd backend && .venv/bin/pytest tests/ -v
```

Covers worldgen determinism (same seed → byte-identical world) and structural invariants (settlements on land, rivers flow downhill, ocean fraction respected).

## Architecture

```
React + MapLibre GL (frontend/)          FastAPI (backend/vmap/api/)
  viewer: tiles, search, measure    ←→     worlds, jobs, search, tiles
                                                 │
                                    worldgen pipeline (backend/vmap/worldgen/)
                                      mesh → elevation → climate → rivers
                                      → biomes → settlements → names
                                                 │
                                    tile renderer (backend/vmap/render/)
                                      on-demand XYZ PNGs, cached to disk
```

Worlds live in a normalized mercator square so standard slippy-tile math and MapLibre work unmodified. See [`tech plan.md`](tech%20plan.md) for the full breakdown.
