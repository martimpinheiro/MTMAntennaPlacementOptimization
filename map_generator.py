"""
Random map generator for the antenna placement problem.

Generates an R×C grid and assigns terrain types:
  Plains (.)  - €1 000 to build
  Forest (F)  - €1 500 to build
  Building (B)- €2 500 to build
  Mountain (M)- banned, no tower allowed

Proportions: ~12% mountains, ~20% forest, ~15% buildings, rest plains.
Output is written to map_data.json.
"""

import json
import random
import os


def generate_and_save_map(rows=6, cols=6, filename='map_data.json', seed=None):
    """Generate a random map and save it to JSON.

    Args:
        rows, cols: grid dimensions.
        filename:   output path.
        seed:       random seed for reproducibility.
    """
    if seed is not None:
        random.seed(seed)

    num_cells = rows * cols

    num_providers = 4
    provider_radii = [0, 1, 1, 2]  # P0=5G mmWave, P1/P2=mid-band, P3=macro LTE
    penalty_cost = 800
    antenna_slot_cost = 100

    all_indices = list(range(num_cells))
    random.shuffle(all_indices)

    num_banned    = max(2, int(num_cells * 0.12))
    num_forests   = max(4, int(num_cells * 0.20))
    num_buildings = max(3, int(num_cells * 0.15))

    banned_zones   = sorted(all_indices[:num_banned])
    forest_zones   = sorted(all_indices[num_banned : num_banned + num_forests])
    building_zones = sorted(all_indices[num_banned + num_forests : num_banned + num_forests + num_buildings])

    map_dataset = {
        "rows": rows,
        "cols": cols,
        "num_providers": num_providers,
        "provider_radii": provider_radii,
        "penalty_cost": penalty_cost,
        "antenna_slot_cost": antenna_slot_cost,
        "banned_zones": banned_zones,
        "forest_zones": forest_zones,
        "building_zones": building_zones,
    }

    if seed is not None:
        map_dataset["seed"] = seed

    with open(filename, 'w') as f:
        json.dump(map_dataset, f, indent=4)

    banned_set   = set(banned_zones)
    forest_set   = set(forest_zones)
    building_set = set(building_zones)

    print(f"Map saved to {os.path.abspath(filename)} ({rows}x{cols})")
    for r in range(rows):
        row_str = []
        for c in range(cols):
            idx = r * cols + c
            if idx in banned_set:      row_str.append(" M ")
            elif idx in forest_set:    row_str.append(" F ")
            elif idx in building_set:  row_str.append(" B ")
            else:                      row_str.append(" . ")
        print(" ".join(row_str))


if __name__ == '__main__':
    generate_and_save_map(rows=6, cols=6)
