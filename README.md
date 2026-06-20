# MultiTenant Mobile Antenna Placement Optimization

**PLR@FEUP 2026** — Martim Pinheiro (up20509641) · Adam Oprchal (up202512712)

## Problem

Given a grid map with varied terrain (plains, forests, buildings, mountains), place cell towers and assign antennas to four telecom providers to minimise total infrastructure cost while maximising signal coverage. Each provider operates on a different frequency band with a different coverage radius. Towers can be shared by up to four tenants. Cells left uncovered incur a financial penalty instead of being a hard constraint.

The four providers and their Manhattan coverage radii:

| Provider | Band | Radius |
|----------|------|--------|
| P0 | High-band / 5G mmWave | 0 (own cell only) |
| P1 | Mid-band / 4G-5G | 1 |
| P2 | Mid-band / 4G-5G | 1 |
| P3 | Low-band / Macro LTE | 2 |

Terrain affects tower construction cost:

| Terrain | Cost |
|---------|------|
| Plains | €1 000 |
| Forest | €1 500 |
| Building | €2 500 |
| Mountain | banned (no tower allowed) |

Each antenna slot costs an additional €100. Each uncovered cell costs €800 per provider.

## Solvers

The same model is implemented in two constraint programming solvers for comparison:

- **OR-Tools CP-SAT** (`ortools/optimizer.py`) — Google's hybrid SAT/CP solver
- **SICStus Prolog CLP(FD)** (`sicstus/optimizer.pl`) — branch-and-bound over finite domains

## Project Structure

```
map_generator.py        shared map generator  → map_data.json
benchmark.py            benchmark runner (both solvers, outputs benchmark_results.csv)
ortools/
└── optimizer.py        OR-Tools solver
sicstus/
├── preprocessor.py     translates map_data.json → map_data.pl
├── optimizer.pl        SICStus CLP(FD) solver
└── map_data.pl         auto-generated Prolog facts (do not edit)
```

## Requirements

- Python 3.10+
- [OR-Tools](https://developers.google.com/optimization/install): `pip install ortools`
- [SICStus Prolog 4.x](https://sicstus.sics.se/) — set `SICSTUS_PATH` to the binary

## Running

> **Note:** The commands below use `export` and Bash syntax. They work on Linux, macOS, and Windows Subsystem for Linux (WSL). On native Windows (PowerShell/cmd), use `$env:SICSTUS_PATH = "..."` (PowerShell) or `set SICSTUS_PATH=...` (cmd) instead of `export`.

**Generate a map:**
```bash
python map_generator.py                        # random 6x6
python -c "from map_generator import generate_and_save_map; generate_and_save_map(rows=8, cols=8, seed=42)"
```

**Run the OR-Tools solver:**
```bash
python ortools/optimizer.py
```

**Run the SICStus solver:**
```bash
python sicstus/preprocessor.py                 # generate map_data.pl from map_data.json
export SICSTUS_PATH=/path/to/sicstus/bin/sicstus
sicstus -f -l sicstus/optimizer.pl --goal \
  "run_optimization(Cost, Cov), format('Cost: ~w  Coverage: ~w%~n', [Cost, Cov]), halt."
```

**Run benchmarks (both solvers, all grid sizes):**
```bash
export SICSTUS_PATH=/path/to/sicstus/bin/sicstus
python benchmark.py
# results written to benchmark_results.csv
```
