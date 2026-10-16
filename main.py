from boxgame import Level, parse_board
from search import bfs

puzzle = parse_board(Level)
goal, expanded = bfs(puzzle)

if goal is None:
    print("No solution")
else:
    print("Solution :", goal.getSolution())
    print("Cost     :", goal.g)
    print("Expanded :", expanded)
    for state in goal.getPath():
        print(state, "\n")
 
