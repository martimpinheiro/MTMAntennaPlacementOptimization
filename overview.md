# Solver Comparison Overview

Both solvers implement the same model on the same data. Benchmark results show OR-Tools completing all grid sizes in under 500ms while SICStus times out at 6×6 and above. This gap comes from several compounding factors.

## 1. Naive labeling order

The SICStus solver uses `labeling([minimize(GlobalCost)], AllVars)` with no variable selection heuristics. Variables are labeled in the order they appear in the list: all tower variables first, then all antenna variables per provider, then all slacks. This is a poor ordering — the solver commits to a complete tower layout before seeing the coverage consequences, discovers conflicts deep in the tree, and has to backtrack all the way to tower decisions. A simple improvement would be the `ff` (first-fail) heuristic, which at each step picks the variable with the smallest remaining domain, surfacing conflicts earlier.

## 2. Branch-and-bound with weak bounds

`minimize(GlobalCost)` in SICStus runs branch-and-bound: find a feasible solution, record its cost as an upper bound, then continue searching for something strictly cheaper. The quality of pruning depends on how tight the lower bound is at each search node. CLP(FD) derives lower bounds purely from constraint propagation, which is often loose. OR-Tools CP-SAT additionally runs a linear programming relaxation at each node to compute tight lower bounds on the objective, allowing it to prune entire subtrees early with a proof that they cannot improve on the current best.

## 3. CLP(FD) propagation vs CDCL in CP-SAT

CLP(FD) uses arc consistency: when a variable's domain shrinks, it re-checks connected constraints and propagates reductions transitively. This is sound but shallow — it cannot reason about *combinations* of decisions that lead to contradictions. OR-Tools CP-SAT is a hybrid SAT solver that encodes everything as boolean clauses and uses Conflict-Driven Clause Learning (CDCL). When CP-SAT hits a contradiction, it analyses the reason, derives a new "no-good" clause, and adds it permanently to the constraint store. That clause then prunes entire regions of the search space that share the same root cause, even in completely different branches of the tree. CLP(FD) backtracks and forgets; CP-SAT learns and remembers.

## 4. Symmetry between providers

P1 and P2 have identical coverage radii. Any solution with their antenna placements swapped is equally valid with the same cost. Without symmetry breaking, the solver explores both symmetric variants, effectively doubling the work for a large portion of the search tree. OR-Tools handles this internally; the SICStus solver does not add any symmetry-breaking constraints.

## 5. OR-Tools timing is mostly overhead

The ~330–500ms OR-Tools figures are dominated by Python startup, JSON loading, model construction, and precomputing coverage sources — not solve time. The actual CP-SAT search for these grid sizes is likely single-digit milliseconds. SICStus at 4×4 (~370ms) is comparable once Prolog startup and library loading are accounted for. The divergence becomes visible at 5×5 where CLP(FD) search time starts to dominate (8–14 seconds), and the solver cannot complete 6×6 within 60 seconds.

## Summary

OR-Tools and SICStus are not solving the same search problem in practice, even though they encode the same model. CP-SAT brings learned clauses, LP-derived bounds, and portfolio heuristics to bear on each node. CLP(FD)'s strength is declarative expressiveness and correctness guarantees; raw performance on combinatorial optimisation without careful manual search tuning is where it falls short.
