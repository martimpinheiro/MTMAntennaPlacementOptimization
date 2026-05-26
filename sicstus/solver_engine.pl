%% solver_engine.pl
:- use_module(library(clpfd)).
:- use_module(library(lists)).

% Load the pre-processed map facts natively
:- ensure_loaded('map_data.pl').

% =====================================================================
% 1. MAIN ENTRY POINT
% =====================================================================
run_optimization(GlobalCost, CoveragePercentage) :-
    grid_dimensions(GridSize, _, _),
    PenaltyCost = 800,

    % Setup structural domain arrays matching the grid layout size
    length(T, GridSize),   domain(T, 0, 1),
    length(P0, GridSize),  domain(P0, 0, 1),
    length(P1, GridSize),  domain(P1, 0, 1),
    length(P2, GridSize),  domain(P2, 0, 1),
    length(P3, GridSize),  domain(P3, 0, 1),
    
    length(S0, GridSize),  domain(S0, 0, 1),
    length(S1, GridSize),  domain(S1, 0, 1),
    length(S2, GridSize),  domain(S2, 0, 1),
    length(S3, GridSize),  domain(S3, 0, 1),

    % STEP 1: Topology Rules
    constrain_topology(T, P0, P1, P2, P3, 0),

    % STEP 2: Coverage Routing Bounds
    constrain_coverage([P0, P1, P2, P3], [S0, S1, S2, S3], 0, 4, GridSize),

    % STEP 3: Search Strategy Allocation (Instantiates variables to raw integers)
    append([T, P0, P1, P2, P3, S0, S1, S2, S3], AllVars),
    labeling([], AllVars),

    % STEP 4: Post-Solution Math (Using plain Prolog logic, no CLPFD predicates)
    evaluate_hardware_costs(T, P0, P1, P2, P3, HardwareCost),
    
    sum_list(S0, D0), sum_list(S1, D1), sum_list(S2, D2), sum_list(S3, D3),
    TotalDrops is D0 + D1 + D2 + D3,
    PenaltyTotal is TotalDrops * PenaltyCost,
    
    GlobalCost is HardwareCost + PenaltyTotal,
    TotalPoss is GridSize * 4,
    CoveragePercentage is ((TotalPoss - TotalDrops) * 100) // TotalPoss.


% =====================================================================
% 2. TOPOLOGY STEP
% =====================================================================
constrain_topology([], [], [], [], [], _) :- !.
constrain_topology([Tower|Ts], [Ant0|A0s], [Ant1|A1s], [Ant2|A2s], [Ant3|A3s], I) :-
    %(is_banned(I) -> Tower #= 0 ; true),

    Ant0 #<= Tower, 
    Ant1 #<= Tower, 
    Ant2 #<= Tower, 
    Ant3 #<= Tower,
    
    sum([Ant0, Ant1, Ant2, Ant3], #<=, 4),

    NextI is I + 1,
    constrain_topology(Ts, A0s, A1s, A2s, A3s, NextI).


% =====================================================================
% =====================================================================
% 3. MULTI-TENANT COVERAGE GEOMETRY (Resilient List-Walking Version)
% =====================================================================
constrain_coverage(_, _, NumProv, NumProv, _) :- !.
constrain_coverage(Antennas, Slacks, K, NumProv, GridSize) :-
    nth0(K, Antennas, P_k),
    nth0(K, Slacks, S_k),
    % Pass the entire slack list directly to walk it sequentially
    loop_target_cells(P_k, S_k, K, 0, GridSize),
    NextK is K + 1,
    constrain_coverage(Antennas, Slacks, NextK, NumProv, GridSize).

loop_target_cells(_, [], _, _, _) :- !. % Base case: slack list exhausted
loop_target_cells(P_k, [SlackVar|RestSlacks], K, Tgt, GridSize) :-
    % Collect all potential source indices for this target cell
    findall(Src, can_cover(K, Src, Tgt), ValidSources),
    
    % Safely extract the corresponding antenna domain variables
    extract_domain_variables(ValidSources, P_k, CoverageVars),
    
    % If there are physically no paths to cover this cell, lock the drop-slack to 1.
    % Otherwise, require either an active antenna OR a drop dropout.
    (CoverageVars == [] ->
        SlackVar #= 1
    ;
        sum([SlackVar|CoverageVars], #>=, 1)
    ),
    
    NextTgt is Tgt + 1,
    loop_target_cells(P_k, RestSlacks, K, NextTgt, GridSize).
% =====================================================================
% 4. POST-LABELING EVALUATION (Pure List Math)
% =====================================================================
evaluate_hardware_costs([], [], [], [], [], 0) :- !.
evaluate_hardware_costs([TowerVal|Ts], [A0|A0s], [A1|A1s], [A2|A2s], [A3|A3s], TotalCost) :-
    ActiveCount is A0 + A1 + A2 + A3,
    (TowerVal == 1 -> 
        CellCost is 1000 + (ActiveCount * 100)
    ; 
        CellCost is 0
    ),
    evaluate_hardware_costs(Ts, A0s, A1s, A2s, A3s, RemainingCost),
    TotalCost is CellCost + RemainingCost.


% =====================================================================
% 5. UTILITY DATA EXTRACTORS
% =====================================================================
extract_domain_variables([], _, []).
extract_domain_variables([Idx|Idxs], TargetList, [Var|Vars]) :-
    PrologIdx is Idx + 1,
    length(TargetList, TotalLen),
    (PrologIdx <= TotalLen ->
        element(PrologIdx, TargetList, Var)
    ;
        Var #= 0
    ),
    extract_domain_variables(Idxs, TargetList, Vars).