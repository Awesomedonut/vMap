"""vMap API: world generation, manifests, features, search, on-demand tiles."""

from __future__ import annotations

import io
import shutil
import threading
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..worldgen.pipeline import DEFAULT_SETTINGS, generate
from .jobs import JobTracker
from .store import WorldStore

MAX_ZOOM = 7
TILE_CACHE_HEADERS = {"Cache-Control": "public, max-age=3600"}

app = FastAPI(title="vMap API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = WorldStore()
jobs = JobTracker()


class GenerateRequest(BaseModel):
    seed: int | None = None
    preset: str = Field(default="continents", pattern="^(continents|pangaea|archipelago)$")
    grid_n: int = Field(default=96, ge=32, le=160)
    ocean_fraction: float = Field(default=0.62, ge=0.2, le=0.85)
    world_km: int = Field(default=3000, ge=200, le=40000)

    def to_settings(self) -> dict[str, Any]:
        return {**DEFAULT_SETTINGS, "preset": self.preset, "grid_n": self.grid_n,
                "ocean_fraction": self.ocean_fraction, "world_km": self.world_km}

    def resolved_seed(self) -> int:
        return self.seed if self.seed is not None else uuid.uuid4().int % (2**31)


class JobStatus(BaseModel):
    id: str
    status: str  # running | done | error
    stage: str
    progress: float
    slug: str | None = None
    error: str | None = None


def _run_generation(job_id: str, seed: int, settings: dict[str, Any]) -> None:
    try:
        world = generate(seed, settings,
                         on_progress=lambda stage, frac: jobs.update(job_id, stage=stage, progress=frac))
        slug = store.save(world)
        jobs.update(job_id, status="done", slug=slug, progress=1.0, stage="done")
    except Exception as exc:  # surface generation failures to the client
        jobs.update(job_id, status="error", error=str(exc))


@app.post("/api/worlds", response_model=JobStatus, status_code=202)
def create_world(req: GenerateRequest) -> JobStatus:
    job = jobs.create()
    threading.Thread(
        target=_run_generation, args=(job["id"], req.resolved_seed(), req.to_settings()), daemon=True
    ).start()
    return JobStatus(**job)


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return JobStatus(**job)


@app.get("/api/worlds")
def list_worlds() -> list[dict]:
    return store.list_worlds()


@app.get("/api/worlds/{slug}")
def world_manifest(slug: str) -> dict:
    manifest = store.manifest(slug)
    if not manifest:
        raise HTTPException(404, "world not found")
    return {**manifest, "max_zoom": MAX_ZOOM}


@app.get("/api/worlds/{slug}/features")
def world_features(slug: str) -> dict:
    features = store.features(slug)
    if features is None:
        raise HTTPException(404, "world not found")
    return features


@app.get("/api/worlds/{slug}/search")
def search(slug: str, q: str) -> dict:
    features = store.features(slug)
    if features is None:
        raise HTTPException(404, "world not found")
    needle = q.lower().strip()
    hits = [f for f in features["features"] if needle in f["properties"]["name"].lower()]
    return {"type": "FeatureCollection", "features": hits[:10]}


@app.delete("/api/worlds/{slug}", status_code=204)
def delete_world(slug: str) -> Response:
    world_dir = store.data_dir / slug
    if not world_dir.exists():
        raise HTTPException(404, "world not found")
    shutil.rmtree(world_dir)
    return Response(status_code=204)


@app.get("/tiles/{slug}/{z}/{x}/{y}.png")
def tile(slug: str, z: int, x: int, y: int) -> Response:
    if not (0 <= z <= MAX_ZOOM and 0 <= x < 2**z and 0 <= y < 2**z):
        raise HTTPException(404, "tile out of range")
    cached = store.tile_path(slug, z, x, y)
    if cached.exists():
        return Response(cached.read_bytes(), media_type="image/png", headers=TILE_CACHE_HEADERS)
    return Response(_render_and_cache_tile(slug, z, x, y), media_type="image/png",
                    headers=TILE_CACHE_HEADERS)


def _render_and_cache_tile(slug: str, z: int, x: int, y: int) -> bytes:
    renderer = store.renderer(slug)
    if renderer is None:
        raise HTTPException(404, "world not found")
    buf = io.BytesIO()
    renderer.render_tile(z, x, y).save(buf, format="PNG")
    data = buf.getvalue()
    path = store.tile_path(slug, z, x, y)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data
