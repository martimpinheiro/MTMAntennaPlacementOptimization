import os
import json
import sys
from ortools.sat.python import cp_model

def load_map_data(filename='map_data.json'):
    if not os.path.exists(filename):
        print(f"Error: External map data file '{filename}' not found.")
        print("Please run map_generator.py first to output the grid parameters.")
        sys.exit(1)
    with open(filename, 'r') as f:
        return json.load(f)

def get_covered_cells(src_idx, radius, grid_cols, grid_rows):
    """Returns all cell indices reachable from src within Manhattan radius."""
    row = src_idx // grid_cols
    col = src_idx % grid_cols
    return [
        r * grid_cols + c
        for r in range(grid_rows)
        for c in range(grid_cols)
        if abs(row - r) + abs(col - c) <= radius
    ]

def solve_network():
    map_config = load_map_data('map_data.json')

    GRID_ROWS      = map_config.get('rows', 6)
    GRID_COLS      = map_config.get('cols', 6)
    NUM_CELLS      = GRID_ROWS * GRID_COLS
    NUM_PROVIDERS  = map_config.get('num_providers', 4)
    PROVIDER_RADII = map_config.get('provider_radii', [0, 1, 1, 2])
    PENALTY_COST   = map_config.get('penalty_cost', 800)
    ANTENNA_COST   = map_config.get('antenna_slot_cost', 100)
    MAX_TENANTS    = 4  # Physical co-location cap per tower mast

    BANNED_ZONES   = set(map_config.get('banned_zones', []))
    FOREST_ZONES   = set(map_config.get('forest_zones', []))
    BUILDING_ZONES = set(map_config.get('building_zones', []))

    # Cells that actually require coverage (mountains don't need service)
    COVERABLE = [i for i in range(NUM_CELLS) if i not in BANNED_ZONES]

    def get_tower_base_cost(cell_idx):
        if cell_idx in BUILDING_ZONES: return 2500
        if cell_idx in FOREST_ZONES:   return 1500
        return 1000

    # Precompute: for each (provider, target), which source cells can cover it
    coverage_sources = {
        (k, tgt): [
            src for src in range(NUM_CELLS)
            if tgt in get_covered_cells(src, PROVIDER_RADII[k], GRID_COLS, GRID_ROWS)
        ]
        for k in range(NUM_PROVIDERS)
        for tgt in COVERABLE
    }

    model = cp_model.CpModel()

    towers  = [model.NewBoolVar(f'tower_{i}') for i in range(NUM_CELLS)]
    antennas = {k: [model.NewBoolVar(f'ant_p{k}_c{i}') for i in range(NUM_CELLS)]
                for k in range(NUM_PROVIDERS)}
    slacks  = {k: {tgt: model.NewBoolVar(f'slack_p{k}_c{tgt}') for tgt in COVERABLE}
               for k in range(NUM_PROVIDERS)}

    # Rule A: No towers on banned terrain
    for i in BANNED_ZONES:
        model.Add(towers[i] == 0)

    for i in range(NUM_CELLS):
        # Rule B: Antenna requires a tower at the same cell
        for k in range(NUM_PROVIDERS):
            model.Add(antennas[k][i] <= towers[i])
        # Rule D: Physical co-location cap
        model.Add(sum(antennas[k][i] for k in range(NUM_PROVIDERS)) <= MAX_TENANTS)

    # Rule C: Each coverable cell must be served or pay a dropout penalty
    for (k, tgt), sources in coverage_sources.items():
        model.Add(sum(antennas[k][src] for src in sources) + slacks[k][tgt] >= 1)

    total_tower_cost  = sum(towers[i] * get_tower_base_cost(i) for i in range(NUM_CELLS))
    total_antenna_cost = sum(sum(antennas[k]) for k in range(NUM_PROVIDERS)) * ANTENNA_COST
    total_penalty     = sum(slacks[k][tgt]
                            for k in range(NUM_PROVIDERS)
                            for tgt in COVERABLE) * PENALTY_COST

    model.Minimize(total_tower_cost + total_antenna_cost + total_penalty)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("Solver was unable to compute a feasible constraint arrangement.")
        return

    print("=" * 60)
    print("   MULTI-BAND REIFIED INFRASTRUCTURE LAYOUT OPTIMIZER   ")
    print("=" * 60)
    print(f"Global Net Cost Objective : €{int(solver.ObjectiveValue())}")
    print(f"Physical Towers Constructed: {sum(solver.Value(towers[i]) for i in range(NUM_CELLS))} Units")
    print("-" * 60)

    print("PROVIDER CAPABILITY DEPLOYMENT ANALYSIS:")
    for k in range(NUM_PROVIDERS):
        k_ants  = sum(solver.Value(antennas[k][i]) for i in range(NUM_CELLS))
        k_drops = sum(solver.Value(slacks[k][tgt]) for tgt in COVERABLE)
        k_cov   = ((len(COVERABLE) - k_drops) * 100) // len(COVERABLE)
        print(f" -> Provider {k} [R={PROVIDER_RADII[k]}]: "
              f"Antennas = {k_ants:2d} | Drops = {k_drops:2d} | Coverage = {k_cov}%")

    print("-" * 60)
    print("GRID TOPOGRAPHY LEDGER:")
    print(".=Plains | F=Forest | B=Building | M=Mountain (Banned)")
    print("TX(Y) -> Tower built with X active co-located antennas on Y terrain")
    print("-" * 60)

    for r in range(GRID_ROWS):
        row_str = []
        for c in range(GRID_COLS):
            idx = r * GRID_COLS + c
            if idx in BANNED_ZONES:      t_char = "M"
            elif idx in FOREST_ZONES:    t_char = "F"
            elif idx in BUILDING_ZONES:  t_char = "B"
            else:                        t_char = "."

            if solver.Value(towers[idx]):
                tenants = sum(solver.Value(antennas[k][idx]) for k in range(NUM_PROVIDERS))
                row_str.append(f"T{tenants}({t_char})")
            else:
                row_str.append(f"  {t_char}  ")
        print(" ".join(row_str))
    print("=" * 60)

if __name__ == '__main__':
    solve_network()
