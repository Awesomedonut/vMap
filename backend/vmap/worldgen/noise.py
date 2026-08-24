"""Fast deterministic 2D fractal value noise, fully vectorized in numpy.

Hash-based lattice noise with smoothstep interpolation — lower fidelity
than simplex but indistinguishable at map scale, and ~100x faster than
per-point scalar noise calls.
"""

from __future__ import annotations

import numpy as np

_M1 = np.uint64(0x9E3779B185EBCA87)
_M2 = np.uint64(0xC2B2AE3D27D4EB4F)


def _hash01(ix: np.ndarray, iy: np.ndarray, seed: int) -> np.ndarray:
    """Lattice corner -> pseudorandom float in [0, 1)."""
    h = ix.astype(np.uint64) * _M1 + iy.astype(np.uint64) * _M2 + np.uint64(seed)
    h ^= h >> np.uint64(29)
    h *= _M1
    h ^= h >> np.uint64(32)
    return (h & np.uint64(0xFFFFFF)).astype(np.float64) / float(0x1000000)


def _smooth(t: np.ndarray) -> np.ndarray:
    return t * t * (3.0 - 2.0 * t)


def value_noise(pts: np.ndarray, freq: float, seed: int) -> np.ndarray:
    """Per-point noise in [-1, 1] at the given lattice frequency."""
    x, y = pts[:, 0] * freq, pts[:, 1] * freq
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = _smooth(x - ix), _smooth(y - iy)
    v00 = _hash01(ix, iy, seed)
    v10 = _hash01(ix + 1, iy, seed)
    v01 = _hash01(ix, iy + 1, seed)
    v11 = _hash01(ix + 1, iy + 1, seed)
    top = v00 + (v10 - v00) * fx
    bot = v01 + (v11 - v01) * fx
    return (top + (bot - top) * fy) * 2.0 - 1.0


def fbm(pts: np.ndarray, seed: int, octaves: int = 5, base_freq: float = 2.4) -> np.ndarray:
    """Fractal sum of value noise octaves, roughly in [-1, 1]."""
    out = np.zeros(len(pts))
    amp, freq, total = 1.0, base_freq, 0.0
    for o in range(octaves):
        out += amp * value_noise(pts, freq, seed + o * 7919)
        total += amp
        amp *= 0.5
        freq *= 2.13
    return out / total
