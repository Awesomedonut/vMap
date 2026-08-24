"""vMap API: world generation, manifests, features, search, on-demand tiles."""

from __future__ import annotations

import io
import threading
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..worldgen.pipeline import DEFAULT_SETTINGS, generate
from .store import WorldStore

app = FastAPI(title="vMap API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = WorldStore()
jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()

MAX_ZOOM = 7


class GenerateRequest(BaseModel):
    seed: int | None = None
    preset: str = Field(default="continents", pattern="^(continents|pangaea|archipelago)$")
    grid_n: int = Field(default=96, ge=32, le=160)
    ocean_fraction: float = Field(default=0.62, ge=0.2, le=0.85)
    world_km: int = Field(default=3000, ge=200, le=40000)


class JobStatus(BaseModel):
    id: str
    status: str  # running | done | error
    stage: str
    progress: float
    slug: str | None = None
    error: str | None = None


def _run_generation(job_id: str, seed: int, settings: dict[str, Any]) -> None:
    def report(stage: str, frac: float) -> None:
        with jobs_lock:
            jobs[job_id].update(stage=stage, progress=frac)

    try:
        world = generate(seed, settings, on_progress=report)
        slug = store.save(world)
        with jobs_lock:
            jobs[job_id].update(status="done", slug=slug, progress=1.0, stage="done")
    except Exception as exc:  # surface generation failures to the client
        with jobs_lock:
            jobs[job_id].update(status="error", error=str(exc))


@app.post("/api/worlds", response_model=JobStatus, status_code=202)
def create_world(req: GenerateRequest) -> JobStatus:
    seed = req.seed if req.seed is not None else uuid.uuid4().int % (2**31)
    settings = {**DEFAULT_SETTINGS, "preset": req.preset, "grid_n": req.grid_n,
                "ocean_fraction": req.ocean_fraction, "world_km": req.world_km}
    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {"id": job_id, "status": "running", "stage": "queued", "progress": 0.0,
                        "slug": None, "error": None}
    threading.Thread(target=_run_generation, args=(job_id, seed, settings), daemon=True).start()
    return JobStatus(**jobs[job_id])


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return JobStatus(**job)


@app.get("/api/worlds")
def list_worlds() -> list[dict]:
    return store.list_worlds()


@app.get("/api/worlds/{slug}")
def world_manifest(slug: str) -> dict:
    mf = store.manifest(slug)
    if not mf:
        raise HTTPException(404, "world not found")
    mf["max_zoom"] = MAX_ZOOM
    return mf


@app.get("/api/worlds/{slug}/features")
def world_features(slug: str) -> dict:
    feats = store.features(slug)
    if feats is None:
        raise HTTPException(404, "world not found")
    return feats


@app.get("/api/worlds/{slug}/search")
def search(slug: str, q: str) -> dict:
    feats = store.features(slug)
    if feats is None:
        raise HTTPException(404, "world not found")
    ql = q.lower().strip()
    hits = [f for f in feats["features"] if ql in f["properties"]["name"].lower()]
    return {"type": "FeatureCollection", "features": hits[:10]}


@app.delete("/api/worlds/{slug}", status_code=204)
def delete_world(slug: str) -> Response:
    wdir = store.data_dir / slug
    if not wdir.exists():
        raise HTTPException(404, "world not found")
    import shutil

    shutil.rmtree(wdir)
    return Response(status_code=204)


@app.get("/tiles/{slug}/{z}/{x}/{y}.png")
def tile(slug: str, z: int, x: int, y: int) -> Response:
    if not (0 <= z <= MAX_ZOOM and 0 <= x < 2**z and 0 <= y < 2**z):
        raise HTTPException(404, "tile out of range")
    path = store.tile_path(slug, z, x, y)
    if path.exists():
        return Response(path.read_bytes(), media_type="image/png",
                        headers={"Cache-Control": "public, max-age=3600"})
    renderer = store.renderer(slug)
    if renderer is None:
        raise HTTPException(404, "world not found")
    img = renderer.render_tile(z, x, y)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return Response(data, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})
