import json
import random
import os

def generate_and_save_map(rows=6, cols=6, filename='map_data.json'):
    """
    Generates a telecom landscape configuration matrix with varied terrain distribution,
    ready for execution via the CP-SAT engine pipeline conduit.
    """
    num_cells = rows * cols
    
    num_providers = 4
    penalty_cost = 800       
    antenna_slot_cost = 100  
    
    all_indices = list(range(num_cells))
    random.shuffle(all_indices)
    
    # Dynamic proportional allocations based on grid surface bounds
    num_banned = max(2, int(num_cells * 0.12))     # Mountains
    num_forests = max(4, int(num_cells * 0.20))    # Dense Forests
    num_buildings = max(3, int(num_cells * 0.15))  # Urban Zones
    
    banned_zones = sorted(all_indices[:num_banned])
    forest_zones = sorted(all_indices[num_banned : num_banned + num_forests])
    building_zones = sorted(all_indices[num_banned + num_forests : num_banned + num_forests + num_buildings])
    
    map_dataset = {
        "rows": rows,
        "cols": cols,
        "num_providers": num_providers,
        "penalty_cost": penalty_cost,
        "antenna_slot_cost": antenna_slot_cost,
        "banned_zones": banned_zones,
        "forest_zones": forest_zones,
        "building_zones": building_zones
    }
    
    with open(filename, 'w') as json_file:
        json.dump(map_dataset, json_file, indent=4)
        
    print("=" * 60)
    print(f" SYSTEM CONDUIT SETUP SUCCESSFUL ({rows}x{cols} Map Fact Sheets Compiled)")
    print(f" File Destination Path: '{os.path.abspath(filename)}'")
    print("=" * 60)
    
    for r in range(rows):
        row_str = []
        for c in range(cols):
            idx = r * cols + c
            if idx in banned_zones:    row_str.append(" M ")
            elif idx in forest_zones:  row_str.append(" F ")
            elif idx in building_zones: row_str.append(" B ")
            else:                      row_str.append(" . ")
        print(" ".join(row_str))
    print("=" * 60)

if __name__ == '__main__':
    generate_and_save_map(rows=6, cols=6)