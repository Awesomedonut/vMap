"""Core data model for a generated world.

Coordinates live in a normalized mercator square [0,1]x[0,1]:
x maps linearly to longitude, y is web-mercator y. This lets standard
XYZ slippy-tile math address the world directly, and MapLibre render it
with zero custom projection code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

BIOME_NAMES = [
    "deep ocean",
    "ocean",
    "shallows",
    "beach",
    "tundra",
    "taiga",
    "temperate forest",
    "grassland",
    "shrubland",
    "desert",
    "savanna",
    "jungle",
    "swamp",
    "mountain",
    "snow peak",
]


@dataclass
class Settlement:
    name: str
    x: float
    y: float
    kind: str  # capital | town | village
    population: int


@dataclass
class World:
    seed: int
    settings: dict[str, Any]
    name: str
    # geometry
    points: np.ndarray          # (N,2) cell centers, normalized coords
    polygons: list[np.ndarray]  # per-cell voronoi polygon vertices (M_i, 2)
    neighbors: list[list[int]]  # per-cell adjacent cell indices
    # per-cell attributes
    elevation: np.ndarray       # (N,) in [0,1]
    is_land: np.ndarray         # (N,) bool
    temperature: np.ndarray     # (N,) in [0,1]
    moisture: np.ndarray        # (N,) in [0,1]
    flow: np.ndarray            # (N,) river flow accumulation
    biome: np.ndarray           # (N,) int index into BIOME_NAMES
    # derived features
    rivers: list[np.ndarray] = field(default_factory=list)   # polylines (K,2)
    settlements: list[Settlement] = field(default_factory=list)

    @property
    def sea_level(self) -> float:
        return float(self.settings["sea_level"])


def norm_to_lonlat(x: float, y: float) -> tuple[float, float]:
    """Normalized mercator square -> (lon, lat) for GeoJSON/MapLibre."""
    lon = x * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * y))))
    return lon, lat


def world_distance_km(world: World, a: tuple[float, float], b: tuple[float, float]) -> float:
    """Straight-line distance between two normalized points, in world km."""
    span_km = float(world.settings["world_km"])
    return math.hypot(b[0] - a[0], b[1] - a[1]) * span_km


def save_npz(world: World, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        points=world.points,
        elevation=world.elevation,
        is_land=world.is_land,
        temperature=world.temperature,
        moisture=world.moisture,
        flow=world.flow,
        biome=world.biome,
        polygons=np.array(world.polygons, dtype=object),
        neighbors=np.array([np.array(n, dtype=np.int32) for n in world.neighbors], dtype=object),
        rivers=np.array(world.rivers, dtype=object),
        settlements=np.array(
            [(s.name, s.x, s.y, s.kind, s.population) for s in world.settlements], dtype=object
        ),
        meta=np.array([world.seed, world.name], dtype=object),
        settings=np.array([world.settings], dtype=object),
        allow_pickle=True,
    )


def load_npz(path: Path) -> World:
    d = np.load(path, allow_pickle=True)
    seed, name = d["meta"]
    return World(
        seed=int(seed),
        settings=dict(d["settings"][0]),
        name=str(name),
        points=d["points"],
        polygons=list(d["polygons"]),
        neighbors=[list(n) for n in d["neighbors"]],
        elevation=d["elevation"],
        is_land=d["is_land"],
        temperature=d["temperature"],
        moisture=d["moisture"],
        flow=d["flow"],
        biome=d["biome"],
        rivers=list(d["rivers"]),
        settlements=[
            Settlement(name=str(n), x=float(x), y=float(y), kind=str(k), population=int(p))
            for n, x, y, k, p in d["settlements"]
        ],
    )
