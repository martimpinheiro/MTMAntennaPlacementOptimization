import os
import json
import sys
from ortools.sat.python import cp_model

def load_map_data(filename='map_data.json'):
    """Safely loads dynamically generated map data from an external JSON file."""
    if not os.path.exists(filename):
        print(f"Error: External map data file '{filename}' not found.")
        print("Please run your map generator script first to output the grid parameters.")
        sys.exit(1)
        
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def get_provider_covered_cells(src_idx, provider_k, grid_cols, grid_rows):
    """
    Calculates coverage footprint based on a provider's specific frequency band.
    P0: High-frequency / 5G mmWave  -> Radius 0 (Cellular Small Cell)
    P1: Mid-band / Standard 4G-5G    -> Radius 1 (Cardinal neighbors)
    P2: Mid-band / Standard 4G-5G    -> Radius 1 (Cardinal neighbors)
    P3: Low-band / Long-range Macro  -> Radius 2 (Manhattan distance <= 2)
    """
    row = src_idx // grid_cols
    col = src_idx % grid_cols
    
    # Define frequency band range profiles
    if provider_k == 0:
        radius = 0  
    elif provider_k == 3:
        radius = 2  
    else:
        radius = 1  
        
    covered = []
    for r in range(grid_rows):
        for c in range(grid_cols):
            tgt_idx = r * grid_cols + c
            # Calculate grid distance (Manhattan Routing)
            distance = abs(row - r) + abs(col - c)
            if distance <= radius:
                covered.append(tgt_idx)
    return covered

def solve_network():
    # 1. READ CONFIGURATION EXTENSION DATA SHEET
    map_config = load_map_data('map_data.json')
    
    GRID_ROWS = map_config.get('rows', 6)
    GRID_COLS = map_config.get('cols', 6)
    NUM_CELLS = GRID_ROWS * GRID_COLS
    NUM_PROVIDERS = map_config.get('num_providers', 4)
    
    PENALTY_COST = map_config.get('penalty_cost', 800)
    ANTENNA_SLOT_COST = map_config.get('antenna_slot_cost', 100)
    
    BANNED_ZONES = map_config.get('banned_zones', [])
    FOREST_ZONES = map_config.get('forest_zones', [])
    BUILDING_ZONES = map_config.get('building_zones', [])

    # Dynamic Pricing Engine by Terrain Profile
    def get_tower_base_cost(cell_idx):
        if cell_idx in BUILDING_ZONES: return 2500  # Urban premium infrastructure
        if cell_idx in FOREST_ZONES: return 1500    # Environmental clearing mitigation
        return 1000                                 # Open fields

    # Initialize CP-SAT Model Engine
    model = cp_model.CpModel()
    
    # 2. DECISION VARIABLES
    towers = [model.NewBoolVar(f'tower_{i}') for i in range(NUM_CELLS)]
    
    antennas = {}
    for k in range(NUM_PROVIDERS):
        antennas[k] = [model.NewBoolVar(f'ant_p{k}_c{i}') for i in range(NUM_CELLS)]
        
    slacks = {}
    for k in range(NUM_PROVIDERS):
        slacks[k] = [model.NewBoolVar(f'slack_p{k}_c{i}') for i in range(NUM_CELLS)]

    # 3. MATHEMATICAL CONSTRAINT MATRIX
    for i in range(NUM_CELLS):
        # Rule A: Banned Mountain Terrain Constraint
        if i in BANNED_ZONES:
            model.Add(towers[i] == 0)
            
        # Rule B: Structural Coupling Constraint
        for k in range(NUM_PROVIDERS):
            model.Add(antennas[k][i] <= towers[i])
            
        # Physical Tower Capacity Co-location Cap (Max 4 tenants per mast frame)
        model.Add(sum(antennas[k][i] for k in range(NUM_PROVIDERS)) <= 4)

    # Rule C: Provider-Aware Heterogeneous Signal Routing Matrix
    for k in range(NUM_PROVIDERS):
        for tgt in range(NUM_CELLS):
            valid_sources = [
                src for src in range(NUM_CELLS) 
                if tgt in get_provider_covered_cells(src, k, GRID_COLS, GRID_ROWS)
            ]
            # Ensure coverage via antenna routing, or take a financial dropout slack penalty
            model.Add(sum(antennas[k][src] for src in valid_sources) + slacks[k][tgt] >= 1)

    # 4. TERRAIN-WEIGHTED FINANCIAL OBJECTIVE
    total_tower_cost = sum(towers[i] * get_tower_base_cost(i) for i in range(NUM_CELLS))
    total_antennas_deployed = sum(sum(antennas[k]) for k in range(NUM_PROVIDERS))
    total_dropped_cells = sum(sum(slacks[k]) for k in range(NUM_PROVIDERS))
    
    model.Minimize(
        total_tower_cost + 
        (total_antennas_deployed * ANTENNA_SLOT_COST) + 
        (total_dropped_cells * PENALTY_COST)
    )

    # 5. EXECUTE SOLVER RUN
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)
    
    # 6. PERFORMANCE RENDERING & LEDGER VISUALIZATION
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("=" * 60)
        print("   MULTI-BAND REIFIED INFRASTRUCTURE LAYOUT OPTIMIZER   ")
        print("=" * 60)
        print(f"Global Net Cost Objective : €{int(solver.ObjectiveValue())}")
        print(f"Physical Towers Constructed: {sum(int(solver.Value(towers[i])) for i in range(NUM_CELLS))} Units")
        print("-" * 60)
        
        # Breakdown Metrics Per Operator
        print("PROVIDER CAPABILITY DEPLOYMENT ANALYSIS:")
        for k in range(NUM_PROVIDERS):
            k_ants = sum(int(solver.Value(antennas[k][i])) for i in range(NUM_CELLS))
            k_drops = sum(int(solver.Value(slacks[k][i])) for i in range(NUM_CELLS))
            k_cov = ((NUM_CELLS - k_drops) * 100) // NUM_CELLS
            
            # Map band descriptor strings
            band_desc = "High-Band (R=0)" if k==0 else "Low-Band (R=2)" if k==3 else "Mid-Band (R=1)"
            print(f" -> Provider {k} [{band_desc}]: Antennas Deployed = {k_ants:2d} | Signal Drops = {k_drops:2d} | Coverage = {k_cov}%")
            
        print("-" * 60)
        print("GRID TOPOGRAPHY LEDGER:")
        print(".=Plains | F=Forest | B=Building | M=Mountain (Banned)")
        print("TX(Y) -> Tower built with X active co-located antennas on Y terrain")
        print("-" * 60)
        
        for r in range(GRID_ROWS):
            row_str = []
            for c in range(GRID_COLS):
                idx = r * GRID_COLS + c
                if idx in BANNED_ZONES: t_char = "M"
                elif idx in FOREST_ZONES: t_char = "F"
                elif idx in BUILDING_ZONES: t_char = "B"
                else: t_char = "."
                
                if solver.Value(towers[idx]) == 1:
                    sharing_count = sum(int(solver.Value(antennas[k][idx])) for k in range(NUM_PROVIDERS))
                    row_str.append(f"T{sharing_count}({t_char})")
                else:
                    row_str.append(f"  {t_char}  ")
            print(" ".join(row_str))
        print("=" * 60)
    else:
        print("Solver was unable to compute a feasible constraint arrangement.")

if __name__ == '__main__':
    solve_network()