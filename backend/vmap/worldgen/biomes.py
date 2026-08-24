"""Stage 5b: Whittaker-style biome assignment from temperature x moisture."""

from __future__ import annotations

import numpy as np

# indices into model.BIOME_NAMES
DEEP_OCEAN, OCEAN, SHALLOWS, BEACH = 0, 1, 2, 3
TUNDRA, TAIGA, TEMPERATE_FOREST, GRASSLAND = 4, 5, 6, 7
SHRUBLAND, DESERT, SAVANNA, JUNGLE, SWAMP, MOUNTAIN, SNOW_PEAK = 8, 9, 10, 11, 12, 13, 14


def assign_biomes(
    elevation: np.ndarray,
    is_land: np.ndarray,
    temperature: np.ndarray,
    moisture: np.ndarray,
    flow: np.ndarray,
    sea_level: float,
) -> np.ndarray:
    n = len(elevation)
    biome = np.empty(n, dtype=np.int16)

    # water depths
    biome[~is_land] = np.where(
        elevation[~is_land] < sea_level - 0.12,
        DEEP_OCEAN,
        np.where(elevation[~is_land] < sea_level - 0.03, OCEAN, SHALLOWS),
    )

    t, m = temperature, moisture
    land = is_land
    alt = elevation - sea_level

    cond = [
        (land & (alt > 0.34), SNOW_PEAK),
        (land & (alt > 0.24), MOUNTAIN),
        (land & (alt < 0.015), BEACH),
        (land & (t < 0.22), TUNDRA),
        (land & (t < 0.42) & (m > 0.35), TAIGA),
        (land & (t < 0.42), TUNDRA),
        (land & (t > 0.72) & (m > 0.62), JUNGLE),
        (land & (t > 0.72) & (m > 0.32), SAVANNA),
        (land & (t > 0.72), DESERT),
        (land & (m > 0.72) & (flow > 2.0), SWAMP),
        (land & (m > 0.55), TEMPERATE_FOREST),
        (land & (m > 0.32), GRASSLAND),
        (land, SHRUBLAND),
    ]
    assigned = np.zeros(n, dtype=bool)
    for mask, b in cond:
        pick = mask & ~assigned & land
        biome[pick] = b
        assigned |= pick
    return biome
