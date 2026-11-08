# Sokoban Fairy Puzzle

A Sokoban solver with a Pygame interface (Project 1, Part 3).
It solves the puzzle with BFS and with A* (three heuristics, with or without
deadlock detection) and compares them on the boards of Figure 4 and Figure 7.

## Run

```
pip install pygame
python gui.py
python tests.py
python benchmark.py
```

`python benchmark.py` prints the comparison table and writes `benchmark.csv`.

## Interface

- `SPACE` play / pause, `R` restart, `<` `>` previous / next step
- `-` `+` speed
- `[` `]` previous / next level (13 levels)
- `A` change the algorithm: BFS, A* h1, A* h2, A* h3, A* h3+deadlock
- `C` open / close the comparison screen (complexity, cost, expanded, generated)
- `F11` fullscreen, `ESC` quit

## How to read the numbers

- **Expanded**: nodes taken out of the queue and explored (loop iterations).
- **Generated**: nodes created.
- Fewer is better. All algorithms return the same cost on the test boards.
- `limit reached` means the search stopped at 400000 expanded nodes.
- The heuristic-call and deadlock-check counters are kept in
  `benchmark.csv`, not in the on-screen comparison.

## Files

- `boxgame.py` - the board, the rules (`SokobanPuzzle`), the parser and `Node`
- `search.py` - BFS, h1, h2, h3, A*, dead cells and deadlock check
- `levels.py` - the 13 levels
- `figure4_boards.py`, `figure7_boards.py` - the boards of the PDF
- `gui.py` - the interface
- `benchmark.py`, `benchmark.csv` - runs every algorithm on 7 boards
- `tests.py` - tests (they run without a window)
- `report.md` - report with tables and solutions
- `EXPLAIN_LIKE_IM_5.md` - the code explained in simple words
- `EXPLANATION.md` - the long line-by-line explanation of every file
- `main.py` - tiny console demo
- `puzzle.py` - first, very simple viewer (not used any more)
- `assets/` - images, fonts, sounds
