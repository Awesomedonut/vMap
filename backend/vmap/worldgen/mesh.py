"""Stage 1: irregular cell mesh via jittered-grid points + Voronoi.

Points are reflected across all four edges of the unit square before
computing the Voronoi diagram so every interior region is finite and
naturally clipped to the square.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import Voronoi


def build_mesh(rng: np.random.Generator, grid_n: int) -> tuple[np.ndarray, list[np.ndarray], list[list[int]]]:
    """Return (points (N,2), polygons, neighbors) for an N = grid_n^2 cell mesh."""
    ax = (np.arange(grid_n) + 0.5) / grid_n
    gx, gy = np.meshgrid(ax, ax)
    jitter = (rng.random((grid_n * grid_n, 2)) - 0.5) * (0.9 / grid_n)
    points = np.column_stack([gx.ravel(), gy.ravel()]) + jitter
    points = np.clip(points, 1e-6, 1 - 1e-6)
    n = len(points)

    mirrored = [points]
    for axis, bound in ((0, 0.0), (0, 1.0), (1, 0.0), (1, 1.0)):
        m = points.copy()
        m[:, axis] = 2 * bound - m[:, axis]
        mirrored.append(m)
    vor = Voronoi(np.vstack(mirrored))

    polygons: list[np.ndarray] = []
    for i in range(n):
        region = vor.regions[vor.point_region[i]]
        poly = vor.vertices[region]
        polygons.append(np.clip(poly, 0.0, 1.0))

    neighbors: list[list[int]] = [[] for _ in range(n)]
    for (p, q) in vor.ridge_points:
        if p < n and q < n:
            neighbors[p].append(int(q))
            neighbors[q].append(int(p))
    return points, polygons, neighbors
