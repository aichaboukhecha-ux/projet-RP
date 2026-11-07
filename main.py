from boxgame import Level, parse_board
from search import bfs

puzzle = parse_board(Level)
stats = {}
goal, expanded = bfs(puzzle, stats)

if goal is None:
    print("No solution")
else:
    print("Solution :", goal.getSolution())
    print("Cost     :", goal.g)
    print("Expanded :", expanded)
    print("Generated:", stats["generated"])
    print("OPEN     :", stats["open_size"], "nodes left at the end"
          " (max %d)" % stats["max_open"])
    print("CLOSED   :", stats["closed_size"], "nodes expanded")
    for state in goal.getPath():
        print(state, "\n")