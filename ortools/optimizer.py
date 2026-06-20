"""
OR-Tools CP-SAT solver for the Multi-Tenant Antenna Placement problem.

Decision variables (Boolean):
  t[i]     - tower built at cell i
  a[k][i]  - provider k has antenna at cell i
  s[k][j]  - cell j is NOT covered by provider k (slack)

Constraints:
  C1: t[i] = 0 for banned cells (mountains)
  C2: a[k][i] <= t[i]  (antenna needs a tower)
  C3: sum_k a[k][i] <= 4  (max 4 tenants per tower)
  C4: sum_{i in cov(k,j)} a[k][i] + s[k][j] >= 1  (cover or pay penalty)

Objective: minimise tower costs + antenna slots (100 each) + uncoverage penalties (800 each)
"""

import os
import json
import sys
from ortools.sat.python import cp_model

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_map_data():
    filename = os.path.join(_ROOT, 'map_data.json')
    if not os.path.exists(filename):
        print(f"Error: '{filename}' not found. Run map_generator.py first.")
        sys.exit(1)
    with open(filename, 'r') as f:
        return json.load(f)


def get_covered_cells(src_idx, radius, grid_cols, grid_rows):
    """Return all cell indices within Manhattan radius of src_idx."""
    row = src_idx // grid_cols
    col = src_idx % grid_cols
    return [
        r * grid_cols + c
        for r in range(grid_rows)
        for c in range(grid_cols)
        if abs(row - r) + abs(col - c) <= radius
    ]


def solve_network(verbose=True, timeout=10.0):
    """Build and solve the antenna placement model. Returns {cost, coverage_pct} or None."""
    map_config = load_map_data()

    GRID_ROWS      = map_config.get('rows', 6)
    GRID_COLS      = map_config.get('cols', 6)
    NUM_CELLS      = GRID_ROWS * GRID_COLS
    NUM_PROVIDERS  = map_config.get('num_providers', 4)
    PROVIDER_RADII = map_config.get('provider_radii', [0, 1, 1, 2])
    PENALTY_COST   = map_config.get('penalty_cost', 800)
    ANTENNA_COST   = map_config.get('antenna_slot_cost', 100)
    MAX_TENANTS    = 4

    BANNED_ZONES   = set(map_config.get('banned_zones', []))
    FOREST_ZONES   = set(map_config.get('forest_zones', []))
    BUILDING_ZONES = set(map_config.get('building_zones', []))
    COVERABLE      = [i for i in range(NUM_CELLS) if i not in BANNED_ZONES]

    def get_tower_base_cost(cell_idx):
        if cell_idx in BUILDING_ZONES: return 2500
        if cell_idx in FOREST_ZONES:   return 1500
        return 1000

    # Precompute which source cells can cover each (provider, target) pair
    coverage_sources = {
        (k, tgt): [
            src for src in range(NUM_CELLS)
            if tgt in get_covered_cells(src, PROVIDER_RADII[k], GRID_COLS, GRID_ROWS)
        ]
        for k in range(NUM_PROVIDERS)
        for tgt in COVERABLE
    }

    model = cp_model.CpModel()

    towers   = [model.NewBoolVar(f'tower_{i}') for i in range(NUM_CELLS)]
    antennas = {k: [model.NewBoolVar(f'ant_p{k}_c{i}') for i in range(NUM_CELLS)]
                for k in range(NUM_PROVIDERS)}
    slacks   = {k: {tgt: model.NewBoolVar(f'slack_p{k}_c{tgt}') for tgt in COVERABLE}
                for k in range(NUM_PROVIDERS)}

    # C1 - no tower on mountain
    for i in BANNED_ZONES:
        model.Add(towers[i] == 0)

    # C2 + C3 - antenna requires tower; at most MAX_TENANTS per tower
    for i in range(NUM_CELLS):
        for k in range(NUM_PROVIDERS):
            model.Add(antennas[k][i] <= towers[i])
        model.Add(sum(antennas[k][i] for k in range(NUM_PROVIDERS)) <= MAX_TENANTS)

    # C4 - cover cell j with provider k, or activate the slack (pay penalty)
    for (k, tgt), sources in coverage_sources.items():
        model.Add(sum(antennas[k][src] for src in sources) + slacks[k][tgt] >= 1)

    total_tower_cost   = sum(towers[i] * get_tower_base_cost(i) for i in range(NUM_CELLS))
    total_antenna_cost = sum(sum(antennas[k]) for k in range(NUM_PROVIDERS)) * ANTENNA_COST
    total_penalty      = sum(slacks[k][tgt]
                             for k in range(NUM_PROVIDERS)
                             for tgt in COVERABLE) * PENALTY_COST

    model.Minimize(total_tower_cost + total_antenna_cost + total_penalty)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if verbose:
            print("No solution found within time limit.")
        return None

    cost         = int(solver.ObjectiveValue())
    total_drops  = sum(solver.Value(slacks[k][tgt])
                       for k in range(NUM_PROVIDERS) for tgt in COVERABLE)
    total_poss   = len(COVERABLE) * NUM_PROVIDERS
    coverage_pct = ((total_poss - total_drops) * 100) // total_poss

    if verbose:
        towers_built = sum(solver.Value(towers[i]) for i in range(NUM_CELLS))
        print(f"\nSolution found!")
        print(f"  Total cost : €{cost}")
        print(f"  Towers built: {towers_built}")
        print(f"  Overall coverage: {coverage_pct}%")
        print()
        print("Provider breakdown:")
        for k in range(NUM_PROVIDERS):
            k_ants  = sum(solver.Value(antennas[k][i]) for i in range(NUM_CELLS))
            k_drops = sum(solver.Value(slacks[k][tgt]) for tgt in COVERABLE)
            k_cov   = ((len(COVERABLE) - k_drops) * 100) // len(COVERABLE)
            print(f"  P{k} (radius={PROVIDER_RADII[k]}): {k_ants} antennas, {k_cov}% coverage")
        print()
        print("Grid layout:  . Plains  F Forest  B Building  M Mountain")
        print("              T<n>(<terrain>) = tower with n active antennas")
        for r in range(GRID_ROWS):
            row_str = []
            for c in range(GRID_COLS):
                idx = r * GRID_COLS + c
                if idx in BANNED_ZONES:     t_char = "M"
                elif idx in FOREST_ZONES:   t_char = "F"
                elif idx in BUILDING_ZONES: t_char = "B"
                else:                       t_char = "."
                if solver.Value(towers[idx]):
                    tenants = sum(solver.Value(antennas[k][idx]) for k in range(NUM_PROVIDERS))
                    row_str.append(f"T{tenants}({t_char})")
                else:
                    row_str.append(f"  {t_char}  ")
            print(" ".join(row_str))
        print()

    return {'cost': cost, 'coverage_pct': coverage_pct}


if __name__ == '__main__':
    if '--benchmark' in sys.argv:
        timeout = float(sys.argv[sys.argv.index('--timeout') + 1]) if '--timeout' in sys.argv else 10.0
        result = solve_network(verbose=False, timeout=timeout)
        if result:
            print(f"RESULT:{result['cost']},{result['coverage_pct']}")
    else:
        solve_network()
