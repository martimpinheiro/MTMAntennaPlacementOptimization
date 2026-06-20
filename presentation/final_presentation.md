---
title: "Multi-Tenant Mobile Antenna Placement Optimization"
subtitle: "PLR — Programação em Lógica com Restrições · FEUP 2026"
author:
  - "Martim Pinheiro (up20509641)"
  - "Adam Oprchal (up202512712)"
date: "June 2026"
institute: "Faculdade de Engenharia da Universidade do Porto"
theme: "Madrid"
colortheme: "dolphin"
fonttheme: "professionalfonts"
aspectratio: 169
header-includes:
  - \usepackage{booktabs}
  - \usepackage{array}
  - \usepackage{tikz}
  - \usetikzlibrary{positioning,shapes,arrows}
  - \usepackage{amsmath}
  - \setbeamertemplate{navigation symbols}{}
  - \AtBeginSection[]{\begin{frame}<beamer>{Outline}\tableofcontents[currentsection]\end{frame}}
  - |
    \setbeamertemplate{footline}{%
      \leavevmode%
      \hbox{%
        \begin{beamercolorbox}[wd=.44\paperwidth,ht=2.25ex,dp=1ex,center]{author in head/foot}%
          \usebeamerfont{author in head/foot}%
          Martim Pinheiro (up20509641)\enspace\ensuremath{\cdot}\enspace Adam Oprchal (up202512712)%
        \end{beamercolorbox}%
        \begin{beamercolorbox}[wd=.44\paperwidth,ht=2.25ex,dp=1ex,center]{title in head/foot}%
          \usebeamerfont{title in head/foot}\inserttitle%
        \end{beamercolorbox}%
        \begin{beamercolorbox}[wd=.12\paperwidth,ht=2.25ex,dp=1ex,right]{date in head/foot}%
          \usebeamerfont{date in head/foot}%
          \insertframenumber\,/\,\inserttotalframenumber\hspace*{2ex}%
        \end{beamercolorbox}%
      }%
      \vskip0pt%
    }
---

# Problem Description

## Problem Overview

**Multi-Tenant Mobile Antenna Placement Optimization**

\vspace{0.3em}

Given a **grid map** with varied terrain, we must:

\begin{itemize}
  \item Place \textbf{cell towers} on valid terrain cells
  \item Assign \textbf{antennas} from 4 telecom providers to towers
  \item \textbf{Minimise total infrastructure cost} while maximising signal coverage
\end{itemize}

\vspace{0.5em}

\begin{block}{Key Characteristics}
\begin{itemize}
  \item Towers can be \textbf{shared} by up to 4 tenants (multi-tenant)
  \item Each provider has a different \textbf{frequency band} and \textbf{coverage radius}
  \item Uncovered cells incur a \textbf{financial penalty} (soft constraint)
\end{itemize}
\end{block}

## Terrain Types

\begin{columns}[onlytextwidth]
\begin{column}{0.5\textwidth}
\begin{table}
\centering
\begin{tabular}{lrc}
\toprule
\textbf{Terrain} & \textbf{Tower Cost} & \textbf{Symbol} \\
\midrule
Plains    & €1\,000 & \texttt{.} \\
Forest    & €1\,500 & \texttt{F} \\
Building  & €2\,500 & \texttt{B} \\
Mountain  & \textit{Banned}  & \texttt{M} \\
\bottomrule
\end{tabular}
\caption{Terrain costs}
\end{table}
\end{column}
\begin{column}{0.5\textwidth}
\begin{block}{Additional Costs}
\begin{itemize}
  \item \textbf{Antenna slot}: €100 per antenna
  \item \textbf{Uncovered cell}: €800 per provider
\end{itemize}
\end{block}
\vspace{0.5em}
Penalty makes coverage a \textbf{soft constraint}---the solver can choose not to cover a remote cell if it is cheaper than building a tower for it.
\end{column}
\end{columns}

## Provider Frequency Bands

\begin{table}
\centering
\begin{tabular}{clcl}
\toprule
\textbf{Provider} & \textbf{Band} & \textbf{Manhattan Radius} & \textbf{Characteristics} \\
\midrule
P0 & High-band / 5G mmWave & 0 & Own cell only; high capacity \\
P1 & Mid-band / 4G--5G     & 1 & Adjacent cells; balanced \\
P2 & Mid-band / 4G--5G     & 1 & Adjacent cells; balanced \\
P3 & Low-band / Macro LTE  & 2 & Wide area; legacy coverage \\
\bottomrule
\end{tabular}
\caption{Provider coverage parameters}
\end{table}

\vspace{0.5em}
\begin{alertblock}{Note}
P1 and P2 share the same radius, introducing \textbf{solution symmetry}---any swap of their placements yields an equally valid solution.
\end{alertblock}

# Formal Model

## Decision Variables

Let $N = R \times C$ be the total number of grid cells.

\vspace{0.5em}

\begin{align*}
t_i &\in \{0,1\} && \text{tower built at cell } i,\quad i \in [0, N) \\
a_{k,i} &\in \{0,1\} && \text{provider } k \text{ has antenna at cell } i \\
s_{k,j} &\in \{0,1\} && \text{slack: cell } j \text{ uncovered by provider } k
\end{align*}

\vspace{0.3em}

where $k \in \{0,1,2,3\}$ and $j$ ranges over all non-banned cells.

\vspace{0.5em}

\begin{block}{Coverage Sources}
$\mathrm{cov}(k, j) = \bigl\{ i \in [0,N) \mid \|i - j\|_1 \leq r_k \land i \notin \text{banned} \bigr\}$
\end{block}

## Constraints

**C1 — No tower on mountain:**
$$t_i = 0 \qquad \forall\, i \in \text{banned}$$

**C2 — Antenna requires a tower:**
$$a_{k,i} \leq t_i \qquad \forall\, k,\, \forall\, i$$

**C3 — Multi-tenant capacity (max 4 providers per tower):**
$$\sum_{k=0}^{3} a_{k,i} \leq 4 \qquad \forall\, i$$

**C4 — Coverage or penalty (reified):**
$$\sum_{i \in \mathrm{cov}(k,j)} a_{k,i} + s_{k,j} \geq 1 \qquad \forall\, k,\, \forall\, j \notin \text{banned}$$

## Objective Function

**Minimise total infrastructure cost:**

$$\min \underbrace{\sum_{i} c_i \cdot t_i}_{\text{tower construction}} + \underbrace{100 \cdot \sum_{k,i} a_{k,i}}_{\text{antenna slots}} + \underbrace{800 \cdot \sum_{k,j} s_{k,j}}_{\text{uncoverage penalties}}$$

where $c_i \in \{1000, 1500, 2500\}$ depends on terrain type.

\vspace{0.5em}

\begin{block}{Problem Class}
This is a \textbf{Constraint Satisfaction \& Optimisation Problem (CSOP)} over Boolean finite domains---naturally suited to Constraint Programming.
\end{block}

# Implementation

## OR-Tools CP-SAT

\textbf{Platform:} Google OR-Tools CP-SAT · Python 3

\vspace{0.5em}

\begin{columns}[onlytextwidth]
\begin{column}{0.55\textwidth}
\textbf{Model construction:}
\begin{itemize}
  \item \texttt{NewBoolVar} for every $t_i$, $a_{k,i}$, $s_{k,j}$
  \item Coverage sources precomputed before model building
  \item Linear constraints added with \texttt{model.Add(...)}
  \item Minimisation via \texttt{model.Minimize(...)}
\end{itemize}
\end{column}
\begin{column}{0.45\textwidth}
\begin{exampleblock}{Key snippet}
\footnotesize
\texttt{for (k,tgt), srcs in coverage\_sources:}\\
\quad\texttt{model.Add(}\\
\quad\quad\texttt{sum(ant[k][s]}\\
\quad\quad\texttt{  for s in srcs)}\\
\quad\quad\texttt{+ slack[k][tgt] >= 1)}
\end{exampleblock}
\end{column}
\end{columns}

\vspace{0.4em}

\begin{block}{Solver configuration}
\texttt{CpSolver} with \texttt{max\_time\_in\_seconds} timeout; accepts first OPTIMAL or FEASIBLE status.
\end{block}

## SICStus Prolog CLP(FD)

\textbf{Platform:} SICStus Prolog 4.x · \texttt{library(clpfd)}

\vspace{0.3em}

\begin{columns}[onlytextwidth]
\begin{column}{0.55\textwidth}
\textbf{Declarative model:}
\begin{itemize}
  \item Lists of 0/1 domain variables: \texttt{T}, \texttt{P0--P3}, \texttt{S0--S3}
  \item \texttt{scalar\_product} for cost terms
  \item \texttt{sum(..., \#>=, 1)} for coverage
  \item Branch-and-bound via \texttt{labeling([minimize(GlobalCost)], Vars)}
\end{itemize}
\end{column}
\begin{column}{0.45\textwidth}
\begin{exampleblock}{Key snippet}
\footnotesize
\texttt{sum([Slack|CovVars],}\\
\quad\texttt{\#>=, 1)}\\
\vspace{0.3em}
\texttt{labeling(}\\
\quad\texttt{[minimize(Cost)],}\\
\quad\texttt{AllVars)}
\end{exampleblock}
\end{column}
\end{columns}

\vspace{0.3em}

\begin{alertblock}{Preprocessor}
A Python script (\texttt{preprocessor.py}) translates \texttt{map\_data.json} into Prolog facts (\texttt{map\_data.pl}), keeping a single source of truth for map data across both solvers.
\end{alertblock}

## Architecture

\begin{center}
\begin{tikzpicture}[
  box/.style={draw, rounded corners, minimum width=2.4cm, minimum height=0.7cm, align=center, font=\small},
  arr/.style={->, thick}
]
  \node[box, fill=blue!15]  (gen)  {map\_generator.py};
  \node[box, fill=gray!15, right=1.2cm of gen] (json) {map\_data.json};
  \node[box, fill=green!15, below left=0.9cm and 0.3cm of json] (ort)  {OR-Tools\\optimizer.py};
  \node[box, fill=orange!15, below right=0.9cm and 0.3cm of json] (pre)  {preprocessor.py};
  \node[box, fill=red!15, right=0.5cm of pre] (pl)   {map\_data.pl};
  \node[box, fill=red!15, below=0.6cm of pl]  (sic)  {SICStus\\optimizer.pl};
  \node[box, fill=purple!15, below=1.6cm of json] (bench) {benchmark.py};

  \draw[arr] (gen)  -- (json);
  \draw[arr] (json) -- (ort);
  \draw[arr] (json) -- (pre);
  \draw[arr] (pre)  -- (pl);
  \draw[arr] (pl)   -- (sic);
  \draw[arr] (json) -- (bench);
  \draw[arr] (bench) edge[bend right=15] (ort);
  \draw[arr] (bench) edge[bend left=15]  (sic);
\end{tikzpicture}
\end{center}

# Results

## Benchmark Setup

\begin{columns}[onlytextwidth]
\begin{column}{0.5\textwidth}
\textbf{Test matrices:}
\begin{itemize}
  \item Grid sizes: $4\times4$ to $8\times8$
  \item 3 random seeds per size (42, 123, 456)
  \item Timeout: \textbf{60 seconds} per run
  \item 15 total runs per solver
\end{itemize}
\end{column}
\begin{column}{0.5\textwidth}
\textbf{Metrics collected:}
\begin{itemize}
  \item Wall-clock time (ms)
  \item Optimal cost (€)
  \item Coverage (\%)
  \item Solution equivalence check
\end{itemize}
\end{column}
\end{columns}

\vspace{0.5em}

\begin{block}{Correctness validation}
For instances where both solvers complete, their optimal costs are compared. All 6 completed instances (three $4\times4$, three $5\times5$) produce \textbf{identical costs}, confirming model equivalence.
\end{block}

## Benchmark Results

\begin{table}
\centering
\small
\begin{tabular}{lcrrcrr}
\toprule
\textbf{Grid} & \textbf{Seed} & \multicolumn{2}{c}{\textbf{OR-Tools}} & & \multicolumn{2}{c}{\textbf{SICStus}} \\
\cmidrule{3-4} \cmidrule{6-7}
& & Time (ms) & Cost (€) & & Time (ms) & Cost (€) \\
\midrule
$4\times4$ & 42  & 338 & 13\,600 & & 371  & 13\,600 \\
$4\times4$ & 123 & 342 & 14\,000 & & 383  & 14\,000 \\
$4\times4$ & 456 & 344 & 14\,000 & & 397  & 14\,000 \\
\midrule
$5\times5$ & 42  & 332 & 22\,500 & & 13\,850 & 22\,500 \\
$5\times5$ & 123 & 337 & 21\,500 & & 8\,873  & 21\,500 \\
$5\times5$ & 456 & 327 & 21\,500 & & 13\,329 & 21\,500 \\
\midrule
$6\times6$ & 42  & 373 & 31\,600 & & \textcolor{red}{TIMEOUT} & --- \\
$6\times6$ & 123 & 349 & 31\,600 & & \textcolor{red}{TIMEOUT} & --- \\
$6\times6$ & 456 & 347 & 31\,200 & & \textcolor{red}{TIMEOUT} & --- \\
\midrule
$7\times7$ & all & $\approx$390 & $\approx$42\,700 & & \textcolor{red}{TIMEOUT} & --- \\
$8\times8$ & all & $\approx$440 & $\approx$55\,700 & & \textcolor{red}{TIMEOUT} & --- \\
\bottomrule
\end{tabular}
\caption{Benchmark summary (60 s timeout)}
\end{table}

## Solve Time Comparison

\begin{center}
\begin{tikzpicture}[scale=0.88]
  % Axes
  \draw[->] (0,0) -- (0,5.0) node[above,font=\footnotesize] {Time (log scale)};
  \draw[->] (0,0) -- (8.0,0);

  % Group labels on X axis
  \node[below,font=\small] at (1.05,0) {$4{\times}4$};
  \node[below,font=\small] at (3.05,0) {$5{\times}5$};
  \node[below,font=\small] at (5.05,0) {$6{\times}6$};
  \node[below,font=\small] at (7.05,0) {$7{\times}7$};

  % OR-Tools bars (blue) ~400 ms for all sizes
  \fill[blue!60] (0.5,0) rectangle (1.1, 0.9);
  \fill[blue!60] (2.5,0) rectangle (3.1, 0.9);
  \fill[blue!60] (4.5,0) rectangle (5.1, 0.9);
  \fill[blue!60] (6.5,0) rectangle (7.1, 0.9);

  % SICStus bars
  \fill[orange!70] (1.1,0) rectangle (1.7, 0.92);   % 4x4 ~380 ms
  \fill[orange!70] (3.1,0) rectangle (3.7, 2.5);    % 5x5 ~12 s
  \fill[red!55]    (5.1,0) rectangle (5.7, 4.3);    % 6x6 TIMEOUT
  \fill[red!55]    (7.1,0) rectangle (7.7, 4.3);    % 7x7 TIMEOUT
  \node[font=\tiny,rotate=90,white] at (5.4,2.2) {TIMEOUT};
  \node[font=\tiny,rotate=90,white] at (7.4,2.2) {TIMEOUT};

  % Y axis ticks
  \draw (-0.1,0.9)  -- (0,0.9)  node[left,font=\tiny] {${\approx}400$ms};
  \draw (-0.1,2.5)  -- (0,2.5)  node[left,font=\tiny] {12s};
  \draw (-0.1,4.3)  -- (0,4.3)  node[left,font=\tiny] {60s+};

  % Legend — stacked vertically on the right
  \fill[blue!60]   (8.3,3.8) rectangle (8.7,4.1);
  \node[right,font=\scriptsize] at (8.7,3.95) {OR-Tools CP-SAT};
  \fill[orange!70] (8.3,3.2) rectangle (8.7,3.5);
  \node[right,font=\scriptsize] at (8.7,3.35) {SICStus CLP(FD)};
\end{tikzpicture}
\end{center}

## Solution Quality

\begin{columns}[onlytextwidth]
\begin{column}{0.5\textwidth}
\begin{block}{Coverage}
Both solvers achieve approximately \textbf{82--84\%} coverage across all tested instances.

The remaining \textbf{16--18\%} of cells are intentionally left uncovered---it is cheaper to pay the €800 penalty than to build a tower that would only serve remote cells.
\end{block}
\end{column}
\begin{column}{0.5\textwidth}
\begin{block}{Model Equivalence}
On all 6 instances where both solvers terminate:
\begin{itemize}
  \item \textbf{Identical optimal costs}
  \item \textbf{Same coverage \%}
\end{itemize}
This confirms that both implementations encode \textbf{exactly the same CSP}, despite using different constraint programming paradigms.
\end{block}
\end{column}
\end{columns}

# Performance Analysis

## Why is SICStus Slower?

Four compounding factors explain the performance gap:

\begin{enumerate}
  \item \textbf{Naive variable ordering} in \texttt{labeling/2}
  \item \textbf{Weak lower bounds} in branch-and-bound
  \item \textbf{CLP(FD) arc consistency vs CDCL} in CP-SAT
  \item \textbf{Unhandled symmetry} between P1 and P2
\end{enumerate}

\vspace{0.5em}

\begin{alertblock}{Root cause}
These are not fundamental limitations of CLP(FD)---they are \textbf{configuration choices} in this solver setup, each fixable with targeted improvements.
\end{alertblock}

## Factor 1 — Naive Variable Ordering

\begin{columns}[onlytextwidth]
\begin{column}{0.55\textwidth}
\textbf{Current labeling:}
\begin{itemize}
  \item All tower vars first, then all antenna vars, then all slacks
  \item Solver commits to a full tower layout \emph{before} considering coverage
  \item Conflicts discovered deep in the tree $\Rightarrow$ expensive backtracking
\end{itemize}

\vspace{0.5em}
\textbf{Fix --- First-Fail (\texttt{ff}) heuristic:}
\begin{itemize}
  \item At each step, pick variable with \textbf{smallest remaining domain}
  \item Surfaces failures earlier, cuts branches sooner
\end{itemize}
\end{column}
\begin{column}{0.45\textwidth}
\begin{exampleblock}{One-line fix}
\small
\texttt{labeling([ff,}\\
\quad\texttt{minimize(Cost)],}\\
\quad\texttt{AllVars)}
\end{exampleblock}
\vspace{0.5em}
Other candidates: \texttt{ffc}, \texttt{bisect}, \texttt{min}/\texttt{max} value ordering.
\end{column}
\end{columns}

## Factor 2 — Weak Lower Bounds

\begin{columns}[onlytextwidth]
\begin{column}{0.5\textwidth}
\begin{block}{SICStus branch-and-bound}
\begin{itemize}
  \item Finds a feasible solution, records cost as upper bound
  \item Continues search for strictly cheaper solutions
  \item Lower bounds from \textbf{constraint propagation only}---often loose
  \item Cannot prove a subtree is suboptimal without exploring it
\end{itemize}
\end{block}
\end{column}
\begin{column}{0.5\textwidth}
\begin{block}{OR-Tools CP-SAT}
\begin{itemize}
  \item Runs an \textbf{LP relaxation} at each node
  \item LP gives \textbf{tight fractional lower bounds}
  \item Can prune entire subtrees with a \emph{proof} they cannot improve
  \item Dramatically reduces the effective search space
\end{itemize}
\end{block}
\end{column}
\end{columns}

## Factor 3 — Propagation vs Learning

\begin{columns}[onlytextwidth]
\begin{column}{0.5\textwidth}
\begin{exampleblock}{CLP(FD) — Arc Consistency}
\begin{itemize}
  \item Domain shrinks $\Rightarrow$ re-check connected constraints
  \item Transitively prunes domains (AC-3 / AC-4)
  \item \textbf{Sound but shallow}: cannot reason about combinations of decisions
  \item \textbf{Backtracks and forgets}
\end{itemize}
\end{exampleblock}
\end{column}
\begin{column}{0.5\textwidth}
\begin{exampleblock}{CP-SAT — CDCL}
\begin{itemize}
  \item Encodes everything as Boolean clauses
  \item On contradiction, \textbf{analyses root cause}
  \item Derives a \textbf{no-good clause} and adds it permanently
  \item Clause prunes regions in \emph{future} branches
  \item \textbf{Learns and remembers}
\end{itemize}
\end{exampleblock}
\end{column}
\end{columns}

\begin{center}
\textbf{CLP(FD) backtracks; CP-SAT prunes with proof.}
\end{center}

## Factor 4 — Unhandled Symmetry

P1 and P2 have \textbf{identical coverage radii} ($r = 1$).

\vspace{0.2em}

\begin{block}{Consequence}
Any solution with P1 and P2 antenna placements swapped has \textbf{exactly the same cost}. Without symmetry breaking, the solver explores \textbf{both symmetric variants}---effectively doubling work across a large portion of the search tree.
\end{block}

\vspace{0.2em}

\textbf{Fix --- Lexicographic ordering constraint:}

$$\texttt{lex\_chain([P1, P2])}$$

\vspace{-0.4em}
Forces a canonical ordering, eliminating the symmetric half of the search space. OR-Tools handles this \textbf{internally}; the SICStus model does not.

## OR-Tools Timing Context

\begin{block}{Important: OR-Tools overhead}
The 330--500 ms OR-Tools figures are dominated by:
\begin{enumerate}
  \item Python interpreter startup
  \item JSON map loading and parsing
  \item Model construction and coverage precomputation
\end{enumerate}
The actual \textbf{CP-SAT search time is likely single-digit milliseconds} for these grid sizes.
\end{block}

\vspace{0.3em}

\begin{columns}[onlytextwidth]
\begin{column}{0.5\textwidth}
SICStus at 4×4 ($\approx$380 ms) is \textbf{comparable} once Prolog startup and library loading are accounted for.
\end{column}
\begin{column}{0.5\textwidth}
The divergence becomes visible at \textbf{5×5} where CLP(FD) search time dominates (8--14 s), and the solver cannot complete \textbf{6×6} within 60 s.
\end{column}
\end{columns}

# Conclusions

## Summary

\begin{columns}[onlytextwidth]
\begin{column}{0.55\textwidth}
\begin{block}{What we built}
\begin{itemize}
  \item Full CSP/CSOP formulation of a realistic telecom network placement problem
  \item Two complete, equivalent implementations in OR-Tools and SICStus
  \item Shared map generator and benchmark harness
  \item Quantified comparative study across 5 grid sizes
\end{itemize}
\end{block}
\end{column}
\begin{column}{0.45\textwidth}
\begin{block}{Key findings}
\begin{itemize}
  \item \textbf{Model equivalence} confirmed on all shared instances
  \item OR-Tools scales to 8×8+ with ease; SICStus times out at 6×6
  \item The gap is \textbf{not a fundamental CLP(FD) limitation}---it is solver configuration
  \item CDCL + LP bounds vs pure propagation is the decisive factor
\end{itemize}
\end{block}
\end{column}
\end{columns}

## Course Connections

This project applies the core PLR/CLP competencies:

\begin{itemize}
  \item \textbf{Declarative modelling}: problem expressed as constraints, not procedural search
  \item \textbf{CLP(FD) in SICStus Prolog}: finite domain variables, arc consistency, branch-and-bound
  \item \textbf{Constraint propagation}: how domain reductions propagate through the constraint graph
  \item \textbf{Search strategies}: impact of variable ordering and value selection heuristics
  \item \textbf{Comparative study}: same model, different solvers---understanding \emph{why} performance differs
\end{itemize}

\vspace{0.3em}
\begin{alertblock}{}
The performance gap between solvers is itself a concrete demonstration of course theory: why heuristics, symmetry breaking, and learned clauses matter in practice.
\end{alertblock}

## Future Work

\begin{enumerate}
  \item \textbf{SICStus search heuristics}: add \texttt{ff} variable ordering; expected to make 6×6 solvable
  \item \textbf{Symmetry breaking}: \texttt{lex\_chain([P1, P2])} to eliminate symmetric search space
  \item \textbf{Extended OR-Tools benchmarks}: test 10×10, 12×12, 15×15 to find CP-SAT's own limits
  \item \textbf{Mathematical formalization}: complete ILP/CSP notation for report submission
  \item \textbf{Grid visualization}: matplotlib overlay of terrain, towers, and coverage radii
\end{enumerate}

## Questions?

\begin{center}
\vspace{1em}
{\Large Multi-Tenant Mobile Antenna Placement Optimization}

\vspace{0.5em}

{\large Martim Pinheiro (up20509641) · Adam Oprchal (up202512712)}

\vspace{1.5em}

{\large Thank you!}
\end{center}

