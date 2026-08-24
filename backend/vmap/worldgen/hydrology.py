"""Stage 4-5: climate (temperature, moisture), flow accumulation, rivers."""

from __future__ import annotations

import numpy as np

from .noise import fbm


def compute_climate(
    rng: np.random.Generator, pts: np.ndarray, elevation: np.ndarray, sea_level: float
) -> tuple[np.ndarray, np.ndarray]:
    seed = int(rng.integers(0, 2**31))
    # latitude band: warm equator (y=0.5), cold poles; altitude cools
    lat = np.abs(pts[:, 1] - 0.5) * 2.0
    altitude = np.clip(elevation - sea_level, 0, None)
    temperature = np.clip(1.0 - lat**1.3 - altitude * 1.1 + 0.08, 0.0, 1.0)
    moisture = fbm(pts, seed, octaves=4, base_freq=3.0)
    moisture = (moisture - moisture.min()) / (moisture.max() - moisture.min())
    return temperature, moisture


def compute_flow(
    pts: np.ndarray,
    elevation: np.ndarray,
    is_land: np.ndarray,
    neighbors: list[list[int]],
    moisture: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Accumulate rainfall downhill. Returns (flow, downstream index or -1)."""
    n = len(pts)
    flow = np.where(is_land, 0.2 + moisture, 0.0)
    downstream = np.full(n, -1, dtype=np.int64)
    order = np.argsort(-elevation)  # highest first
    for i in order:
        if not is_land[i]:
            continue
        nbrs = neighbors[i]
        if not nbrs:
            continue
        lowest = min(nbrs, key=lambda j: elevation[j])
        if elevation[lowest] < elevation[i]:
            downstream[i] = lowest
            flow[lowest] += flow[i]
    return flow, downstream


def trace_rivers(
    pts: np.ndarray,
    flow: np.ndarray,
    downstream: np.ndarray,
    is_land: np.ndarray,
    threshold: float,
) -> list[np.ndarray]:
    """River polylines: start at cells above threshold whose upstream isn't, follow down to sea."""
    n = len(pts)
    is_river = is_land & (flow >= threshold)
    has_river_upstream = np.zeros(n, dtype=bool)
    for i in range(n):
        if is_river[i] and downstream[i] >= 0:
            has_river_upstream[downstream[i]] = True

    rivers: list[np.ndarray] = []
    for i in range(n):
        if not is_river[i] or has_river_upstream[i]:
            continue
        path = [i]
        cur = i
        while downstream[cur] >= 0:
            cur = downstream[cur]
            path.append(cur)
            if not is_land[cur]:
                break
        if len(path) >= 3:
            rivers.append(pts[path].copy())
    return rivers
