"""World generation pipeline: deterministic from (seed, settings)."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np

from .biomes import assign_biomes
from .elevation import compute_elevation
from .hydrology import compute_climate, compute_flow, trace_rivers
from .mesh import build_mesh
from .model import World
from .naming import NameGenerator
from .settlements import place_settlements

DEFAULT_SETTINGS: dict[str, Any] = {
    "preset": "continents",      # continents | pangaea | archipelago
    "grid_n": 96,                # mesh resolution (grid_n^2 cells)
    "ocean_fraction": 0.62,      # fraction of the world under water
    "river_threshold": 6.0,
    "world_km": 3000,            # width of the map in km
    "n_capitals": 4,
    "n_towns": 10,
    "n_villages": 16,
}

ProgressFn = Callable[[str, float], None]


def generate(seed: int, settings: dict[str, Any] | None = None, on_progress: ProgressFn | None = None) -> World:
    cfg = {**DEFAULT_SETTINGS, **(settings or {})}
    report = on_progress or (lambda stage, frac: None)
    rng = np.random.default_rng(seed)

    report("laying the mesh", 0.05)
    points, polygons, neighbors = build_mesh(rng, int(cfg["grid_n"]))

    report("raising mountains", 0.25)
    elevation = compute_elevation(rng, points, cfg)
    # sea level as an elevation quantile so ocean_fraction is exact by construction
    cfg["sea_level"] = float(np.quantile(elevation, float(cfg["ocean_fraction"])))
    is_land = elevation > float(cfg["sea_level"])

    report("shaping climates", 0.45)
    temperature, moisture = compute_climate(rng, points, elevation, float(cfg["sea_level"]))

    report("carving rivers", 0.6)
    flow, downstream = compute_flow(points, elevation, is_land, neighbors, moisture)
    rivers = trace_rivers(points, flow, downstream, is_land, float(cfg["river_threshold"]))

    report("seeding biomes", 0.75)
    biome = assign_biomes(elevation, is_land, temperature, moisture, flow, float(cfg["sea_level"]))

    report("founding cities", 0.9)
    settlements = place_settlements(rng, points, elevation, is_land, biome, flow, neighbors, cfg)

    world_name = NameGenerator(rng).generate()
    report("done", 1.0)
    return World(
        seed=seed, settings=cfg, name=world_name,
        points=points, polygons=polygons, neighbors=neighbors,
        elevation=elevation, is_land=is_land,
        temperature=temperature, moisture=moisture,
        flow=flow, biome=biome, rivers=rivers, settlements=settlements,
    )
