# Sokoban - Part 3 report

All numbers come from `python benchmark.py` (also saved in `benchmark.csv`).
Nothing is estimated. Complexity is counted in loop iterations, not seconds.

## 1. Model

- A state = the player position + the set of box positions. Walls and targets
  never change.
- One action = one move of the player (UP, DOWN, LEFT, RIGHT). Walking and
  pushing both cost 1, so the cost of a solution is its number of moves.
- Goal: every target holds a box (any box on any target).
- `Node` keeps `state`, `parent`, `action`, `g` and `f`. `setF(heuristic)` sets
  `f = g + h(state)`.

Board symbols: `O` wall, `R` player, `B` box, `S` target, `.` player on target,
`*` box on target.

## 2. Heuristics

**h1** = number of boxes not on a target. Cost per call: O(B).

**h2** (given by the teacher) = 2 * h1 + for each box, the Manhattan distance
to its nearest target. Cost per call: O(B*T). It is not admissible (the weight
of 2 can overestimate), but it still found the optimal cost on all seven boards.

**h3** (our proposal) has two parts:

1. *Pushes*: for each target we compute once per level, with a backward
   search, how many pushes a box needs from every cell to reach it. Walls and
   corners are taken into account, which Manhattan distance ignores. Then each
   box gets its own target, with the cheapest total (assignment solved with a
   small bitmask search, O(B*2^B)).
2. *Walk*: distance from the player to the nearest misplaced box, minus 1.

We did not prove that h3 never overestimates, but every A* run with h3
returned the same cost as BFS, so it behaved as a lower bound on all boards. A box on a cell with no push route to any
target gets a huge value, so those states are never expanded.

Why it is better than h2: Manhattan distance says a box is close to a target
even when a wall makes the way very long. The push table knows the real way.

## 3. Deadlock detection

`dead_cells(state)` is computed once per level:

- **Corner cell**: not a target, with a wall above or below and a wall on the
  left or right.
- **Line cells**: take two corner cells in the same row (or column). If every
  cell between them has no wall and no target, and the whole row above (or
  below) is wall, all the cells of the line are dead.

`has_deadlock(state)` returns True if one box is on a dead cell that is not a
target (check cost O(B)). `astar(..., use_deadlock=True)` does not push
children with a deadlock.

## 4. Complexity

| Algorithm | Search | Cost per node | Note |
|---|---|---|---|
| BFS | O(b^d) time and memory | none | b = branching factor, d = solution depth |
| A* h1 | O(b^d) worst case | O(B) | |
| A* h2 | O(b^d) worst case | O(B*T) | |
| A* h3 | O(b^d) worst case | O(B*2^B) | push table: one backward search per target, once |
| A* h3 + deadlock | O(b^d) worst case | O(B*2^B) + O(B) | dead cells: O(rows*cols) once, plus corner pairs |

A good heuristic does not change the worst case but lowers the real number of
nodes, which the tables below measure.

## 5. Results

Each cell is **expanded / generated**. Expanded = iterations of the main loop.
Generated = nodes created. Cost is the same for all five algorithms on every
board.

Figure 4:

| Board | cost | BFS | A* h1 | A* h2 | A* h3 | A* h3+deadlock |
|---|---|---|---|---|---|---|
| Fig. 4 Ex. 1 | 4 | 11 / 15 | 12 / 16 | 9 / 14 | 6 / 11 | 6 / 11 |
| Fig. 4 Ex. 2 | 29 | 1079 / 1162 | 1106 / 1178 | 749 / 835 | 196 / 263 | 196 / 251 |
| Fig. 4 Ex. 3 | 33 | 2496 / 2560 | 2489 / 2554 | 1443 / 1527 | 353 / 401 | 353 / 372 |
| Fig. 4 Ex. 4 | 30 | 6051 / 6665 | 5476 / 6118 | 3098 / 3591 | 878 / 1089 | 878 / 1013 |
| Fig. 4 Ex. 5 | 25 | 8446 / 9430 | 7337 / 8308 | 2128 / 2761 | 716 / 1116 | 716 / 1028 |

Figure 7:

| Board | cost | BFS | A* h1 | A* h2 | A* h3 | A* h3+deadlock |
|---|---|---|---|---|---|---|
| Fig. 7 Ex. 1 | 41 | 2307 / 2345 | 2313 / 2354 | 2242 / 2275 | 1023 / 1141 | 1023 / 1087 |
| Fig. 7 Ex. 2 | 55 | 54726 / 54841 | 54671 / 54802 | 49811 / 51615 | 5334 / 6367 | 5334 / 5622 |

Totals over the seven boards:

| Algorithm | expanded | generated | heuristic calls | deadlock checks |
|---|---|---|---|---|
| BFS | 75116 | 77018 | 0 | 0 |
| A* h1 | 73404 | 75330 | 75330 | 0 |
| A* h2 | 59480 | 62618 | 62618 | 0 |
| A* h3 | 8506 | 10388 | 10388 | 0 |
| A* h3+deadlock | 8506 | 9384 | 9384 | 10388 |

### Solutions of Figure 7 (A* h3 + deadlock)

**Figure 7, Example 1** - cost 41, 1023 iterations (expanded nodes), 1087 generated:

```
DOWN DOWN LEFT LEFT LEFT UP LEFT DOWN DOWN RIGHT UP RIGHT RIGHT RIGHT DOWN DOWN LEFT UP RIGHT UP LEFT LEFT LEFT DOWN LEFT UP UP RIGHT DOWN RIGHT RIGHT RIGHT UP UP LEFT DOWN RIGHT DOWN LEFT LEFT LEFT
```
**Figure 7, Example 2** - cost 55, 5334 iterations (expanded nodes), 5622 generated:

```
UP UP LEFT LEFT LEFT LEFT DOWN LEFT UP RIGHT RIGHT RIGHT RIGHT RIGHT DOWN DOWN LEFT UP RIGHT UP LEFT LEFT RIGHT DOWN DOWN LEFT UP LEFT UP DOWN RIGHT RIGHT UP LEFT UP LEFT RIGHT DOWN DOWN LEFT UP LEFT LEFT DOWN RIGHT RIGHT RIGHT DOWN RIGHT UP RIGHT UP LEFT LEFT LEFT
```

The other algorithms return other action lists of the same cost; all of them
are in `benchmark.csv`.

## 6. Effect of the deadlock filter (expanded nodes)

| Board | h1 | h1 + deadlock | h2 | h2 + deadlock | h3 | h3 + deadlock |
|---|---|---|---|---|---|---|
| Fig. 4 Ex. 1 | 12 | 12 | 9 | 9 | 6 | 6 |
| Fig. 4 Ex. 2 | 1106 | 468 | 749 | 362 | 196 | 196 |
| Fig. 4 Ex. 3 | 2489 | 383 | 1443 | 372 | 353 | 353 |
| Fig. 4 Ex. 4 | 5476 | 1330 | 3098 | 999 | 878 | 878 |
| Fig. 4 Ex. 5 | 7337 | 2899 | 2128 | 1045 | 716 | 716 |
| Fig. 7 Ex. 1 | 2313 | 1134 | 2242 | 1063 | 1023 | 1023 |
| Fig. 7 Ex. 2 | 54671 | 6414 | 49811 | 5815 | 5334 | 5334 |
| **Total** | **73404** | **12640** | **59480** | **9665** | **8506** | **8506** |

With h1 and h2 the filter removes most of the useless nodes (for example
Figure 7 Example 2: h2 goes from 49811 to a few thousand). With h3 the
expanded nodes stay the same: the push table already gives a huge value to
every dead cell, so those states are never taken from the queue. The filter
still saves generated nodes with h3 (9384 against 10388 over the seven boards).

## 7. Comparison

- BFS, h1 and h2 expand tens of thousands of nodes on the hardest boards.
  h1 is almost as slow as BFS because it only counts boxes.
- h3 is the biggest gain: about 7 times fewer expanded nodes than h2 in total.
- Deadlock detection is the biggest gain for weak heuristics (h1, h2) and a
  small gain for h3 (fewer generated nodes).
- Best choice: A* with h3 and the deadlock filter. It is optimal on all boards
  and expands the fewest nodes.

## 8. Boards used

The boards were rebuilt from the PDF pictures by overlaying a grid on every
figure. Cells of the picture that are not drawn (white) are written as walls,
which changes nothing because the player cannot reach them.

Figure 4, Example 1:
```
OOOOOO
OS B O
O OR O
O    O
O    O
OOOOOO
```
Figure 4, Example 2:
```
OOOOOOOOO
O       O
O       O
O  OOO  O
O    O. O
O     O O
O  B  O O
O     O O
OOOOOOOOO
```
Figure 4, Example 3:
```
OOOOOOOO
O   O  O
O  BR  O
O   OB O
OOOOO SO
OOOOO SO
OOOOOOOO
```
Figure 4, Example 4:
```
OOOOOOO
OO  OOO
OO  OOO
OO *  O
OOBOB O
O SRS O
O    OO
OOO  OO
OOOOOOO
```
Figure 4, Example 5:
```
OOOOOOOOO
OOOSO  OO
O    B OO
O B R  SO
OOO O OOO
OOOBO OOO
OOO  SOOO
OOOOOOOOO
```
Figure 7, Example 1:
```
OOOOOOO
OS O RO
O  OB O
OS  B O
O  OB O
OS O  O
OOOOOOO
```
Figure 7, Example 2:
```
OOOOOOOO
OSSS OOO
O S B  O
O  BBB O
OOOO  RO
OOOOOOOO
```

## 9. Interface

`python gui.py` plays the solution of the chosen algorithm. `A` changes the
algorithm, `C` opens the comparison screen (expanded, generated, heuristic
calls, deadlock checks and the theoretical complexity of each algorithm).
