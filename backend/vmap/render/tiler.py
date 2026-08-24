"""XYZ raster tile renderer.

Tile (z, x, y) covers the normalized-square region
[x/2^z, (x+1)/2^z] x [y/2^z, (y+1)/2^z] — standard slippy scheme over the
world's normalized mercator coordinates. Tiles render on demand with a
2x supersample for antialiasing, and a coarse grid index keeps per-tile
work proportional to visible cells.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from ..worldgen.model import World
from .palette import BIOME_COLORS, COAST_COLOR, RIVER_COLOR, shade

TILE = 256
SS = 2  # supersample factor
GRID = 64  # spatial index resolution


class WorldRenderer:
    def __init__(self, world: World):
        self.world = world
        self.cell_colors = self._precompute_colors()
        self.index = self._build_index()
        self.coastal = self._find_coastal()

    def _precompute_colors(self) -> list[tuple[int, int, int]]:
        w = self.world
        colors = []
        for i in range(len(w.points)):
            base = BIOME_COLORS[int(w.biome[i])]
            if w.is_land[i]:
                # brighten with altitude for a cheap hillshade feel
                f = 0.92 + (w.elevation[i] - w.sea_level) * 0.55
            else:
                f = 0.85 + w.elevation[i] * 0.3
            colors.append(shade(base, float(f)))
        return colors

    def _build_index(self) -> dict[tuple[int, int], list[int]]:
        idx: dict[tuple[int, int], list[int]] = {}
        for i, poly in enumerate(self.world.polygons):
            x0, y0 = poly.min(axis=0)
            x1, y1 = poly.max(axis=0)
            for gx in range(int(x0 * GRID), min(int(x1 * GRID) + 1, GRID)):
                for gy in range(int(y0 * GRID), min(int(y1 * GRID) + 1, GRID)):
                    idx.setdefault((gx, gy), []).append(i)
        return idx

    def _find_coastal(self) -> set[int]:
        w = self.world
        return {
            i for i in range(len(w.points))
            if w.is_land[i] and any(not w.is_land[j] for j in w.neighbors[i])
        }

    def cells_in(self, x0: float, y0: float, x1: float, y1: float) -> list[int]:
        found: set[int] = set()
        for gx in range(max(0, int(x0 * GRID)), min(int(x1 * GRID) + 1, GRID)):
            for gy in range(max(0, int(y0 * GRID)), min(int(y1 * GRID) + 1, GRID)):
                found.update(self.index.get((gx, gy), []))
        return list(found)

    def render_tile(self, z: int, x: int, y: int) -> Image.Image:
        n = 2 ** z
        span = 1.0 / n
        x0, y0 = x * span, y * span
        pad = span * 0.05
        size = TILE * SS
        scale = size / span

        img = Image.new("RGB", (size, size), BIOME_COLORS[0])
        draw = ImageDraw.Draw(img)

        def to_px(px: float, py: float) -> tuple[float, float]:
            return (px - x0) * scale, (py - y0) * scale

        cells = self.cells_in(x0 - pad, y0 - pad, x0 + span + pad, y0 + span + pad)
        # draw ocean cells first, land on top, coastline strokes last
        for land_pass in (False, True):
            for i in cells:
                if bool(self.world.is_land[i]) != land_pass:
                    continue
                pts = [to_px(px, py) for px, py in self.world.polygons[i]]
                if len(pts) >= 3:
                    draw.polygon(pts, fill=self.cell_colors[i])
        for i in cells:
            if i in self.coastal:
                pts = [to_px(px, py) for px, py in self.world.polygons[i]]
                if len(pts) >= 3:
                    draw.line(pts + [pts[0]], fill=COAST_COLOR, width=max(1, SS * max(0, z - 2)))

        # rivers: width grows with zoom
        if z >= 3:
            rw = max(1, int(SS * (z - 2) * 0.9))
            for river in self.world.rivers:
                rx0, ry0 = river.min(axis=0)
                rx1, ry1 = river.max(axis=0)
                if rx1 < x0 - pad or rx0 > x0 + span + pad or ry1 < y0 - pad or ry0 > y0 + span + pad:
                    continue
                draw.line([to_px(px, py) for px, py in river], fill=RIVER_COLOR, width=rw, joint="curve")

        return img.resize((TILE, TILE), Image.LANCZOS)
