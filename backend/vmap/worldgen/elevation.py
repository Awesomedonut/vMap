"""Stage 2-3: elevation from layered value noise shaped by a preset mask."""

from __future__ import annotations

import numpy as np

from .noise import fbm


def compute_elevation(rng: np.random.Generator, pts: np.ndarray, settings: dict) -> np.ndarray:
    seed = int(rng.integers(0, 2**31))
    preset = settings.get("preset", "continents")

    e = fbm(pts, seed, octaves=5, base_freq=settings.get("base_freq", 2.4))
    e = (e - e.min()) / (e.max() - e.min())  # -> [0,1]

    cx, cy = pts[:, 0] - 0.5, pts[:, 1] - 0.5
    r = np.sqrt(cx**2 + cy**2) / 0.7071  # 0 at center -> 1 at corner

    if preset == "pangaea":
        mask = 1.0 - np.clip(r * 1.25, 0, 1) ** 2
        e = e * 0.6 + mask * 0.5
    elif preset == "archipelago":
        e = fbm(pts, seed + 101, octaves=5, base_freq=4.5)
        e = (e - e.min()) / (e.max() - e.min())
        e = e * (1.0 - np.clip(r, 0, 1) ** 2 * 0.35)
    else:  # continents
        mask = 1.0 - np.clip(r, 0, 1) ** 2
        e = e * 0.8 + mask * 0.25

    return np.clip(e, 0.0, 1.0)
