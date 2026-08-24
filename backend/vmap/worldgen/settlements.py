"""Stage 6: settlement placement by suitability score with spacing constraints."""

from __future__ import annotations

import numpy as np

from .biomes import BEACH, GRASSLAND, JUNGLE, SAVANNA, SHRUBLAND, TEMPERATE_FOREST
from .model import Settlement
from .naming import NameGenerator

HOSPITABLE = {TEMPERATE_FOREST, GRASSLAND, SHRUBLAND, SAVANNA, BEACH, JUNGLE}


def place_settlements(
    rng: np.random.Generator,
    pts: np.ndarray,
    elevation: np.ndarray,
    is_land: np.ndarray,
    biome: np.ndarray,
    flow: np.ndarray,
    neighbors: list[list[int]],
    settings: dict,
) -> list[Settlement]:
    n = len(pts)
    coastal = np.zeros(n, dtype=bool)
    for i in range(n):
        if is_land[i] and any(not is_land[j] for j in neighbors[i]):
            coastal[i] = True

    score = np.full(n, -np.inf)
    for i in range(n):
        if not is_land[i] or biome[i] not in HOSPITABLE:
            continue
        s = 0.0
        s += 2.5 if coastal[i] else 0.0
        s += min(float(flow[i]), 8.0) * 0.6          # river access
        nbr_elev = [abs(elevation[j] - elevation[i]) for j in neighbors[i]]
        s += (1.0 - min(np.mean(nbr_elev) * 12, 1.0)) if nbr_elev else 0.0  # flatness
        s += float(rng.random()) * 0.4               # tie-breaking character
        score[i] = s

    counts = {"capital": settings.get("n_capitals", 4), "town": settings.get("n_towns", 10),
              "village": settings.get("n_villages", 16)}
    min_dist = {"capital": 0.16, "town": 0.07, "village": 0.045}
    pops = {"capital": (60_000, 220_000), "town": (6_000, 40_000), "village": (200, 3_000)}

    namer = NameGenerator(rng)
    placed: list[Settlement] = []
    order = np.argsort(-score)
    taken: list[np.ndarray] = []

    for kind in ("capital", "town", "village"):
        want = counts[kind]
        got = 0
        for i in order:
            if got >= want or not np.isfinite(score[i]):
                break
            p = pts[i]
            if any(np.hypot(*(p - q)) < min_dist[kind] for q in taken):
                continue
            lo, hi = pops[kind]
            placed.append(
                Settlement(
                    name=namer.generate(),
                    x=float(p[0]), y=float(p[1]), kind=kind,
                    population=int(rng.integers(lo, hi)),
                )
            )
            taken.append(p)
            got += 1
    return placed
