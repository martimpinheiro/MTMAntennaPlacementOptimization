# Ideas & Future Work

## 1. Improve SICStus search heuristics

The current labeling call uses no heuristics: `labeling([minimize(GlobalCost)], AllVars)`. Adding `ff` (first-fail) is a one-line change that picks the variable with the smallest remaining domain at each step, surfacing conflicts earlier and reducing backtracking. This could make SICStus competitive on 6×6 grids. Re-running the benchmark before and after would give a concrete, quantified demonstration of why variable selection matters — directly relevant to the course topic.

```prolog
labeling([ff, minimize(GlobalCost)], AllVars)
```

Other strategies worth trying: `ffc` (first-fail with ties broken by most-constrained), `min`/`max` (value ordering), `bisect` (domain bisection instead of enumeration).

## 2. Symmetry breaking

P1 and P2 have identical coverage radii, so any solution with their antenna placements swapped is equally valid at the same cost. Without symmetry breaking the solver explores both variants, doubling the work for that part of the tree. A simple lexicographic constraint forces a canonical ordering between the two antenna lists:

```prolog
lex_chain([P1, P2])   % P1 <= P2 lexicographically
```

This eliminates the symmetric half of the search space entirely. Measuring the speedup relative to idea 1 would show the additive effect of combining heuristics and symmetry breaking.

## 3. Grid visualization

A matplotlib plot of the solution: terrain as background colours (white/green/grey/black for plains/forest/building/mountain), tower markers sized by tenant count, coverage radius overlays per provider. Would make results immediately presentable for the report and useful for spot-checking correctness on specific instances.

## 4. Extended OR-Tools scalability benchmarks

CP-SAT handles all tested sizes (up to 8×8) trivially. Running it on 10×10, 12×12, and 15×15 grids would show where it too starts to slow down and give the benchmark section a proper scalability curve rather than a flat line. It also provides a meaningful upper bound on what grid size is practically solvable.

## 5. Mathematical formalization

Write the CSP/ILP formulation with proper notation for the report submission: decision variables, domains, objective function, and each constraint as an equation. Everything is already in the code — this is transcription, but it is typically required for academic CP submissions and makes the model easier to reason about formally.
