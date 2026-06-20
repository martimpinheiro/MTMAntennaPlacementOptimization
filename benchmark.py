"""
Benchmark runner — runs both solvers on the same instances and compares results.

For each (grid size, seed) the script generates a map, runs OR-Tools and SICStus
with a timeout, and records time, cost, coverage, and whether both solvers agree.

Results are written to benchmark_results.csv.

Usage:
    export SICSTUS_PATH=/path/to/sicstus/bin/sicstus
    python benchmark.py
"""

import contextlib
import csv
import io
import os
import shutil
import subprocess
import sys
import time

ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
SICSTUS_DIR = os.path.join(ROOT_DIR, 'sicstus')

sys.path.insert(0, ROOT_DIR)
from map_generator import generate_and_save_map
from sicstus.preprocessor import generate_prolog_facts

# Configuration
GRID_SIZES    = [4, 5, 6, 7, 8, 12, 16, 32, 64]
SEEDS         = [42]
OR_TIMEOUT_S  = 60
SIC_TIMEOUT_S = 60
CSV_FILE      = os.path.join(ROOT_DIR, 'benchmark_results.csv')

PROLOG_GOAL = (
    "run_optimization(Cost, Coverage), "
    "format('RESULT:~w,~w~n', [Cost, Coverage]), halt."
)


def find_sicstus():
    """Locate the SICStus binary via SICSTUS_PATH environment variable."""
    path = os.environ.get('SICSTUS_PATH')
    if path and shutil.which(path):
        return path
    sys.exit(
        "Error: SICSTUS_PATH is not set or the binary was not found.\n"
        "Set it to the full path of the sicstus executable, e.g.:\n"
        "  export SICSTUS_PATH=/path/to/sicstus/bin/sicstus"
    )


def parse_result(stdout):
    for line in stdout.splitlines():
        if line.startswith('RESULT:'):
            cost, cov = line[7:].split(',')
            return {'cost': int(cost), 'coverage_pct': int(cov)}
    return None


def run_ortools(timeout):
    start = time.time()
    proc = subprocess.Popen(
        [sys.executable, os.path.join('ortools', 'optimizer.py'),
         '--benchmark', '--timeout', str(timeout)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=ROOT_DIR,
    )
    try:
        stdout, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return None, (time.time() - start) * 1000
    return parse_result(stdout), (time.time() - start) * 1000


def run_sicstus(sicstus_bin, timeout):
    start = time.time()
    proc = subprocess.Popen(
        [sicstus_bin, '-f', '-l', 'optimizer.pl', '--goal', PROLOG_GOAL],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=SICSTUS_DIR,
    )
    try:
        stdout, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return None, (time.time() - start) * 1000
    return parse_result(stdout), (time.time() - start) * 1000


def run_benchmarks(sicstus_bin):
    total_runs = len(GRID_SIZES) * len(SEEDS)
    print(f"Running {total_runs} benchmark instances "
          f"({len(GRID_SIZES)} grid sizes x {len(SEEDS)} seeds, {OR_TIMEOUT_S}s timeout)")
    print(f"Output -> {CSV_FILE}\n")

    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Grid_Size', 'Cells', 'Seed',
            'OR_Time_MS', 'OR_Cost', 'OR_Coverage_Pct',
            'SIC_Time_MS', 'SIC_Cost', 'SIC_Coverage_Pct',
            'Costs_Match',
        ])

        for size in GRID_SIZES:
            for seed in SEEDS:
                print(f"[{size}x{size}  seed={seed}]")

                with contextlib.redirect_stdout(io.StringIO()):
                    generate_and_save_map(rows=size, cols=size, seed=seed)
                    generate_prolog_facts()

                print(f"  OR-Tools ...", end='', flush=True)
                or_result, or_ms = run_ortools(OR_TIMEOUT_S)
                or_label = f"{or_result['cost']} EUR" if or_result else 'TIMEOUT'
                print(f"  {or_ms:8.1f} ms   {or_label}")

                print(f"  SICStus  ...", end='', flush=True)
                sic_result, sic_ms = run_sicstus(sicstus_bin, SIC_TIMEOUT_S)
                sic_label = f"{sic_result['cost']} EUR" if sic_result else 'TIMEOUT'
                print(f"  {sic_ms:8.1f} ms   {sic_label}")

                if or_result and sic_result:
                    match = or_result['cost'] == sic_result['cost']
                    print(f"  costs match: {'YES' if match else 'NO - MISMATCH'}")
                    costs_match = match
                else:
                    costs_match = 'N/A'

                writer.writerow([
                    f'{size}x{size}', size * size, seed,
                    round(or_ms, 2),
                    or_result['cost'] if or_result else 'TIMEOUT',
                    or_result['coverage_pct'] if or_result else 'TIMEOUT',
                    round(sic_ms, 2),
                    sic_result['cost'] if sic_result else 'TIMEOUT',
                    sic_result['coverage_pct'] if sic_result else 'TIMEOUT',
                    costs_match,
                ])
                f.flush()
                print()

    print(f"Done. Results saved to {CSV_FILE}")


if __name__ == '__main__':
    run_benchmarks(find_sicstus())
