# Multi-Tenant Mobile Antenna Placement Optimization

**PLR @ FEUP 2026** — Martim Pinheiro (up20509641) · Adam Oprchal (up202512712)

## Problem

Given a grid map with varied terrain (plains, forests, buildings, mountains),
place cell towers and assign antennas to four telecom providers to minimise
total infrastructure cost while maximising signal coverage. Each provider
operates on a different frequency band with a different coverage radius. Towers
can be shared by up to four tenants. Cells left uncovered incur a financial
penalty (soft constraint) rather than being forbidden.

| Provider | Band | Radius |
|----------|------|--------|
| P0 | High-band / 5G mmWave | 0 (own cell only) |
| P1 | Mid-band / 4G-5G | 1 |
| P2 | Mid-band / 4G-5G | 1 |
| P3 | Low-band / Macro LTE | 2 |

| Terrain | Tower cost |
|---------|-----------|
| Plains | €1 000 |
| Forest | €1 500 |
| Building | €2 500 |
| Mountain | banned — no tower allowed |

Each antenna slot costs an additional €100. Each uncovered cell costs €800 per provider.

## Solvers

The same CSOP model is implemented in two constraint programming solvers:

- **OR-Tools CP-SAT** (`ortools/optimizer.py`) — Google's hybrid SAT/CP solver (CDCL + LP relaxation)
- **SICStus Prolog CLP(FD)** (`sicstus/optimizer.pl`) — branch-and-bound over finite domains with first-fail heuristic

## Project Structure

```
map_generator.py          random map generator → map_data.json
benchmark.py              benchmark runner (both solvers) → benchmark_results.csv
ortools/
└── optimizer.py          OR-Tools CP-SAT solver
sicstus/
├── preprocessor.py       translates map_data.json → map_data.pl
├── optimizer.pl          SICStus CLP(FD) solver
└── map_data.pl           auto-generated Prolog facts (do not edit by hand)
benchmark_results.csv     pre-computed benchmark results (seed 42, sizes 4–64)
```

## Requirements

- Python 3.10+
- [OR-Tools](https://developers.google.com/optimization/install): `pip install ortools`
- [SICStus Prolog 4.x](https://sicstus.sics.se/) with the path set in `SICSTUS_PATH`

> **Windows PowerShell note:** replace `export VAR=value` with `$env:VAR = "value"`.

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd MTMAntennaPlacementOptimization

# 2. Install the Python dependency
pip install ortools

# 3. Point to your SICStus binary (skip if you only want to run OR-Tools)
export SICSTUS_PATH=/path/to/sicstus/bin/sicstus   # Linux / macOS / WSL
$env:SICSTUS_PATH = "C:\path\to\sicstus.exe"        # Windows PowerShell
```

---

## Usage

### 1 — Generate a map

```bash
python map_generator.py                    # random 6×6 map (default)

# Custom size and reproducible seed:
python -c "
from map_generator import generate_and_save_map
generate_and_save_map(rows=8, cols=8, seed=42)
"
```

The map is saved to `map_data.json` and printed as an ASCII grid.

### 2 — Run the OR-Tools solver

```bash
python ortools/optimizer.py
```

Prints the optimal cost, per-provider antenna counts, coverage percentages,
and an ASCII grid showing tower placements.

### 3 — Run the SICStus solver

```bash
# Step 3a — translate the JSON map into Prolog facts
python sicstus/preprocessor.py

# Step 3b — run the Prolog solver
sicstus -f -l sicstus/optimizer.pl --goal \
  "run_optimization(Cost, Cov), format('Cost: ~w  Coverage: ~w%~n', [Cost, Cov]), halt."
```

### 4 — Run the full benchmark (both solvers, all grid sizes)

```bash
python benchmark.py
# Results written to benchmark_results.csv
```

The benchmark iterates over grid sizes 4×4 → 64×64 with a 60-second timeout
per solver and records timing, cost, coverage, and cost equality in CSV format.

---

## Testing

### Quick correctness check (OR-Tools only, no SICStus needed)

Generate a small reproducible map and verify the solver returns a known-good cost:

```bash
python -c "
from map_generator import generate_and_save_map
generate_and_save_map(rows=4, cols=4, seed=42)
"
python ortools/optimizer.py
# Expected optimal cost: €13 600
```

### Cross-solver equivalence check

The strongest correctness test is running both solvers on the same map and
confirming they find the same optimal cost. The benchmark runner does this
automatically and prints `costs match: YES` for each completed instance.

For a single manual check:

```bash
# 1. Generate a map
python -c "
from map_generator import generate_and_save_map
generate_and_save_map(rows=5, cols=5, seed=42)
"

# 2. Run OR-Tools
python ortools/optimizer.py

# 3. Run SICStus
python sicstus/preprocessor.py
sicstus -f -l sicstus/optimizer.pl --goal \
  "run_optimization(Cost, Cov), format('Cost: ~w  Coverage: ~w%~n', [Cost, Cov]), halt."

# Both solvers should report the same cost (€22 500 for this instance).
```

### Verifying benchmark results

The pre-computed results are in `benchmark_results.csv`. The `Costs_Match`
column is `True` for all instances where both solvers completed, confirming
model equivalence. To reproduce:

```bash
python benchmark.py    # requires SICSTUS_PATH to be set
```
