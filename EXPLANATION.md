# Sokoban Fairy Puzzle - the whole code explained

This document explains the project from top to bottom:

- what every file does;
- how the data is represented;
- what happens line by line in `boxgame.py` and `search.py`;
- how the deadlock detector works;
- how BFS and A* work;
- how the three heuristics work;
- the complexity of every important function;
- how the GUI, the benchmark and the tests use all of this.

The code shown below is the real code. The `#` comments are short
explanations of what the line does.

---

## Table of contents

1. [What the program does](#1-what-the-program-does)
2. [Project structure and every file](#2-project-structure-and-every-file)
3. [The model: `boxgame.py`](#3-the-model-boxgamepy)
4. [The search tools: OPEN and CLOSED](#4-the-search-tools-open-and-closed)
5. [Deadlocks](#5-deadlocks)
6. [Breadth-first search](#6-breadth-first-search)
7. [The heuristics h1, h2 and h3](#7-the-heuristics-h1-h2-and-h3)
8. [A*](#8-a)
9. [Complexity](#9-complexity)
10. [Benchmark and results](#10-benchmark-and-results)
11. [The GUI](#11-the-gui)
12. [The tests](#12-the-tests)
13. [How to run everything](#13-how-to-run-everything)
14. [Small glossary](#14-small-glossary)
15. [The short version](#15-the-short-version)

---

## 1. What the program does

Sokoban is a puzzle. The board is a grid:

- `O` is a wall;
- `R` is the player;
- `B` is a box;
- `S` is a target;
- ` ` is empty floor;
- `.` is the player standing on a target;
- `*` is a box already on a target.

The rules are:

1. the player moves one cell at a time: up, down, left or right;
2. the player cannot walk through a wall;
3. the player cannot walk through a box;
4. the player can **push** a box by walking into it;
5. a box moves exactly one cell and only if the cell behind it is free;
6. the player can never pull a box;
7. the puzzle is solved when every target holds a box.

The program does not play randomly. It builds a graph:

- one **state** is a photo of the board: player position + box positions;
- one **action** is one move;
- an **edge** goes from one state to the state after one legal move;
- a **solution** is a path from the start state to a goal state.

Then BFS or A* searches this graph.

The data flow is:

```
text board
   |
   v
parse_board()          -> SokobanPuzzle (start state)
   |
   v
successorFunction()    -> all legal next states
   |
   v
BFS / A*               -> goal Node (or None)
   |
   v
Node.getSolution()     -> list of actions
   |
   v
GUI                    -> replay the actions on screen
```

---

## 2. Project structure and every file

```
projet-RP/
|
|-- boxgame.py              the model: state, rules, parser, Node
|-- search.py               OPEN/CLOSED, BFS, A*, heuristics, deadlocks
|-- levels.py               the 13 levels used by the GUI
|-- figure4_boards.py       the 5 boards of Figure 4
|-- figure7_boards.py       the 2 boards of Figure 7
|-- gui.py                  the Pygame interface
|-- benchmark.py            runs all algorithms on all boards
|-- benchmark.csv           the measured results
|-- tests.py                automatic tests
|-- main.py                 tiny console demo
|-- puzzle.py               old simple viewer (not used by the final GUI)
|-- report.md               written report
|-- README.md               quick start
|-- EXPLAIN_LIKE_IM_5.md    short explanation for beginners
|-- EXPLANATION.md          this long explanation
|-- SokobanFairyPuzzle.exe  packaged Windows game
|-- assets/                 images, fonts and sounds
|-- sfp/                    empty old build folder
|-- __pycache__/            Python cache (generated automatically)
```

### `boxgame.py`

The rules of the game.

- `Level` is a default 8x8 board, used by `main.py`.
- `SokobanPuzzle` is one state.
- `parse_board()` reads a list of strings and builds a `SokobanPuzzle`.
- `Node` is one node of the search tree.

### `search.py`

Everything about searching:

- `Closed`, `OpenFIFO`, `OpenPriority`: the OPEN and CLOSED lists;
- `dead_cells()`, `dead_line()`, `has_deadlock()`: the deadlock detector;
- `bfs()`: breadth-first search;
- `h1()`, `h2()`, `h3()`: the three heuristics;
- `push_distances()`: real push distances with walls;
- `cheapest_assignment()`: one-to-one box/target matching;
- `SearchResult`: the result plus all counters;
- `astar()`: A* with an optional deadlock filter.

### `levels.py`

A list of 13 ASCII boards:

- levels 1-6: the original levels of the project;
- levels 7-11: the five boards of Figure 4;
- levels 12-13: the two boards of Figure 7.

`level_count()` returns 13.

### `figure4_boards.py`

The five boards of Figure 4, copied by hand into ASCII.
`FIGURE4_ORDER` fixes their order; `boards()` yields them.

### `figure7_boards.py`

The two boards of Figure 7, copied by hand into ASCII.
The file also documents the one ambiguity of Example 2: cells that are not
drawn in the picture are read as walls.
`FIGURE7_ORDER` fixes their order; `boards()` yields them.

### `gui.py`

The Pygame application.

- `Assets` loads images and fonts.
- `Audio` loads and plays the sounds and the music.
- `SolutionPlayer` replays a solution step by step.
- `draw_*` functions draw the header, board, panel, splash and comparison.
- `run_all_algorithms()` runs the five main algorithms once.
- `make_player()` builds the playback for one algorithm.
- `load_level()` parses a level and prepares everything.
- `main()` contains the event loop, the keys and the buttons.

### `benchmark.py`

Runs BFS, A* h1, A* h2, A* h3 and A* h3+deadlock on the seven boards.
It also runs A* h1+deadlock and A* h2+deadlock to show the effect of the
deadlock filter on the weaker heuristics.
It prints tables and writes `benchmark.csv`.

### `benchmark.csv`

One row per board and per method. The columns are:

| Column | Meaning |
|---|---|
| `board` | board name |
| `method` | algorithm |
| `cost` | number of actions in the solution |
| `expanded` | nodes taken out of OPEN |
| `generated` | nodes created and accepted |
| `closed` | nodes in CLOSED at the end |
| `open_end` | nodes left in OPEN at the end |
| `max_open` | biggest OPEN during the search |
| `heuristic_calls` | calls to the heuristic |
| `deadlock_checks` | calls to `has_deadlock` |
| `status` | `ok`, `LIMIT` or `NO-SOLUTION` |
| `actions` | the complete solution as action words |

### `tests.py`

The automatic checker. It runs without a window
(`SDL_VIDEODRIVER=dummy`) and prints PASS or FAIL for every check.
It covers the levels, the rules, the parser, the heuristics, the deadlocks,
the Figure 4 and Figure 7 boards, the node limit, OPEN/CLOSED and the GUI.

### `main.py`

The smallest demo:

1. parse the default `Level`;
2. run BFS;
3. print the solution, the cost, expanded and generated nodes, OPEN and
   CLOSED sizes, and every state of the path.

### `puzzle.py`

The first, very simple viewer. The final game is `gui.py`; `puzzle.py` is
kept for history and is not used any more.

### `report.md`

The written report: modelling choices, heuristics, deadlock method,
complexity, result tables, comparison and conclusion.

### `README.md`

The quick start: install, run, keys, how to read expanded/generated, file
list.

### `EXPLAIN_LIKE_IM_5.md`

A very short explanation in simple words. This file (`EXPLANATION.md`) is
the long, line-by-line version.

### `assets/`

- `player_up.png`, `player_down.png`, `player_left.png`, `player_right.png`
- `player_directions_sheet.png`
- `box.png`, `target.png`, `wall.png`, `mushroom.png`
- `fonts/` (Silkscreen, Press Start 2P)
- `sounds/` and `pack/` (music and sound effects)

### `SokobanFairyPuzzle.exe`

The Windows executable built with PyInstaller. It contains the Python code,
the assets and a Python runtime, so it can be launched without installing
Python.

### `sfp/`

An empty old build folder. It is not used.

### `__pycache__/`

Python bytecode cache. It is generated automatically and can be deleted.

---

## 3. The model: `boxgame.py`

### 3.1 The symbols

| Symbol | Meaning |
|---|---|
| `O` | wall |
| `R` | player |
| `B` | box |
| `S` | target |
| `.` | player on a target |
| `*` | box on a target |
| space | empty floor |

### 3.2 `SokobanPuzzle.__init__`

```python
def __init__(self, targets, walls, boxes, player, height, width):
    self.targets = frozenset(targets)   # targets never move
    self.walls = frozenset(walls)       # walls never move
    self.boxes = frozenset(boxes)       # boxes move, but a state is immutable
    self.player = player                # one (row, col) tuple
    self.height = height
    self.width = width
```

A state is **immutable**: the sets are `frozenset`, so nobody can modify a
state after it is created. Every move creates a new state. That is important
because the same state object can be stored in OPEN, in CLOSED and in a
solution path without being changed later.

`player` is a tuple `(row, col)`. `boxes`, `targets` and `walls` are sets of
`(row, col)` tuples.

### 3.3 `isInside`

```python
def isInside(self, position):
    row, col = position
    return 0 <= row < self.height and 0 <= col < self.width
```

This prevents the player or a box from leaving the grid. A move that goes
outside is illegal.

### 3.4 `isGoal`

```python
def isGoal(self):
    return self.targets <= self.boxes   # every target holds a box
```

`A <= B` means "every element of A is also in B". So every target must be
in the box set. Because the parser guarantees that the number of boxes
equals the number of targets, this also means that every box is on a target.

### 3.5 `stateKey`

```python
def stateKey(self):
    return (self.player, tuple(sorted(self.boxes)))
```

The key is used by OPEN and CLOSED to recognise the same state.

- `self.player` is already a tuple;
- `sorted(self.boxes)` puts the boxes in a fixed order;
- `tuple(...)` makes the result hashable.

Without sorting, two states with the same boxes in a different set order
could get different keys. With sorting, the key is stable.

### 3.6 `__eq__` and `__hash__`

```python
def __eq__(self, other):
    return self.stateKey() == other.stateKey()

def __hash__(self):
    return hash(self.stateKey())
```

Two states are equal when the player and all boxes are in the same cells.
The hash lets a state be used in a `set` or as a dictionary key.

### 3.7 `successorFunction`

```python
def successorFunction(self):
    successors = []
    for action, (dr, dc) in self.DIRECTIONS.items():
        nxt = (self.player[0] + dr, self.player[1] + dc)

        if not self.isInside(nxt) or nxt in self.walls:
            continue

        new_boxes = set(self.boxes)
        if nxt in self.boxes:                      # push
            dest = (nxt[0] + dr, nxt[1] + dc)
            if (not self.isInside(dest) or dest in self.walls
                    or dest in self.boxes):
                continue
            new_boxes.remove(nxt)
            new_boxes.add(dest)

        successors.append((action, SokobanPuzzle(
            self.targets, self.walls, new_boxes, nxt,
            self.height, self.width)))
    return successors
```

Line by line:

1. Try the four directions: `UP`, `DOWN`, `LEFT`, `RIGHT`.
2. `nxt` is the cell in front of the player.
3. If `nxt` is outside the board or is a wall, the move is illegal.
4. Copy the box set. We never modify the current state.
5. If `nxt` contains a box, this is a push:
   - `dest` is the cell behind the box;
   - if `dest` is outside, a wall, or another box, the push is illegal;
   - otherwise remove the box from `nxt` and add it to `dest`.
6. Create a new `SokobanPuzzle` with the new box set and the new player
   position (`nxt`).
7. Store `(action, new_state)` in the list.

There is no pull, no jump, and the player never lands on a box: in a push,
the player moves into the cell that the box just left.

The branching factor is at most 4, because there are only four directions.

### 3.8 `toGrid` and `__str__`

`toGrid()` rebuilds a 2D list of characters from the state. It is used for
debug printing and by the tests (round-trip of `.`, `*`, etc.).
`__str__` joins the rows with newlines, so `print(state)` shows the board.

### 3.9 `parse_board`

```python
def parse_board(board):
    walls, targets, boxes, player = set(), set(), set(), None
    height, width = len(board), len(board[0])

    for row in board:
        if len(row) != width:
            raise ValueError("All rows must have the same length.")

    for r in range(height):
        for c in range(width):
            s, pos = board[r][c], (r, c)
            if s == "O":
                walls.add(pos)
            elif s == "S":
                targets.add(pos)
            elif s in ("R", "."):
                if player is not None:
                    raise ValueError("There must be only one player.")
                player = pos
                if s == ".":
                    targets.add(pos)
            elif s in ("B", "*"):
                boxes.add(pos)
                if s == "*":
                    targets.add(pos)
            elif s != " ":
                raise ValueError(f"Unknown symbol: {s!r}")

    if player is None:
        raise ValueError("The board must contain a player.")
    if len(boxes) != len(targets):
        raise ValueError("The number of boxes and targets must be equal.")

    return SokobanPuzzle(targets, walls, boxes, player, height, width)
```

What it checks:

1. every row has the same length;
2. exactly one player;
3. there is at least one player;
4. the number of boxes equals the number of targets;
5. only the seven known symbols are accepted.

For `.` the player position is stored and the cell is also added to targets.
For `*` the box position is stored and the cell is also added to targets.

The equal-count check is what makes `isGoal()` simple: if every target is
covered, and there are as many boxes as targets, then every box is on a
target.

### 3.10 `Node`

```python
class Node:
    def __init__(self, state, parent=None, action=None, g=0):
        self.state = state        # the photo
        self.parent = parent      # the previous node
        self.action = action      # the move that produced this node
        self.g = g                # cost from the root to this node
        self.f = g                # f = g + h, set later

    def setF(self, heuristic):
        """Set f = g + h(state) and return it."""
        self.f = self.g + heuristic(self.state)
        return self.f

    def getPath(self):
        path, cur = [], self
        while cur is not None:
            path.append(cur.state)
            cur = cur.parent
        return path[::-1]

    def getSolution(self):
        actions, cur = [], self
        while cur.parent is not None:
            actions.append(cur.action)
            cur = cur.parent
        return actions[::-1]
```

A `Node` is a linked list. Each node remembers:

- the state;
- its parent;
- the action that led to it;
- `g`, the cost from the start;
- `f = g + h`, the A* score.

`setF()` is called for every generated A* node. `getPath()` walks backwards
to the root and reverses the list, so it returns states from start to goal.
`getSolution()` does the same but returns actions.

Because every action costs 1, `g` is also the number of actions, and the
solution length is `goal.g`.

---

## 4. The search tools: OPEN and CLOSED

The course presentation uses two lists:

- **OPEN** = nodes that were generated but not expanded yet. This is the
  frontier.
- **CLOSED** = nodes that were already expanded.

The generic algorithm is:

```
OPEN   <- [root]
CLOSED <- {}

while OPEN is not empty:
    n <- take a node from OPEN
    if n is a goal: return n
    put n in CLOSED
    for every successor c of n:
        if c is new: put c in OPEN
```

The difference between BFS and A* is **which node leaves OPEN**:

- BFS: the oldest node (FIFO queue);
- A*: the node with the smallest `f` (priority queue).

### 4.1 `Closed`

```python
class Closed:
    def __init__(self):
        self.nodes = {}

    def add(self, node):
        self.nodes[node.state.stateKey()] = node

    def get(self, state):
        return self.nodes.get(state.stateKey())

    def remove(self, state):
        del self.nodes[state.stateKey()]

    def contains(self, state):
        return state.stateKey() in self.nodes

    def __contains__(self, state):
        return self.contains(state)

    def __len__(self):
        return len(self.nodes)
```

CLOSED is a dictionary:

- key = state key;
- value = the node that was expanded.

`add()` stores a node, `get()` finds it again, `remove()` is used by A* when
a better path to a closed state is found, and `contains()` answers "was this
state already expanded?".

`__len__` is used by the benchmark to report the CLOSED size.

### 4.2 `OpenFIFO` (BFS)

```python
class OpenFIFO:
    def __init__(self):
        self.queue = deque()
        self.keys = set()           # states waiting in the queue

    def push(self, node):
        self.queue.append(node)
        self.keys.add(node.state.stateKey())

    def pop(self):
        node = self.queue.popleft()
        self.keys.discard(node.state.stateKey())
        return node

    def contains(self, state):
        return state.stateKey() in self.keys

    def __contains__(self, state):
        return self.contains(state)

    def __len__(self):
        return len(self.queue)
```

- `deque` gives O(1) append on the right and O(1) pop on the left.
- `keys` is a set of the state keys currently in the queue. It makes the
  "is this state already in OPEN?" test fast.
- `pop()` removes the node from the queue and from the key set.

FIFO means "first in, first out": the oldest node is expanded first. That is
what makes BFS explore level by level.

### 4.3 `OpenPriority` (A*)

```python
class OpenPriority:
    def __init__(self):
        self.heap = []
        self.live = {}              # state key -> the node that counts
        self.tie = count()

    def push(self, node):
        self.live[node.state.stateKey()] = node
        heappush(self.heap, (node.f, next(self.tie), node))

    def pop(self):
        while self.heap:
            _, _, node = heappop(self.heap)
            key = node.state.stateKey()
            if self.live.get(key) is node:      # skip replaced entries
                del self.live[key]
                return node
        return None

    def get(self, state):
        return self.live.get(state.stateKey())

    def contains(self, state):
        return state.stateKey() in self.live

    def __len__(self):
        return len(self.live)
```

A* needs the smallest `f` first. Python's `heapq` is a min-heap.

Two details:

1. **Tie breaker.** `next(self.tie)` is a unique increasing number. If two
   nodes have the same `f`, the heap compares this number instead of the
   `Node` object (which cannot be compared). It also makes the order stable.
2. **Lazy deletion.** When a better path to a state is found, a new node is
   pushed and `live[key]` points to it. The old entry stays in the heap.
   When `pop()` takes the old entry, `live.get(key) is node` is false, so it
   is skipped. The heap can contain stale entries, but `len(open_list)` uses
   `live`, so the reported OPEN size counts only live nodes.

`push()` is O(log N), `pop()` is O(log N) amortised (each stale entry is
removed once), and `get()` / `contains()` are average O(1) after the state
key is computed.

---

## 5. Deadlocks

### 5.1 What is a deadlock?

A deadlock is a state from which the puzzle can never be solved. The boxes
are stuck in a configuration that cannot reach a goal.

If the search keeps exploring a deadlocked state, it wastes time. The goal
of the deadlock detector is to recognise those states and throw them away
**before** they fill OPEN.

The assignment defines two kinds:

1. **corner deadlock** (red cells in Figure 5);
2. **line deadlock** (yellow cells in Figure 6).

### 5.2 Corner deadlock

A cell is a corner deadlock when:

- it is not a wall;
- it is not a target;
- it has at least one wall above or below;
- it has at least one wall left or right.

The two walls are perpendicular, so they form a corner.

Why is a box there trapped? A box can only move when the player stands on
the opposite side and pushes. With a wall above (or below) and a wall on the
left (or right), two of the four push directions are impossible. For the
other two directions, the player would have to stand in one of those same
walls, so they are impossible too. The box can never leave the cell.

A **target** cell is never added. If a box is on a target, it is already
where it should be. A box on a corner target is not a deadlock.

```python
for row in range(state.height):
    for col in range(state.width):
        pos = (row, col)
        if pos in walls or pos in targets:
            continue                    # a target is never dead
        vertical = (row - 1, col) in walls or (row + 1, col) in walls
        horizontal = (row, col - 1) in walls or (row, col + 1) in walls
        if vertical and horizontal:
            corners.add(pos)            # one wall on each axis = corner
```

Example: on Figure 7 / Example 1, the red cells are
`(1,2) (1,4) (1,5) (5,2) (5,4) (5,5)`.

### 5.3 Line deadlock

A line deadlock connects two corner deadlocks that are on the same row or on
the same column. The whole segment between them becomes dead when:

1. there is at least one cell between the two corners (the segment has at
   least 3 cells);
2. no cell of the segment is a wall;
3. no cell of the segment is a target;
4. at least one of the two parallel sides of the segment is entirely wall.

Why does this work? A box on the segment cannot be pushed perpendicular to
the segment:

- to push it away from the wall, the player would have to stand **on** the
  wall side, which is impossible;
- to push it into the wall, the destination is a wall, which is impossible.

So the box can only be pushed along the segment. Both ends of the segment
are corner deadlocks, so wherever the box stops on the line, it is trapped.

The condition "no target on the line" is important: if a target is on the
line, a box on that target is not dead. The condition "no wall on the line"
is also important: a wall would break the segment into two independent
pieces.

```python
def dead_line(a, b, walls, targets):
    if a[0] == b[0]:                        # same row: horizontal line
        cells = [(a[0], col) for col in range(a[1], b[1] + 1)]
        sides = [(-1, 0), (1, 0)]           # above and below
    elif a[1] == b[1]:                      # same column: vertical line
        cells = [(row, a[1]) for row in range(a[0], b[0] + 1)]
        sides = [(0, -1), (0, 1)]           # left and right
    else:
        return set()                        # corners are not aligned

    if len(cells) < 3:
        return set()                        # need one empty cell between them
    if any(p in walls or p in targets for p in cells):
        return set()                        # a wall or target breaks the line
    for dr, dc in sides:
        if all((r + dr, c + dc) in walls for r, c in cells):
            return set(cells)               # one full wall side = trapped
    return set()
```

The `cells` list is the whole segment, including the two corner cells.
`sides` contains the two directions perpendicular to the segment.

Example: on Figure 7 / Example 1, the yellow line cells are
`(2,5) (3,5) (4,5)`. They connect the corner `(1,5)` to the corner `(5,5)`,
and the right side of the column is the outer wall.

### 5.4 `dead_cells`

```python
def dead_cells(state):
    walls, targets = state.walls, state.targets
    corners = set()
    for row in range(state.height):
        for col in range(state.width):
            pos = (row, col)
            if pos in walls or pos in targets:
                continue                    # a target is never dead
            vertical = (row - 1, col) in walls or (row + 1, col) in walls
            horizontal = (row, col - 1) in walls or (row, col + 1) in walls
            if vertical and horizontal:
                corners.add(pos)            # one wall on each axis = corner

    dead = set(corners)
    for a in corners:
        for b in corners:
            if a < b:                       # each pair once
                dead |= dead_line(a, b, walls, targets)
    return frozenset(dead)
```

Steps:

1. scan every cell;
2. skip walls and targets;
3. collect the corner cells;
4. start `dead` with all corners;
5. for every pair of corners `a, b` with `a < b`, try to build a dead line;
6. add the line cells to `dead`;
7. return a `frozenset`, so the result can be reused without being changed.

This function is called **once per level** by A* or by the GUI. It does not
depend on the player or on the boxes, only on the walls and targets, so the
same set is valid for every state of that level.

### 5.5 `has_deadlock`

```python
def has_deadlock(state, dead=None):
    if dead is None:
        dead = dead_cells(state)            # compute once if not given
    return any(box in dead and box not in state.targets
               for box in state.boxes)      # box on a target is fine
```

It returns `True` when at least one box is on a dead cell **and** that cell
is not a target.

The `dead=None` parameter lets the caller compute the set once and pass it
to every call. A* does exactly that:

```python
if use_deadlock and dead is None:
    dead = dead_cells(initial_state)    # one set for the whole search
```

### 5.6 The dead cells of the two Figure 7 boards

| Board | Corner cells (red) | Line cells (yellow) |
|---|---|---|
| Figure 7 / Example 1 | `(1,2) (1,4) (1,5) (5,2) (5,4) (5,5)` | `(2,5) (3,5) (4,5)` |
| Figure 7 / Example 2 | `(1,4) (2,6) (3,1) (4,4) (4,6)` | `(3,6) (4,5)` |

The tests check every red cell, every yellow cell, and the exact union: no
extra dead cell is allowed. They also check the negative case:

```
a box on a corner target is NOT a deadlock
```

Example 1 start state is not deadlocked. Example 2 start state is not
deadlocked either. The detector only fires after a bad push.

### 5.7 Integration in A*

`astar(..., use_deadlock=False)` keeps the old behaviour.

With `use_deadlock=True`:

1. the dead set is computed once from the initial state;
2. the root is checked before the loop;
3. every generated child is checked before it is pushed into OPEN;
4. a deadlocked child is discarded.

```python
if use_deadlock:
    deadlock_checks += 1
    if has_deadlock(child_state, dead):
        continue                # box on a dead cell: doomed
```

The filter only removes states that cannot reach a goal. It never removes a
state that could still be part of an optimal solution, so the optimal cost is
unchanged.

The switch is kept so the benchmark can compare the same heuristic with and
without the filter.

### 5.8 Complexity of the deadlock detector

Let:

- `H*W` = number of cells;
- `C` = number of corner cells;
- `L` = length of the longest line;
- `B` = number of boxes.

| Function | Time | Space |
|---|---|---|
| `dead_cells` | O(H*W + C^2 * L) | O(H*W) |
| `dead_line` | O(L) | O(L) |
| `has_deadlock` | O(B) | O(1) |

The set is built once per level. The check is one lookup per box.

### 5.9 Limits of this detector

This is the detector required by the assignment: corners and lines. It does
not detect every possible deadlock. For example:

- a 2x2 block of boxes that can never be separated;
- a box that is not in a corner but is blocked by another box forever;
- a freeze deadlock created by several boxes together.

Those cases are not in the Figure 5/6 definitions, so they are not
implemented. The detector is a safe filter: when it says "dead", the state
really is dead. When it says "not dead", the state may still be dead for a
more complicated reason, and the search will simply explore it.

---

## 6. Breadth-first search

### 6.1 The code

```python
def bfs(initial_state, stats=None, node_limit=DEFAULT_NODE_LIMIT):
    root = Node(initial_state)
    open_list, closed = OpenFIFO(), Closed()    # frontier + visited states
    open_list.push(root)
    generated, expanded, max_open = 1, 0, 1     # root is generated
    limit_reached = False
    goal = None

    while len(open_list) > 0:
        if node_limit is not None and expanded >= node_limit:
            limit_reached = True                # stop instead of running forever
            break

        node = open_list.pop()                  # FIFO: oldest node first
        expanded += 1

        if node.state.isGoal():                 # goal test on expansion
            goal = node
            break

        closed.add(node)
        for action, child_state in node.state.successorFunction():
            if child_state in open_list or child_state in closed:
                continue                        # state already seen
            open_list.push(Node(child_state, node, action, node.g + 1))
            generated += 1
        max_open = max(max_open, len(open_list))

    if stats is not None:
        stats.update(generated=generated, limit_reached=limit_reached,
                     open_size=len(open_list), closed_size=len(closed),
                     max_open=max_open)
    return goal, expanded
```

### 6.2 Step by step

1. Create the root node from the start state.
2. Put it in OPEN.
3. `generated = 1` because the root was generated.
4. `expanded = 0` because nothing has been expanded yet.
5. While OPEN is not empty:
   - if the node limit is reached, stop and flag it;
   - pop the oldest node;
   - increment `expanded`;
   - if it is a goal, return it;
   - put it in CLOSED;
   - for every successor:
     - if it is already in OPEN or CLOSED, skip it;
     - otherwise create a child with `g = parent.g + 1`;
     - push it into OPEN;
     - increment `generated`.
6. Return `(goal, expanded)`, and fill `stats` if a dict was given.

### 6.3 Why BFS is optimal

All actions cost 1. BFS expands all states at distance 0, then all states at
distance 1, then all states at distance 2, and so on. The first goal it pops
is therefore at the smallest possible distance. Its cost is the minimum.

### 6.4 The counters

- **expanded**: number of nodes popped from OPEN and processed.
- **generated**: number of nodes created and accepted. The root counts as 1.
- **open_size**: nodes left in OPEN at the end.
- **closed_size**: nodes in CLOSED at the end.
- **max_open**: maximum size of OPEN during the search. It measures the
  memory pressure.

### 6.5 The node limit

`DEFAULT_NODE_LIMIT = 400000`.

The limit is a number of **expansions**, not seconds. If a search is too big,
it stops at exactly 400000 expanded nodes and reports `limit_reached = True`.
The benchmark writes `LIMIT` in that case. The GUI shows `LIMIT REACHED`.

There is no timeout anywhere in the solver. This is deliberate: results do
not depend on the speed of the machine.

### 6.6 Complexity

BFS is O(b^d) in time and O(b^d) in space in the worst case, where:

- `b` is the branching factor (at most 4);
- `d` is the depth of the solution in actions.

More precisely, if `V` is the number of reachable states and `E` the number
of transitions, BFS is O(V + E) graph work. Each state is expanded at most
once thanks to CLOSED.

Each expansion also computes up to four successors, and each state key sorts
the boxes: O(B log B) per key. So the practical cost is about
O(V * B log B), with O(V) memory for OPEN and CLOSED.

---

## 7. The heuristics h1, h2 and h3

A heuristic `h(state)` estimates how many actions are still needed to reach
a goal. In A*, the score of a node is:

```
f = g + h
```

- `g` = actions already done;
- `h` = estimated actions remaining.

A heuristic is **admissible** when it never overestimates the true remaining
cost. With an admissible heuristic, A* is optimal.

### 7.1 h1: misplaced boxes

```python
def h1(state):
    return len(state.boxes - state.targets)     # misplaced boxes
```

`state.boxes - state.targets` is the set of boxes that are not on a target.
Each such box needs at least one push to reach a target, so h1 is a lower
bound. It is admissible.

It is weak: it ignores distance and the player position. On a board where a
box is two cells from its target, h1 = 1 but the true cost is 2.

### 7.2 h2: distance sum with a penalty

```python
def h2(state):
    misplaced = len(state.boxes - state.targets)
    distances = 0
    for box in state.boxes:
        distances += min(abs(box[0] - t[0]) + abs(box[1] - t[1])
                         for t in state.targets)  # nearest target, walls ignored
    return 2 * misplaced + distances            # the 2x makes h2 inadmissible
```

The distance part is a lower bound: a box needs at least one push per
Manhattan unit (walls can only make the real distance larger, never smaller).

The `2 * misplaced` part is an extra penalty. It is not justified by a
lower-bound argument. On the small board

```
OOOOO
OS BR
OOOOO
```

the true optimum is 2, but h2 = 4. So h2 is **inadmissible**. It can guide
the search faster on some boards, but it has no optimality guarantee.

### 7.3 h3: real push distances plus the player walk

h3 is the strongest heuristic of the project. It has two parts.

#### Part 1: real push distances

The old version used Manhattan distance. Manhattan distance lets a box fly
over walls, which is not possible in Sokoban. The new version computes the
real number of pushes needed to move a box to a target, with the walls taken
into account.

```python
push_tables = {}

def push_distances(state):
    key = (state.walls, state.targets)
    if key in push_tables:
        return push_tables[key]             # same board: reuse the tables

    tables = {}
    for target in state.targets:
        dist = {target: 0}
        queue = deque([target])             # reverse search: target -> cells
        while queue:
            row, col = queue.popleft()
            for dr, dc in state.DIRECTIONS.values():
                box = (row - dr, col - dc)      # box before the push
                player = (row - 2 * dr, col - 2 * dc)  # player behind it
                if box in dist or not state.isInside(player):
                    continue
                if box in state.walls or player in state.walls:
                    continue
                dist[box] = dist[(row, col)] + 1
                queue.append(box)
        tables[target] = dist
    push_tables[key] = tables
    return tables
```

How the reverse search works:

- Start at the target with distance 0.
- Suppose the box is now at `(row, col)`.
- To have pushed it there with direction `(dr, dc)`, the box was at
  `(row - dr, col - dc)` and the player was at `(row - 2*dr, col - 2*dc)`.
- If the player and the previous box cell are not walls, then the box can be
  pushed from `box` to `(row, col)` in one push.
- Store `dist[box] = dist[(row, col)] + 1` and continue from `box`.

The result is a table, for each target, that gives the minimum number of
pushes from every cell to that target. It ignores the other boxes and
whether the player can actually reach the pushing position; that makes it a
**lower bound**, which is exactly what an admissible heuristic needs.

The table is cached by `(walls, targets)`, so it is computed once per board,
not once per state.

#### Part 2: one-to-one matching

Each box must end on a different target. Taking, for each box, the nearest
target can assign two boxes to the same target. The code solves the real
assignment problem with dynamic programming.

```python
def cheapest_assignment(costs):
    size = len(costs)
    best = {0: 0}                   # mask 0 = no target used yet
    for box in range(size):
        following = {}
        for used, total in best.items():
            for target in range(size):
                if used >> target & 1:
                    continue        # target already taken by another box
                new_used = used | 1 << target
                new_total = total + costs[box][target]
                if new_total < following.get(new_used, float("inf")):
                    following[new_used] = new_total
        best = following
    return best[(1 << size) - 1]    # mask with every target used
```

- `used` is a bit mask. Bit `i` is 1 when target `i` already has a box.
- `best[used]` is the cheapest total cost for the boxes processed so far.
- For each new box, try every target that is still free.
- Keep the cheapest total for each new mask.
- At the end, `(1 << size) - 1` is the mask with all targets used.

This is exact: it tries all assignments, but with dynamic programming, so it
does not try the same partial assignment twice.

#### Part 3: the player walk

```python
def h3(state):
    tables = push_distances(state)      # cached: computed once per board
    boxes = list(state.boxes)
    targets = list(state.targets)
    costs = [[tables[t].get(b, UNREACHABLE) for t in targets] for b in boxes]
    pushes = cheapest_assignment(costs) # every box gets a different target

    misplaced = [b for b in boxes if b not in state.targets]
    if not misplaced:
        return pushes
    row, col = state.player
    walk = min(abs(row - b[0]) + abs(col - b[1]) for b in misplaced) - 1
    return pushes + max(walk, 0)        # pushes + walk to the first box
```

The player must first walk to a box before pushing it. The Manhattan
distance from the player to the nearest misplaced box, minus 1 (being
adjacent is enough to push), is a lower bound on the walking actions before
the first push. It is floored at 0.

Why can we add the walk to the pushes? Because they count different actions:

- the push tables count pushes;
- the walk counts the moves before the first push.

The two parts do not overlap, so the sum is still a lower bound.

`UNREACHABLE = 1000` is used when a box cannot be pushed to a target at all.
It is larger than any real solution cost on these boards, so it acts like
infinity and makes that assignment very expensive. On a board whose optimal
solution needs more than 1000 pushes, this constant could overestimate and
break admissibility; the project boards are far below that limit.

#### h3 on the Figure 7 start states

| Board | h1 | h2 | h3 | true cost |
|---|---|---|---|---|
| Figure 7 / Example 1 | 3 | 17 | 16 | 41 |
| Figure 7 / Example 2 | 4 | 19 | 17 | 55 |

h3 is much closer to the true cost than h1. h2 is also close, but it is
inadmissible.

#### h3 complexity

| Part | Time | Space | When |
|---|---|---|---|
| `push_distances` | O(T * H * W) | O(T * H * W) | once per board, cached |
| `cheapest_assignment` | O(B^2 * 2^B) | O(2^B) | every h3 call |
| player walk | O(B) | O(1) | every h3 call |

For the project boards, `B` is at most 4, so `2^B` is at most 16. The
factorial/bitmask cost is tiny. For a board with many boxes, this DP would
become expensive, and the code would need a different matching method.

---

## 8. A*

### 8.1 `SearchResult`

```python
class SearchResult(tuple):
    """(goal_node, expanded) plus the other counters."""

    def __new__(cls, goal_node, expanded, generated=0, limit_reached=False,
                heuristic_calls=0, deadlock_checks=0, open_size=0,
                closed_size=0, max_open=0):
        result = super().__new__(cls, (goal_node, expanded))
        result.generated = generated
        result.limit_reached = limit_reached
        result.heuristic_calls = heuristic_calls
        result.deadlock_checks = deadlock_checks
        result.open_size = open_size        # nodes left in OPEN at the end
        result.closed_size = closed_size    # nodes in CLOSED at the end
        result.max_open = max_open          # biggest OPEN during the search
        return result

    @property
    def goal(self):
        return self[0]

    @property
    def expanded(self):
        return self[1]

    @property
    def cost(self):
        return self[0].g if self[0] is not None else None
```

`SearchResult` is a tuple of two values, so old code can still write:

```python
goal, expanded = astar(...)
```

It also carries extra attributes:

- `generated`
- `limit_reached`
- `heuristic_calls`
- `deadlock_checks`
- `open_size`
- `closed_size`
- `max_open`

And three read-only properties: `goal`, `expanded`, `cost`.

### 8.2 The code

```python
def astar(initial_state, heuristic=h1, node_limit=DEFAULT_NODE_LIMIT,
          use_deadlock=False, dead=None):
    if use_deadlock and dead is None:
        dead = dead_cells(initial_state)    # one set for the whole search

    root = Node(initial_state)
    root.setF(heuristic)
    heuristic_calls = 1
    deadlock_checks = 0
    open_list, closed = OpenPriority(), Closed()

    def result(goal, expanded, generated, limit):
        return SearchResult(goal, expanded, generated, limit, heuristic_calls,
                            deadlock_checks, len(open_list), len(closed),
                            max_open)

    max_open = 1
    if use_deadlock:
        deadlock_checks += 1
        if has_deadlock(root.state, dead):
            return result(None, 0, 1, False)  # start state is already lost

    open_list.push(root)
    expanded, generated = 0, 1

    while len(open_list) > 0:
        if node_limit is not None and expanded >= node_limit:
            return result(None, expanded, generated, True)

        node = open_list.pop()              # smallest f first
        expanded += 1

        if node.state.isGoal():             # goal test on expansion
            return result(node, expanded, generated, False)

        closed.add(node)
        for action, child_state in node.state.successorFunction():
            child_g = node.g + 1

            old = open_list.get(child_state)
            if old is None:
                old = closed.get(child_state)
            if old is not None and old.g <= child_g:
                continue                    # a path at least as good exists

            if use_deadlock:
                deadlock_checks += 1
                if has_deadlock(child_state, dead):
                    continue                # box on a dead cell: doomed

            if closed.contains(child_state):
                closed.remove(child_state)  # reopen with the better g
            child = Node(child_state, node, action, child_g)
            child.setF(heuristic)
            heuristic_calls += 1
            generated += 1
            open_list.push(child)
        max_open = max(max_open, len(open_list))

    return result(None, expanded, generated, False)
```

### 8.3 Step by step

1. If the deadlock filter is on and no dead set was given, compute it once.
2. Create the root, set `f = g + h`.
3. `heuristic_calls = 1` for the root.
4. Create OPEN (priority queue) and CLOSED.
5. If the filter is on, check the root.
6. Push the root.
7. While OPEN is not empty:
   - if the node limit is reached, return `limit_reached = True`;
   - pop the node with the smallest `f`;
   - increment `expanded`;
   - if it is a goal, return it;
   - put it in CLOSED;
   - for every successor:
     - `child_g = node.g + 1`;
     - look for the same state in OPEN, then in CLOSED;
     - if a known path is at least as good, skip this child;
     - if the filter is on, count a check and skip dead children;
     - if the state is in CLOSED, remove it (reopen);
     - create the child, compute its `f`, increment the counters, push it.
8. If OPEN becomes empty, return no solution.

### 8.4 Why the "old.g <= child_g" test?

Suppose the same state can be reached by two paths. The one with the smaller
`g` is better, because it has done fewer actions. If the new path is not
strictly better, there is no reason to keep it.

If the state is in OPEN with a better `g`, skip the new child. If it is in
CLOSED with a better `g`, skip the new child too. If the new path is better,
update OPEN or reopen CLOSED.

Reopening is needed when the heuristic is not consistent. h2 can be
inadmissible, so a state that was expanded early with a bad path may need to
be expanded again with a better path. The code handles that.

### 8.5 Goal test

The goal test is done when a node is **expanded**, not when it is generated.
This is the classic version from the course. With A* and an admissible
heuristic, the first goal popped from OPEN has the optimal cost.

### 8.6 The deadlock switch

`use_deadlock=False`:

- no dead set is built;
- `deadlock_checks` stays 0;
- A* behaves exactly like before.

`use_deadlock=True`:

- the dead set is built once;
- the root is checked;
- every child is checked;
- `deadlock_checks` counts the root plus every checked child.

The filter is safe: it only removes states with a box on a dead cell that is
not a target, and those states can never reach a goal.

### 8.7 A tiny A* example

Board:

```
OOOOO
OS BR
OOOOO
```

The player is at `(1,4)`, the box at `(1,3)`, the target at `(1,1)`.

- h1 = 1 (the box is misplaced)
- h2 = 2*1 + 2 = 4
- h3 = 2 (two pushes: left, left)
- true optimum = 2

A* with h1 gives the box a score of `g + 1`. A* with h3 gives `g + 2`, which
matches the true remaining cost. A better estimate means fewer nodes to try.

### 8.8 A* complexity

Worst case: O(b^d) time and O(b^d) space, like BFS. The heuristic does not
change the worst-case bound; it changes the number of nodes expanded in
practice.

With a consistent heuristic, each state is expanded once. With h2
(inadmissible), a state can be reopened, so the number of expansions can be
larger. OPEN operations are O(log N); CLOSED operations are average O(1)
after the state key is computed.

---

## 9. Complexity

### 9.1 Notation

| Symbol | Meaning |
|---|---|
| `H`, `W` | board height and width |
| `V` | number of reachable states |
| `E` | number of transitions between states |
| `b` | branching factor (at most 4) |
| `d` | solution depth in actions |
| `B` | number of boxes |
| `T` | number of targets |
| `C` | number of corner cells |
| `L` | length of the longest line |
| `N` | number of nodes in OPEN |

### 9.2 Per function

| Function | Time | Space |
|---|---|---|
| `parse_board` | O(H*W) | O(H*W) |
| `SokobanPuzzle.successorFunction` | O(B) (copy the box set, up to 4 moves) | O(B) per child |
| `SokobanPuzzle.stateKey` | O(B log B) (sort the boxes) | O(B) |
| `SokobanPuzzle.isGoal` | O(T) | O(1) |
| `Node.setF` | O(h) | O(1) |
| `Node.getPath`, `Node.getSolution` | O(d) | O(d) |
| `Closed.add/get/remove/contains` | average O(1) after the key, key is O(B log B) | O(V) |
| `OpenFIFO.push/pop` | O(1) | O(V) |
| `OpenPriority.push/pop` | O(log N) | O(N) (including stale entries) |
| `dead_cells` | O(H*W + C^2 * L) | O(H*W) |
| `dead_line` | O(L) | O(L) |
| `has_deadlock` | O(B) | O(1) |
| `bfs` | O(V + E), worst O(b^d) | O(V), worst O(b^d) |
| `h1` | O(B) | O(1) |
| `h2` | O(B*T) | O(1) |
| `push_distances` | O(T*H*W) once per board | O(T*H*W) |
| `cheapest_assignment` | O(B^2 * 2^B) | O(2^B) |
| `h3` | O(B*T + B^2 * 2^B) per state, plus the first call | O(2^B) |
| `astar` | O(b^d) worst | O(b^d) worst |
| `run_all_algorithms` (GUI) | 5 searches per level | 5 results |

### 9.3 BFS vs A*

| | BFS | A* |
|---|---|---|
| OPEN | FIFO queue | min-heap on `f` |
| Order | by depth | by estimated total cost |
| Optimal | yes, with unit costs | yes, with an admissible heuristic |
| Worst time | O(b^d) | O(b^d) |
| Worst space | O(b^d) | O(b^d) |
| Uses a heuristic | no | yes |
| Typical effect | explores many nodes | explores fewer nodes |

A* is not automatically faster in the worst case. It is faster when the
heuristic is informative. On these boards, h3 is much more informative than
h1 or h2, and the deadlock filter removes doomed states.

### 9.4 Complexity of the deadlock filter

Building the dead set:

```
O(H*W)        scan every cell
+ O(C^2 * L)  test every pair of corners
```

Checking a state:

```
O(B)          one lookup per box
```

Memory:

```
O(H*W)        the dead set
```

The set is built once per level. The filter is cheap compared to the search.

### 9.5 Practical sizes

On the project boards:

- `H*W` is at most 9x9 = 81;
- `B` is at most 4;
- `T` is at most 4;
- `2^B` is at most 16;
- the branching factor is at most 4.

The exponential parts are therefore small. The real cost is the number of
states explored, which is why the counters (expanded and generated) are the
important measurements.

---

## 10. Benchmark and results

### 10.1 What the benchmark does

`benchmark.py` runs seven methods on seven boards:

Main five:

1. BFS;
2. A* h1;
3. A* h2;
4. A* h3;
5. A* h3+deadlock.

Two extra runs, to show the filter with weaker heuristics:

6. A* h1+deadlock;
7. A* h2+deadlock.

For every run it records:

- cost;
- expanded;
- generated;
- CLOSED size at the end;
- OPEN size at the end;
- maximum OPEN size;
- heuristic calls;
- deadlock checks;
- status;
- the full action list.

The node limit is 400000 expansions. Status is:

- `ok` if a goal was found;
- `LIMIT` if the limit was reached;
- `NO-SOLUTION` if OPEN became empty.

There are no seconds anywhere.

### 10.2 Expanded nodes (current code)

| Board | BFS | A* h1 | A* h2 | A* h3 | A* h3+deadlock |
|---|---|---|---|---|---|
| Fig. 4 Example 1 | 15 | 12 | 9 | **6** | **6** |
| Fig. 4 Example 2 | 1162 | 1106 | 749 | 196 | **196** |
| Fig. 4 Example 3 | 2560 | 2489 | 1443 | 353 | **353** |
| Fig. 4 Example 4 | 6665 | 5476 | 3098 | 878 | **878** |
| Fig. 4 Example 5 | 9430 | 7337 | 2128 | 716 | **716** |
| Fig. 7 Example 1 | 2345 | 2313 | 2242 | 1023 | **1023** |
| Fig. 7 Example 2 | 54841 | 54671 | 49811 | 5334 | **5334** |

The lowest value of each row is in bold. `h3` and `h3+deadlock` tie on
expanded nodes because h3 already gives dead states a huge `f`: they stay at
the end of OPEN and are usually never expanded. The filter still prevents
them from being generated.

### 10.3 Totals over the seven boards

| Method | Expanded | Generated |
|---|---|---|
| BFS | 77018 | 78893 |
| A* h1 | 73404 | 75330 |
| A* h2 | 59480 | 62618 |
| A* h3 | 8506 | 10388 |
| A* h3+deadlock | **8506** | **9384** |

The heuristic calls and deadlock checks are still recorded in
`benchmark.csv`; they are no longer part of the comparison display.

h3 expands **89.0% fewer** nodes than BFS (77018 -> 8506).

The deadlock filter does not reduce h3's expanded count on these boards, but
it reduces generated nodes by **9.7%** (10388 -> 9384). It also reduces the
maximum OPEN size, which means less memory.

### 10.4 Effect of the deadlock filter on the weaker heuristics

| Heuristic | Without filter | With filter | Reduction |
|---|---|---|---|
| h1 | 73404 | 12640 | 82.8% |
| h2 | 59480 | 9665 | 83.8% |
| h3 | 8506 | 8506 | 0.0% |

This table is the clearest proof that the deadlock filter works. With a weak
heuristic, the search generates many dead states; the filter removes them
and the search becomes much smaller. With the strong h3, the heuristic
already keeps dead states at the end of OPEN, so the expanded count is
unchanged, but the filter still saves generated nodes.

### 10.5 Figure 7 in detail

#### Example 1 (7x7)

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

#### Example 2 (8x6)

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

Example 2 is the hardest board. h3 expands 90.3% fewer nodes than BFS
(54841 -> 5334). The deadlock filter reduces generated nodes by 11.7%
(6367 -> 5622).

### 10.6 How to read expanded vs generated

- **Expanded**: a node was taken out of OPEN and processed. This is the real
  work of the search: generate its children, test the goal, put it in
  CLOSED.
- **Generated**: a node was created and accepted into OPEN. It may be
  expanded later, or it may stay in OPEN when the goal is found.

A node is generated when it is discovered. It is expanded when the search
actually looks at it. Expanded is usually the more important number for
comparing algorithms, because it counts the states the algorithm really
processed. Generated is useful to see the memory pressure and the effect of
pruning: the deadlock filter removes children before they are generated.

### 10.7 Status

All 49 runs of the current benchmark have status `ok`. No limit was reached
and no search failed.

The limit path is still tested on purpose: the tests run a search with
`node_limit=1` and check that it reports `limit_reached` and no solution.
The GUI also shows `LIMIT REACHED` in that case.

---

## 11. The GUI

### 11.1 Files and functions

`gui.py` contains:

| Part | What it does |
|---|---|
| `Assets` | loads images and fonts |
| `Audio` | loads and plays sounds/music |
| `SolutionPlayer` | replays a solution step by step |
| `Button`, `build_buttons` | creates the side-panel buttons |
| `draw_header` | title and level number |
| `draw_floor_and_walls` | draws the board background |
| `draw_decorations` | mushrooms and other decorations |
| `draw_targets` | target sprites |
| `draw_boxes` | box sprites |
| `draw_player` | player sprite with facing direction |
| `draw_board` | puts the board together |
| `draw_panel` | side panel: level, algorithm, step, cost, status, expanded, generated |
| `draw_status_message` | "PUZZLE SOLVED", "NO SOLUTION", "LIMIT REACHED" |
| `draw_splash` | "Solving with 5 algorithms ..." |
| `draw_comparison` | the comparison screen |
| `short_label` | short names for the bar charts |
| `run_all_algorithms` | runs the five main algorithms once |
| `make_player` | builds the playback for one cached result |
| `load_level` | parses a level and prepares the five results |
| `main` | event loop, keys, buttons, fullscreen |

### 11.2 What happens when a level is loaded

1. `parse_board` reads the ASCII level.
2. `run_all_algorithms` runs:
   - BFS;
   - A* h1;
   - A* h2;
   - A* h3;
   - A* h3+deadlock.
3. Every result is stored in a list with its label, theory, counters and
   goal.
4. `make_player` builds the playback for the selected algorithm.
5. The splash is displayed while the searches run, so the window does not
   freeze.
6. The result is cached. Pressing `A` only switches to another cached
   result; it does not run a new search.

### 11.3 The side panel

The panel shows:

- `LEVEL`: current level / 13;
- `ALGORITHM`: BFS, A* h1, A* h2, A* h3 or A* h3+deadlock;
- `STEP`: current replay step / total;
- `SOLUTION COST`: number of actions;
- `STATUS`: READY, SOLVING, PLAYING, PAUSED, SOLVED, NO SOLUTION or
  LIMIT REACHED;
- `EXPANDED NODES`;
- `GENERATED NODES`.

### 11.4 The comparison screen

Press `C` to open it. It shows a table:

| Column | Meaning |
|---|---|
| ALGORITHM | name |
| COMPLEXITY | theoretical time complexity |
| COST | number of actions in the solution |
| EXPANDED | expanded nodes |
| GENERATED | generated nodes |

Below the table there are two horizontal bar charts:

- expanded nodes;
- generated nodes.

Each bar is scaled to the largest value of its chart and labelled with the
number. The best algorithm (fewest expanded nodes) is highlighted in gold.
If a run reached the node limit, the text `limit reached` is shown instead
of a bar.

The screen is drawn by `draw_comparison` and does not create a new window.

### 11.5 Keys

| Key | Action |
|---|---|
| `SPACE` | play / pause |
| `R` | restart |
| `<` / `>` | previous / next step |
| `-` / `+` | slower / faster |
| `[` / `]` | previous / next level |
| `1` ... `9` | jump to a level |
| `A` | next algorithm |
| `C` | open / close comparison |
| `F11` or `F` | fullscreen |
| `ESC` | close comparison, or quit |

The buttons in the panel do the same actions with the mouse.

### 11.6 The algorithm picker

`choose_algorithm`:

```python
def choose_algorithm(new_index):
    """Use another cached algorithm for playback, without a new search."""
    nonlocal algorithm_index, player, decorations
    algorithm_index = new_index % len(ALGORITHMS)
    player = make_player(puzzle, results, algorithm_index, delay)
    decorations = pick_decorations(puzzle, player.path)
    sfx("click")
```

It wraps around with `%`, rebuilds the playback from the cached result, and
plays a click sound. No search is repeated.

### 11.7 The comparison caching

`load_level` returns:

```python
return (puzzle, player, pick_decorations(puzzle, player.path), results)
```

The four values are:

1. the parsed puzzle;
2. the playback for the selected algorithm;
3. the decorations;
4. the five cached results.

`main` keeps `results` and passes it to `draw_comparison`. This is why the
comparison screen opens instantly.

---

## 12. The tests

`tests.py` runs headless automatically:

```
python tests.py
```

The file sets `SDL_VIDEODRIVER=dummy` itself, so no window opens. There is
also an optional `python tests.py --real` mode that opens a real window for
the fullscreen checks.

The sections are:

| Section | What it checks |
|---|---|
| 1 | levels are ordered from easy to hard; 13 levels; every level has a solution |
| 2 | speed controls really speed up and clamp at the ends |
| 3 | sound effects fire on the right actions |
| 4 | WAV assets load |
| 5 | window and fullscreen geometry |
| 6 | the frame renders with the new header |
| 7 | successor rules: pushes, walls, boxes, no pull, no jump |
| 8 | `isGoal` accepts any box on any target |
| 9 | `Node.setF`, `getPath`, `getSolution` |
| 10 | h1, h2, h3 on a hand-built board; h2 is inadmissible |
| 11 | A* vs BFS, `SearchResult`, node limits, no-solution |
| 12 | deadlock cells match the red/yellow cells of Figures 5-6 |
| 12b | Figure 4 sizes and optimal costs |
| 13 | Figure 7 boards validate and solve |
| 14 | GUI algorithm picker and comparison screen |
| 15 | OPEN and CLOSED lists |

The last line is:

```
ALL TESTS PASSED  (0 failed)
```

The tests do not measure seconds. They check exact costs, exact dead cells,
counters, limits and rendering.

---

## 13. How to run everything

Install Pygame:

```
pip install pygame
```

Play the game:

```
python gui.py
```

Run the tests:

```
python tests.py
```

Run the benchmark:

```
python benchmark.py
```

Run the tiny console demo:

```
python main.py
```

The old viewer (not used by the final game):

```
python puzzle.py
```

The packaged game:

```
SokobanFairyPuzzle.exe
```

---

## 14. Small glossary

| Word | Meaning |
|---|---|
| **state** | player position + box positions |
| **action** | one move: up, down, left or right |
| **goal** | every target holds a box |
| **successor** | a state reachable by one legal action |
| **search tree** | the graph of states explored by the algorithm |
| **OPEN** | frontier: generated but not expanded |
| **CLOSED** | expanded states |
| **expanded** | node taken out of OPEN and processed |
| **generated** | node created and accepted into OPEN |
| **heuristic** | estimate of the remaining cost |
| **admissible** | never overestimates the true cost |
| **deadlock** | state from which no goal can be reached |
| **corner deadlock** | box trapped in a corner |
| **line deadlock** | box trapped on a line between two corners |
| **BFS** | breadth-first search |
| **A*** | best-first search with `f = g + h` |
| **g** | cost from the start to the node |
| **h** | estimated cost from the node to the goal |
| **f** | `g + h` |
| **node limit** | maximum number of expansions, not seconds |

---

## 15. The short version

If you only remember five things:

1. `boxgame.py` defines the game: state, moves, goal, parser and `Node`.
2. `search.py` defines OPEN/CLOSED, BFS, A*, the three heuristics and the
   deadlock detector.
3. A deadlock is a box that can never reach a target. Corner deadlocks are
   red cells; line deadlocks are yellow cells. `dead_cells` finds them once
   per level, `has_deadlock` checks a state, and A* can skip those states.
4. h1 counts misplaced boxes, h2 adds a distance penalty (but is
   inadmissible), and h3 uses real push distances with walls plus a
   one-to-one matching plus the player walk. h3 is the strongest.
5. The measurements count expanded and generated nodes, not seconds. On the
   seven boards, h3 expands 89.0% fewer nodes than BFS, and the deadlock
   filter removes 82.8% of h1's expansions and 83.8% of h2's expansions.
