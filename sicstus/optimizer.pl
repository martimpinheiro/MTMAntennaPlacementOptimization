%% optimizer.pl
:- use_module(library(clpfd)).
:- use_module(library(lists)).
:- use_module(library(between)).

:- ensure_loaded('map_data.pl').

% =====================================================================
% COVERAGE GEOMETRY  (mirrors OR-Tools get_covered_cells)
% =====================================================================
manhattan_covers(K, Src, Tgt) :-
    grid_dimensions(_, _, Cols),
    provider_radius(K, R),
    SrcRow is Src // Cols, SrcCol is Src mod Cols,
    TgtRow is Tgt // Cols, TgtCol is Tgt mod Cols,
    Dist is abs(SrcRow - TgtRow) + abs(SrcCol - TgtCol),
    Dist =< R.

% =====================================================================
% TERRAIN COST  (mirrors OR-Tools get_tower_base_cost)
% =====================================================================
tower_base_cost(I, 2500) :- is_building(I), !.
tower_base_cost(I, 1500) :- is_forest(I), !.
tower_base_cost(_, 1000).

build_base_costs(GridSize, Costs) :-
    GridSizeM1 is GridSize - 1,
    findall(C, (between(0, GridSizeM1, I), tower_base_cost(I, C)), Costs).

% =====================================================================
% 1. MAIN ENTRY POINT
% =====================================================================
run_optimization(GlobalCost, CoveragePercentage) :-
    grid_dimensions(GridSize, _, _),
    AntennaCost = 100,
    PenaltyCost = 800,

    length(T,  GridSize), domain(T,  0, 1),
    length(P0, GridSize), domain(P0, 0, 1),
    length(P1, GridSize), domain(P1, 0, 1),
    length(P2, GridSize), domain(P2, 0, 1),
    length(P3, GridSize), domain(P3, 0, 1),

    length(S0, GridSize), domain(S0, 0, 1),
    length(S1, GridSize), domain(S1, 0, 1),
    length(S2, GridSize), domain(S2, 0, 1),
    length(S3, GridSize), domain(S3, 0, 1),

    % STEP 1: Topology and coverage constraints
    constrain_topology(T, P0, P1, P2, P3, 0),
    constrain_coverage([P0, P1, P2, P3], [S0, S1, S2, S3], 0, 4, GridSize),

    % STEP 2: Build GlobalCost as a CLP(FD) variable for branch-and-bound
    build_base_costs(GridSize, BaseCosts),
    scalar_product(BaseCosts, T, #=, TowerCostVar),

    append([P0, P1, P2, P3], AllAnts),
    length(AllAnts, NAnts), length(AntCoeffs, NAnts),
    maplist(=(AntennaCost), AntCoeffs),
    scalar_product(AntCoeffs, AllAnts, #=, AntCostVar),

    append([S0, S1, S2, S3], AllSlacks),
    length(AllSlacks, NSlacks), length(PenCoeffs, NSlacks),
    maplist(=(PenaltyCost), PenCoeffs),
    scalar_product(PenCoeffs, AllSlacks, #=, PenaltyCostVar),

    GlobalCost #= TowerCostVar + AntCostVar + PenaltyCostVar,

    % STEP 3: Optimize via branch-and-bound labeling
    append([T, P0, P1, P2, P3, S0, S1, S2, S3], AllVars),
    labeling([ff, minimize(GlobalCost)], AllVars),

    % STEP 4: Compute coverage percentage (all variables are now ground)
    sumlist(S0, D0), sumlist(S1, D1), sumlist(S2, D2), sumlist(S3, D3),
    TotalDrops is D0 + D1 + D2 + D3,
    GridSizeM1 is GridSize - 1,
    findall(I, (between(0, GridSizeM1, I), \+ is_banned(I)), Coverable),
    length(Coverable, NumCoverable),
    TotalPoss is NumCoverable * 4,
    CoveragePercentage is ((TotalPoss - TotalDrops) * 100) // TotalPoss.


% =====================================================================
% 2. TOPOLOGY CONSTRAINTS
% =====================================================================
constrain_topology([], [], [], [], [], _) :- !.
constrain_topology([Tower|Ts], [Ant0|A0s], [Ant1|A1s], [Ant2|A2s], [Ant3|A3s], I) :-
    (is_banned(I) -> Tower #= 0 ; true),

    Ant0 #=< Tower,
    Ant1 #=< Tower,
    Ant2 #=< Tower,
    Ant3 #=< Tower,

    sum([Ant0, Ant1, Ant2, Ant3], #=<, 4),

    NextI is I + 1,
    constrain_topology(Ts, A0s, A1s, A2s, A3s, NextI).


% =====================================================================
% 3. COVERAGE CONSTRAINTS
% =====================================================================
constrain_coverage(_, _, NumProv, NumProv, _) :- !.
constrain_coverage(Antennas, Slacks, K, NumProv, GridSize) :-
    nth0(K, Antennas, P_k),
    nth0(K, Slacks,   S_k),
    loop_target_cells(P_k, S_k, K, 0, GridSize),
    NextK is K + 1,
    constrain_coverage(Antennas, Slacks, NextK, NumProv, GridSize).

loop_target_cells(_, [], _, _, _) :- !.
loop_target_cells(P_k, [SlackVar|RestSlacks], K, Tgt, GridSize) :-
    (is_banned(Tgt) ->
        SlackVar #= 0
    ;
        GridSizeM1 is GridSize - 1,
        findall(Src, (between(0, GridSizeM1, Src),
                      \+ is_banned(Src),
                      manhattan_covers(K, Src, Tgt)),
                ValidSources),
        extract_domain_vars(ValidSources, P_k, CoverageVars),
        (CoverageVars == [] ->
            SlackVar #= 1
        ;
            sum([SlackVar|CoverageVars], #>=, 1)
        )
    ),
    NextTgt is Tgt + 1,
    loop_target_cells(P_k, RestSlacks, K, NextTgt, GridSize).


% =====================================================================
% 4. UTILITY
% =====================================================================
extract_domain_vars([], _, []).
extract_domain_vars([Idx|Idxs], List, [Var|Vars]) :-
    PrologIdx is Idx + 1,
    element(PrologIdx, List, Var),
    extract_domain_vars(Idxs, List, Vars).
