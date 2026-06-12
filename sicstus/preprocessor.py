import json
import os

def generate_prolog_facts(map_json_path=None, output_path=None):
    """Translates map_data.json into minimal Prolog facts for solver_engine.pl."""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if map_json_path is None:
        map_json_path = os.path.join(script_dir, '..', 'map_data.json')
    if output_path is None:
        output_path = os.path.join(script_dir, 'map_data.pl')

    with open(map_json_path) as f:
        data = json.load(f)

    rows           = data['rows']
    cols           = data['cols']
    grid_size      = rows * cols
    provider_radii = data.get('provider_radii', [0, 1, 1, 2])
    banned_zones   = data.get('banned_zones', [])
    forest_zones   = data.get('forest_zones', [])
    building_zones = data.get('building_zones', [])

    with open(output_path, 'w') as f:
        f.write('%% Auto-generated from map_data.json — do not edit by hand\n\n')

        f.write(f'grid_dimensions({grid_size}, {rows}, {cols}).\n\n')

        for k, r in enumerate(provider_radii):
            f.write(f'provider_radius({k}, {r}).\n')
        f.write('\n')

        for idx in banned_zones:
            f.write(f'is_banned({idx}).\n')
        f.write('\n')

        for idx in forest_zones:
            f.write(f'is_forest({idx}).\n')
        f.write('\n')

        for idx in building_zones:
            f.write(f'is_building({idx}).\n')

    print(f'Generated {output_path} ({grid_size} cells, {rows}x{cols})')

if __name__ == '__main__':
    generate_prolog_facts()
