# benchmark_runner.py
import subprocess
import time
import csv
import os
from preprocessor import generate_prolog_facts

def create_synthetic_map(size):
    """ Generates clean checkerboard synthetic layouts of any grid resolution """
    map_rows = []
    for r in range(size):
        row = []
        for c in range(size):
            if r == size // 2 and c > 0 and c < size - 1:
                row.append("X") # Flat line barrier obstacle split
            elif (r + c) % 5 == 0:
                row.append("B") # Buildings blocks scattered
            else:
                row.append(".")
        map_rows.append(" ".join(row))
    return "\n".join(map_rows)
#"C:\Program Files\SICStus Prolog VC16 4.10.1\bin\sicstus.exe"
def run_sicstus_benchmark():
    csv_file = "solver_benchmarks.csv"
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Grid_Size", "Total_Cells", "Execution_Time_MS", "Network_Cost", "Coverage_QoS"])

    # Path to your actual executable (Update this to point to your version)
    sicstus_path = r"C:\Program Files\SICStus Prolog VC16 4.10.1\bin\sicstus.exe"

    for size in range(4, 9):
        total_cells = size * size
        print(f"\n--- Benchmarking Grid Resolution: {size}x{size} ({total_cells} cells) ---")
        
        synthetic_map = create_synthetic_map(size)
        generate_prolog_facts(synthetic_map, {0: 4, 1: 3, 2: 2, 3: 1})

        # Non-interactive inline goal string for SICStus
        prolog_goal = "run_optimization(Cost, Coverage), format('RESULT:~w,~w', [Cost, Coverage]), halt."
        
        start_time = time.time()
        
        # FIXED PIPELINE: Added '--noinitialization' to skip the interactive top-level console prompt
        process = subprocess.Popen(
            [
                sicstus_path, 
                "--noinitialization", 
                "-l", "solver_engine.pl", 
                "--goal", prolog_goal
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Add a 10-second safety timeout so it never hangs indefinitely
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            print(f" [Timeout] {size}x{size} engine calculation ran too long.")
            continue

        elapsed_time_ms = (time.time() - start_time) * 1000

        cost, coverage = "N/A", "N/A"
        for line in stdout.splitlines():
            if "RESULT:" in line:
                metrics = line.replace("RESULT:", "").strip().split(",")
                cost, coverage = metrics[0], metrics[1]

        print(f"Time Taken: {elapsed_time_ms:.2f} ms | Optimal Cost: {cost} EUR | Coverage: {coverage}")
        
        with open(csv_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([f"{size}x{size}", total_cells, round(elapsed_time_ms, 2), cost, f"{coverage}%"])

    print(f"\nAll iterations complete! Logs exported to '{csv_file}'.")

if __name__ == "__main__":
    run_sicstus_benchmark()