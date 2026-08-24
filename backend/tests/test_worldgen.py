"""Worldgen invariants: determinism (golden behavior) and structural properties."""

import numpy as np
import pytest

from vmap.worldgen.pipeline import generate

SEED = 12345
SETTINGS = {"grid_n": 64}


@pytest.fixture(scope="module")
def world():
    return generate(SEED, SETTINGS)


@pytest.mark.unit
def test_same_seed_reproduces_identical_world(world):
    again = generate(SEED, SETTINGS)
    assert np.array_equal(world.elevation, again.elevation)
    assert np.array_equal(world.biome, again.biome)
    assert world.name == again.name
    assert [s.name for s in world.settlements] == [s.name for s in again.settlements]


@pytest.mark.unit
def test_different_seed_produces_different_world(world):
    other = generate(SEED + 1, SETTINGS)
    assert not np.array_equal(world.elevation, other.elevation)


@pytest.mark.unit
def test_ocean_fraction_is_respected(world):
    ocean = 1.0 - world.is_land.mean()
    assert abs(ocean - world.settings["ocean_fraction"]) < 0.02


@pytest.mark.unit
def test_settlements_are_on_land(world):
    assert len(world.settlements) > 0
    land_points = world.points[world.is_land]
    for s in world.settlements:
        dists = np.hypot(land_points[:, 0] - s.x, land_points[:, 1] - s.y)
        assert dists.min() < 1e-9, f"{s.name} is not on a land cell"


@pytest.mark.unit
def test_settlement_names_are_unique(world):
    names = [s.name for s in world.settlements]
    assert len(names) == len(set(names))


@pytest.mark.unit
def test_rivers_flow_downhill_to_water(world):
    # each river polyline should end at (or adjacent to) a non-land cell,
    # or terminate in a pit — but never climb back uphill overall
    for river in world.rivers:
        assert len(river) >= 3
        start, end = river[0], river[-1]
        # end is inside the world square
        assert 0.0 <= end[0] <= 1.0 and 0.0 <= end[1] <= 1.0
        # net descent: elevation at nearest cell to start >= at end
        def elev_at(p):
            i = int(np.argmin(np.hypot(world.points[:, 0] - p[0], world.points[:, 1] - p[1])))
            return world.elevation[i]
        assert elev_at(start) >= elev_at(end)
