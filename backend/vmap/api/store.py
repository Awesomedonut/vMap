"""Filesystem world store with in-memory renderer cache.

Layout: data/worlds/{slug}/world.npz, manifest.json, tiles/{z}/{x}/{y}.png
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from ..render.tiler import WorldRenderer
from ..worldgen import model
from ..worldgen.model import World, load_npz, norm_to_lonlat, save_npz

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "worlds"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "world"


class WorldStore:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._renderers: dict[str, WorldRenderer] = {}
        self._lock = threading.Lock()

    # -- persistence ---------------------------------------------------------

    def save(self, world: World) -> str:
        slug = slugify(world.name)
        base = slug
        n = 2
        while (self.data_dir / slug).exists():
            slug = f"{base}-{n}"
            n += 1
        wdir = self.data_dir / slug
        wdir.mkdir(parents=True)
        save_npz(world, wdir / "world.npz")
        manifest = {
            "slug": slug,
            "name": world.name,
            "seed": world.seed,
            "settings": world.settings,
            "n_settlements": len(world.settlements),
            "n_rivers": len(world.rivers),
        }
        (wdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        (wdir / "features.geojson").write_text(json.dumps(self._features(world)))
        return slug

    def _features(self, world: World) -> dict:
        feats = []
        for s in world.settlements:
            lon, lat = norm_to_lonlat(s.x, s.y)
            feats.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "name": s.name, "kind": s.kind, "population": s.population,
                    "nx": s.x, "ny": s.y,
                },
            })
        return {"type": "FeatureCollection", "features": feats}

    # -- reads ---------------------------------------------------------------

    def list_worlds(self) -> list[dict]:
        out = []
        for mf in sorted(self.data_dir.glob("*/manifest.json")):
            out.append(json.loads(mf.read_text()))
        return out

    def manifest(self, slug: str) -> dict | None:
        mf = self.data_dir / slug / "manifest.json"
        return json.loads(mf.read_text()) if mf.exists() else None

    def features(self, slug: str) -> dict | None:
        f = self.data_dir / slug / "features.geojson"
        return json.loads(f.read_text()) if f.exists() else None

    def renderer(self, slug: str) -> WorldRenderer | None:
        with self._lock:
            if slug in self._renderers:
                return self._renderers[slug]
        npz = self.data_dir / slug / "world.npz"
        if not npz.exists():
            return None
        world = load_npz(npz)
        renderer = WorldRenderer(world)
        with self._lock:
            self._renderers[slug] = renderer
            # keep memory bounded: hold at most 4 renderers
            while len(self._renderers) > 4:
                self._renderers.pop(next(iter(self._renderers)))
        return renderer

    def tile_path(self, slug: str, z: int, x: int, y: int) -> Path:
        return self.data_dir / slug / "tiles" / str(z) / str(x) / f"{y}.png"

    def biome_names(self) -> list[str]:
        return model.BIOME_NAMES
