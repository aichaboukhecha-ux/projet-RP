# Sokoban Fairy Puzzle - Part 3 Report

This report covers the Part 3 additions: the deadlock detector, the A*
deadlock switch, the Figure 7 boards, the benchmark, the GUI comparison
screen and the tests. Every number below comes from `benchmark.py` on the
seven boards (five from Figure 4, two from Figure 7). No result is
estimated.

Environment: Python 3.13.14, pygame 2.6.1. Node limit: 400000 expansions.
There is no time limit in the solver; measurements are in nodes, not
seconds. The printed comparison of the algorithms shows the theoretical
complexity, the cost and the nodes (expanded, generated); the other
counters stay in `benchmark.csv`.

---

## 1. Modelling choices

A board is a grid of ASCII characters read by `boxgame.parse_board`:

```
O  wall          R  player          B  box
S  target        .  player on target  *  box on target
' ' floor
```

The parser enforces the two invariants used everywhere:

- exactly one player;
- the number of boxes equals the number of targets.

A state is the player position plus the set of box positions. Walls and
targets never change, so they are shared by every state of a level. The
state key is `(player, sorted(boxes))`; it is used by the OPEN/CLOSED
lists.

One action is one move of the player. Walking and pushing both cost 1, so
the cost of a solution is its number of actions. This is the same cost
used by BFS and by A*, which is why their optimal costs can be compared
directly in Section 6.

A state is a goal when every target holds a box (`targets <= boxes`).
Because the parser guarantees equal counts, this is equivalent to saying
that every box is on a target.

`Node` stores the state, the parent, the action that produced it, `g`, and
`f = g + h`. BFS uses `g` only. A* calls `setF(heuristic)` before pushing
a node.

---

## 2. The three heuristics

### h1 - misplaced boxes

```
h1(state) = number of boxes that are not on a target
```

Each misplaced box needs at least one push to reach a target, so h1 never
overestimates the remaining cost. It is admissible but weak: it ignores
distance and the player position. On the test board `OS BR` (one box two
cells from its target, player beside it) h1 = 1 while the optimum is 2.

### h2 - distance sum with a penalty

```
h2(state) = 2 * misplaced boxes
          + sum over boxes of the Manhattan distance to the nearest target
```

The distance term alone is a lower bound: a box needs at least one push
per Manhattan unit. The `2 * misplaced` term is added to make the
heuristic more aggressive. It is not justified by a lower-bound argument:
on the same `OS BR` board h2 = 4 while the BFS optimum is 2, so h2 is
**inadmissible**. It can still be used as a comparison point, and on these
seven boards it happened to return optimal solutions, but optimality is
not guaranteed by the heuristic.

### h3 - real push distances, matching and player walk

h3 has three parts.

1. **Real push distances.** A reverse breadth-first search starts at each
   target and walks backwards through legal pushes: if a box is now at
   `(row, col)` and was pushed with direction `(dr, dc)`, it was at
   `(row - dr, col - dc)` and the player was at `(row - 2*dr, col - 2*dc)`.
   The result is, for each target, the minimum number of pushes from every
   cell of the board. Unlike Manhattan distance, walls cannot be crossed.
   The search ignores the other boxes and the real accessibility of the
   player, which makes it a lower bound. The tables are cached per level.
2. **One-to-one matching.** Each box must end on a different target. The
   cheapest assignment is found exactly with dynamic programming over a
   bitmask of used targets (`cheapest_assignment`). A box that cannot push
   to a target gets the cost `UNREACHABLE = 1000`, which is larger than any
   real solution cost on these boards.
3. **Player walk.** The player must first reach a box before pushing it.
   The Manhattan distance from the player to the nearest misplaced box,
   minus one (being adjacent is enough to push), is a lower bound on the
   walking actions that precede the first push. It is floored at zero.

The push term counts pushes and the walk term counts the actions before
the first push, so the two parts count different actions and their sum is
still a lower bound. On `OS BR`, h3 = 2 and the optimum is 2.

Start-of-board values:

| Board | h1 | h2 | h3 | true cost |
|---|---|---|---|---|
| Fig. 7 Exemple 1 | 3 | 17 | 16 | 41 |
| Fig. 7 Exemple 2 | 4 | 19 | 17 | 55 |

Per evaluation, h1 costs O(B), h2 costs O(B*T), and h3 costs
O(B*T + B^2*2^B) after the push tables are built once per level for
O(T*H*W). With B <= 4, the bitmask part is small.

---

## 3. Deadlock detection

The dead-cell set is computed once per level from the walls and targets.
It contains two kinds of cells.

### Corner deadlock

A non-target floor cell is a corner deadlock when it has at least one
vertical wall neighbour (up or down) and at least one horizontal wall
neighbour (left or right). If a box is pushed into such a cell, the two
perpendicular walls block two of the four push directions, and for the
other two the player would have to stand inside one of those walls. The
box can never leave. A target cell is never added: a box on a target is
already where it belongs.

### Line deadlock

Two corner-deadlock cells are connected when they are on the same row or
column with at least one cell between them. The whole segment becomes
dead when:

- no cell of the segment is a wall;
- no cell of the segment is a target;
- at least one of the two parallel sides of the segment is entirely wall.

A box on the segment cannot be pushed perpendicular to it, because the
player would have to stand on the fully walled side. It can only be pushed
along the segment, and both ends are corner deadlocks, so it is trapped
wherever it stops on the line.

The implementation is `dead_cells(state)`. It returns a `frozenset` so it
can be reused without copying. `dead_line(a, b, ...)` tests one segment.
`has_deadlock(state, dead=None)` returns True when at least one box is on
a dead cell that is not a target. When no set is supplied it computes one;
A* computes it once at the start and passes it to every call.

### Validation against Figures 5 and 6

The rule reproduces the red and yellow cells of the two figures exactly.

| Board | Red corner cells (Figure 5) | Yellow line cells (Figure 6) |
|---|---|---|
| Figure 7 / Exemple 1 | (1,2) (1,4) (1,5) (5,2) (5,4) (5,5) | (2,5) (3,5) (4,5) |
| Figure 7 / Exemple 2 | (1,4) (2,6) (3,1) (4,4) (4,6) | (3,6) (4,5) |

The tests check each red cell, each yellow cell, and exact equality with
the union (no extra dead cells). They also check the negative case: a box
on a target in a corner is **not** a deadlock.

### Integration in A*

`astar(..., use_deadlock=False)` keeps the old behaviour. With
`use_deadlock=True`:

1. the dead set is computed once from the initial state;
2. the root is checked;
3. every generated child is checked before it is pushed; a deadlocked
   child is discarded.

This only removes states that cannot lead to a goal, so the optimal cost
is unchanged. The switch is kept so the benchmark can measure its effect
against the same heuristic.

Cost of the mechanism: building the set is O(H*W + C^2*L), where H*W is
the board size, C the number of corners and L the longest line; checking a
state is O(B), one lookup per box.

---

## 4. Theoretical complexity

`b` is the branching factor (at most 4 moves), `d` the solution depth in
actions, `B` the number of boxes, `T` the number of targets, `H*W` the
board size.

| Algorithm | Frontier | Worst-case time | Space | Cost per evaluated node |
|---|---|---|---|---|
| BFS | FIFO queue | O(b^d) | O(b^d) | O(1) |
| A* h1 | priority queue on f | O(b^d) | O(b^d) | O(B) |
| A* h2 | priority queue on f | O(b^d) | O(b^d) | O(B*T) |
| A* h3 | priority queue on f | O(b^d) | O(b^d) | O(B*T + B^2*2^B), after O(T*H*W) once per level |
| A* h3+deadlock | priority queue on f | O(b^d) | O(b^d) | as h3, plus O(B) per child |

A* is asymptotically exponential in the worst case, like BFS. The
heuristics do not change the worst-case bound; they reduce the number of
expanded nodes in practice, which is what Section 6 measures. The
deadlock precomputation adds O(H*W + C^2*L) once per level; a reopen of a
CLOSED state costs the same as a new expansion (needed because h2 is not
admissible).

---

## 5. Protocol and counters

`benchmark.py` runs seven methods on the seven boards:

Main five:

- BFS;
- A* with h1;
- A* with h2;
- A* with h3;
- A* with h3 and `use_deadlock=True`.

Two extra runs show the filter with the weaker heuristics:

- A* with h1 and `use_deadlock=True`;
- A* with h2 and `use_deadlock=True`.

The node limit is 400000 expansions for every run. A run that reaches it
is reported as `LIMIT`; a run that exhausts the frontier without a goal is
reported as `NO-SOLUTION`. There is no timeout.

The printed comparison table shows, for every run:

- the method and its **theoretical complexity**;
- the **cost** of the solution;
- the **expanded** nodes;
- the **generated** nodes;
- the status.

`benchmark.csv` stores, in addition, the CLOSED and maximum OPEN sizes,
the heuristic calls (deprecated by this report), the deadlock checks, and
the complete action list for every run. The tables below use the printed
comparison columns only.

---

## 6. Results

### 6.1 Summary comparison (complexity, cost, nodes)

Total expanded and generated nodes over the seven boards. Same solution
cost on every board (Section 6.2).

| Method | Theoretical complexity | Expanded | Generated |
|---|---|---|---|
| BFS | O(b^d) time / space | 77018 | 78893 |
| A* h1 | O(b^d) h O(B) | 73404 | 75330 |
| A* h2 | O(b^d) h O(B*T) | 59480 | 62618 |
| A* h3 | O(b^d) h O(B^2*2^B) | **8506** | 10388 |
| A* h3+deadlock | O(b^d) h O(B^2*2^B) + O(B) | **8506** | **9384** |

A* h3 expands **89.0% fewer** nodes than BFS (77018 -> 8506). The
deadlock filter does not change h3's expanded count on these boards;
h3 already gives dead states a huge `f`, so they stay at the bottom of
OPEN. The filter still avoids generating them: generated nodes fall by
**9.7%** (10388 -> 9384), and the maximum size of OPEN drops as well.

### 6.2 Cost

All 49 runs found a solution inside the node limit, and all seven methods
returned the same cost on every board. BFS is the reference, and the A*
variants preserve its optimum.

| Board | Cost |
|---|---|
| Fig. 4 Exemple 1 | 4 |
| Fig. 4 Exemple 2 | 29 |
| Fig. 4 Exemple 3 | 33 |
| Fig. 4 Exemple 4 | 30 |
| Fig. 4 Exemple 5 | 25 |
| Fig. 7 Exemple 1 | 41 |
| Fig. 7 Exemple 2 | 55 |

Limit-reached or unsolved runs: **none** (all 49 rows have status `ok`).

### 6.3 Expanded nodes (main five methods)

The lowest value of each row is in bold.

| Board | BFS | A* h1 | A* h2 | A* h3 | A* h3+deadlock |
|---|---|---|---|---|---|
| Fig. 4 Exemple 1 | 15 | 12 | 9 | **6** | **6** |
| Fig. 4 Exemple 2 | 1162 | 1106 | 749 | 196 | **196** |
| Fig. 4 Exemple 3 | 2560 | 2489 | 1443 | 353 | **353** |
| Fig. 4 Exemple 4 | 6665 | 5476 | 3098 | 878 | **878** |
| Fig. 4 Exemple 5 | 9430 | 7337 | 2128 | 716 | **716** |
| Fig. 7 Exemple 1 | 2345 | 2313 | 2242 | 1023 | **1023** |
| Fig. 7 Exemple 2 | 54841 | 54671 | 49811 | 5334 | **5334** |

h3 and h3+deadlock tie on every board. BFS and h1 stay close together
because h1 barely guides the search.

### 6.4 Generated nodes (main five methods)

| Board | BFS | A* h1 | A* h2 | A* h3 | A* h3+deadlock |
|---|---|---|---|---|---|
| Fig. 4 Exemple 1 | 19 | 16 | 14 | 11 | 11 |
| Fig. 4 Exemple 2 | 1237 | 1178 | 835 | 263 | 251 |
| Fig. 4 Exemple 3 | 2609 | 2554 | 1527 | 401 | 372 |
| Fig. 4 Exemple 4 | 7338 | 6118 | 3591 | 1089 | 1013 |
| Fig. 4 Exemple 5 | 10403 | 8308 | 2761 | 1116 | 1028 |
| Fig. 7 Exemple 1 | 2378 | 2354 | 2275 | 1141 | 1087 |
| Fig. 7 Exemple 2 | 54909 | 54802 | 51615 | 6367 | 5622 |

### 6.5 Expanded nodes, without -> with the deadlock filter

This is the clearest proof that the deadlock filter works.

| Heuristic | Without filter | With filter | Reduction |
|---|---|---|---|
| h1 | 73404 | 12640 | **82.8%** |
| h2 | 59480 | 9665 | **83.8%** |
| h3 | 8506 | 8506 | 0.0% |

With a weak heuristic, the search generates many dead states; the filter
removes them and the search becomes many times smaller. With h3 the
heuristic already keeps the dead states at the bottom of OPEN, so the
expanded count is unchanged, but the filter still saves generated nodes
and memory.

### 6.6 Full per-run table (comparison columns)

Status is `ok` for every row.

| Board | Method | Cost | Expanded | Generated | Status |
|---|---|---|---|---|---|
| Fig. 4 Exemple 1 | BFS | 4 | 15 | 19 | ok |
| Fig. 4 Exemple 1 | A* h1 | 4 | 12 | 16 | ok |
| Fig. 4 Exemple 1 | A* h2 | 4 | 9 | 14 | ok |
| Fig. 4 Exemple 1 | A* h3 | 4 | 6 | 11 | ok |
| Fig. 4 Exemple 1 | A* h3+deadlock | 4 | 6 | 11 | ok |
| Fig. 4 Exemple 1 | A* h1+deadlock | 4 | 12 | 16 | ok |
| Fig. 4 Exemple 1 | A* h2+deadlock | 4 | 9 | 14 | ok |
| Fig. 4 Exemple 2 | BFS | 29 | 1162 | 1237 | ok |
| Fig. 4 Exemple 2 | A* h1 | 29 | 1106 | 1178 | ok |
| Fig. 4 Exemple 2 | A* h2 | 29 | 749 | 835 | ok |
| Fig. 4 Exemple 2 | A* h3 | 29 | 196 | 263 | ok |
| Fig. 4 Exemple 2 | A* h3+deadlock | 29 | 196 | 251 | ok |
| Fig. 4 Exemple 2 | A* h1+deadlock | 29 | 468 | 496 | ok |
| Fig. 4 Exemple 2 | A* h2+deadlock | 29 | 362 | 399 | ok |
| Fig. 4 Exemple 3 | BFS | 33 | 2560 | 2609 | ok |
| Fig. 4 Exemple 3 | A* h1 | 33 | 2489 | 2554 | ok |
| Fig. 4 Exemple 3 | A* h2 | 33 | 1443 | 1527 | ok |
| Fig. 4 Exemple 3 | A* h3 | 33 | 353 | 401 | ok |
| Fig. 4 Exemple 3 | A* h3+deadlock | 33 | 353 | 372 | ok |
| Fig. 4 Exemple 3 | A* h1+deadlock | 33 | 383 | 388 | ok |
| Fig. 4 Exemple 3 | A* h2+deadlock | 33 | 372 | 386 | ok |
| Fig. 4 Exemple 4 | BFS | 30 | 6665 | 7338 | ok |
| Fig. 4 Exemple 4 | A* h1 | 30 | 5476 | 6118 | ok |
| Fig. 4 Exemple 4 | A* h2 | 30 | 3098 | 3591 | ok |
| Fig. 4 Exemple 4 | A* h3 | 30 | 878 | 1089 | ok |
| Fig. 4 Exemple 4 | A* h3+deadlock | 30 | 878 | 1013 | ok |
| Fig. 4 Exemple 4 | A* h1+deadlock | 30 | 1330 | 1469 | ok |
| Fig. 4 Exemple 4 | A* h2+deadlock | 30 | 999 | 1110 | ok |
| Fig. 4 Exemple 5 | BFS | 25 | 9430 | 10403 | ok |
| Fig. 4 Exemple 5 | A* h1 | 25 | 7337 | 8308 | ok |
| Fig. 4 Exemple 5 | A* h2 | 25 | 2128 | 2761 | ok |
| Fig. 4 Exemple 5 | A* h3 | 25 | 716 | 1116 | ok |
| Fig. 4 Exemple 5 | A* h3+deadlock | 25 | 716 | 1028 | ok |
| Fig. 4 Exemple 5 | A* h1+deadlock | 25 | 2899 | 3236 | ok |
| Fig. 4 Exemple 5 | A* h2+deadlock | 25 | 1045 | 1316 | ok |
| Fig. 7 Exemple 1 | BFS | 41 | 2345 | 2378 | ok |
| Fig. 7 Exemple 1 | A* h1 | 41 | 2313 | 2354 | ok |
| Fig. 7 Exemple 1 | A* h2 | 41 | 2242 | 2275 | ok |
| Fig. 7 Exemple 1 | A* h3 | 41 | 1023 | 1141 | ok |
| Fig. 7 Exemple 1 | A* h3+deadlock | 41 | 1023 | 1087 | ok |
| Fig. 7 Exemple 1 | A* h1+deadlock | 41 | 1134 | 1175 | ok |
| Fig. 7 Exemple 1 | A* h2+deadlock | 41 | 1063 | 1081 | ok |
| Fig. 7 Exemple 2 | BFS | 55 | 54841 | 54909 | ok |
| Fig. 7 Exemple 2 | A* h1 | 55 | 54671 | 54802 | ok |
| Fig. 7 Exemple 2 | A* h2 | 55 | 49811 | 51615 | ok |
| Fig. 7 Exemple 2 | A* h3 | 55 | 5334 | 6367 | ok |
| Fig. 7 Exemple 2 | A* h3+deadlock | 55 | 5334 | 5622 | ok |
| Fig. 7 Exemple 2 | A* h1+deadlock | 55 | 6414 | 6505 | ok |
| Fig. 7 Exemple 2 | A* h2+deadlock | 55 | 5815 | 6078 | ok |

### 6.7 Figure 7 boards in detail

Both boards were transcribed from page 7 of the assignment. Validation:
rectangular grid, closed by walls, exactly one player, and boxes = targets
(3 = 3 for Exemple 1, 4 = 4 for Exemple 2).

**Reading ambiguity.** In Figure 7 / Exemple 2, the two bottom-left cells
and the two top-right cells are not drawn (they are plain white in the
picture). They are read as walls `O`. The player cannot enter them either
way, so the choice does not change the state space; it only keeps the
"closed board" convention used by every other level. There is no other
ambiguity.

#### Figure 7 / Exemple 1 (7x7)

```
OOOOOOO
OS O RO
O  OB O
OS  B O
O  OB O
OS O  O
OOOOOOO
```

| Method | Cost | Expanded | Generated |
|---|---|---|---|
| BFS | 41 | 2345 | 2378 |
| A* h1 | 41 | 2313 | 2354 |
| A* h2 | 41 | 2242 | 2275 |
| A* h3 | 41 | **1023** | 1141 |
| A* h3+deadlock | 41 | **1023** | 1087 |

Compared with BFS, h3+deadlock expands 56.4% fewer nodes (2345 -> 1023).
The deadlock filter reduces generated nodes by 4.7% (1141 -> 1087) while
expanding exactly the same states.

BFS, A* h1 and A* h2 return this 41-action sequence:

```
DOWN DOWN LEFT LEFT LEFT UP LEFT DOWN DOWN UP RIGHT RIGHT RIGHT RIGHT
UP UP LEFT DOWN RIGHT DOWN LEFT LEFT LEFT DOWN LEFT UP UP DOWN RIGHT
RIGHT RIGHT RIGHT DOWN DOWN LEFT UP RIGHT UP LEFT LEFT LEFT
```

A* h3 and A* h3+deadlock return this other 41-action sequence (same cost):

```
DOWN DOWN LEFT LEFT LEFT UP LEFT DOWN DOWN RIGHT UP RIGHT RIGHT RIGHT
DOWN DOWN LEFT UP RIGHT UP LEFT LEFT LEFT DOWN LEFT UP UP RIGHT DOWN
RIGHT RIGHT RIGHT UP UP LEFT DOWN RIGHT DOWN LEFT LEFT LEFT
```

#### Figure 7 / Exemple 2 (8x6)

```
OOOOOOOO
OSSS OOO
O S B  O
O  BBB O
OOOO  RO
OOOOOOOO
```

| Method | Cost | Expanded | Generated |
|---|---|---|---|
| BFS | 55 | 54841 | 54909 |
| A* h1 | 55 | 54671 | 54802 |
| A* h2 | 55 | 49811 | 51615 |
| A* h3 | 55 | **5334** | 6367 |
| A* h3+deadlock | 55 | **5334** | 5622 |

This is the hardest board of the set. h3+deadlock expands 90.3% fewer
nodes than BFS (54841 -> 5334), and the deadlock filter reduces generated
nodes by 11.7% (6367 -> 5622).

All five main methods return this same 55-action sequence; only the counter
values differ:

```
UP UP LEFT LEFT LEFT LEFT DOWN LEFT UP RIGHT RIGHT RIGHT RIGHT RIGHT
DOWN DOWN LEFT UP RIGHT UP LEFT LEFT RIGHT DOWN DOWN LEFT UP LEFT UP
DOWN RIGHT RIGHT UP LEFT UP LEFT RIGHT DOWN DOWN LEFT UP LEFT LEFT
DOWN RIGHT RIGHT RIGHT DOWN RIGHT UP RIGHT UP LEFT LEFT LEFT
```

The complete action list of every (board, method) pair is in
`benchmark.csv`.

---

## 7. GUI

The existing look, sounds, splash, controls, speed and level switching are
unchanged.

- **A** cycles the algorithm: BFS, A* h1, A* h2, A* h3, A* h3+deadlock.
  The playback is rebuilt from the cached result, so no search is repeated.
- The side panel shows the selected algorithm, its solution cost, its
  expanded nodes, its generated nodes and the status. A run that hits the
  node limit shows `LIMIT REACHED`; a search that exhausts the frontier
  shows `NO SOLUTION`.
- **C** opens the complexity comparison screen. The table shows exactly:
  the algorithm, its theoretical time complexity, the solution cost, the
  expanded nodes and the generated nodes. Below the table, two horizontal
  `pygame.draw.rect` bar charts show expanded and generated nodes, each
  scaled to the largest value of its chart and labelled with the number.
  The best algorithm (fewest expanded nodes) is highlighted in gold. A
  limit-reached run shows the text `limit reached` in place of a bar. No
  seconds are shown anywhere.
- The five algorithms run once when a level is loaded, while the existing
  "Solving with 5 algorithms ..." splash is displayed. Switching levels
  shows the same splash, so the window never freezes. The results are kept
  in memory and reused when the screen is opened.

Functions touched in `gui.py`: `ALGORITHMS` (complexity strings),
`SolutionPlayer.__init__` (display fields), `draw_panel` (cost and node
rows), `draw_status_message` (limit message), `draw_comparison`
(complexity / cost / nodes table and node bars), `short_label`,
`run_all_algorithms`, `make_player`, `load_level`, `main`, and the nested
`switch_level` / `choose_algorithm`.

---

## 8. Comparison and conclusion

- **Best overall method: A* h3 (+ deadlock).** It expands 8506 nodes over
  the seven boards, against 59480 for h2, 73404 for h1 and 77018 for BFS.
- **Best heuristic alone: h3.** Real push distances with walls, an exact
  one-to-one matching and the player walk make it by far the most
  informative guide. On Figure 7 / Exemple 2 it expands 90.2% fewer nodes
  than A* h1 (54671 -> 5334).
- **h1 is not worth using alone.** Its totals are essentially BFS totals:
  it ignores distance and the player position.
- **h2 is aggressive but not admissible** (`2 * misplaced` term). On these
  boards it still returned the optimal cost, but optimality is not
  guaranteed by the heuristic.
- **The deadlock filter is what the assignment asks for, and it works.**
  With h1 it removes 82.8% of the expansions (73404 -> 12640) and with h2
  83.8% (59480 -> 9665). With h3 the expanded count stays identical, but
  the filter saves 9.7% of the generated nodes and shrinks OPEN.
- **Optimality is preserved.** Every run returns the BFS cost. The
  deadlock filter only removes states that cannot reach a goal, and the
  A* implementation keeps the best `g` for each state (and reopens CLOSED
  states when a cheaper path is found).
- **No limit was reached** in the 49 measured runs. The GUI and tests
  still exercise the limit path with a one-node limit, which produces
  `LIMIT REACHED` and no solution.

The practical recommendation is A* with h3 and deadlock detection: the
heuristic does the heavy lifting and the deadlock filter adds safety for
almost no cost.

---

## 9. Reproducing the results

```
pip install pygame
python tests.py
python benchmark.py
python gui.py
```

`benchmark.py` prints the comparison table (method, theoretical
complexity, cost, expanded, generated, status) and writes `benchmark.csv`.
The CSV contains, for every (board, method) pair, also the CLOSED size,
the maximum OPEN size, the heuristic calls, the deadlock checks and the
complete action list. The tests run headless with
`SDL_VIDEODRIVER=dummy` (set automatically by `tests.py`).
