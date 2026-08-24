"""Terrain palette for the raster tile renderer (parchment-atlas theme)."""

# biome index -> RGB
BIOME_COLORS: dict[int, tuple[int, int, int]] = {
    0: (38, 62, 92),      # deep ocean
    1: (52, 82, 116),     # ocean
    2: (88, 124, 152),    # shallows
    3: (216, 200, 158),   # beach
    4: (200, 204, 196),   # tundra
    5: (108, 138, 108),   # taiga
    6: (94, 138, 84),     # temperate forest
    7: (150, 172, 108),   # grassland
    8: (172, 168, 120),   # shrubland
    9: (222, 196, 138),   # desert
    10: (188, 178, 98),   # savanna
    11: (62, 116, 70),    # jungle
    12: (96, 116, 88),    # swamp
    13: (140, 132, 124),  # mountain
    14: (240, 242, 244),  # snow peak
}

RIVER_COLOR = (70, 106, 140)
COAST_COLOR = (46, 64, 82)


def shade(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Brighten (>1) or darken (<1) a color."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)  # type: ignore[return-value]
