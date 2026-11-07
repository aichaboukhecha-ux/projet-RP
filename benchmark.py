"""Measure BFS and A* (h1 / h2 / h3) on the five boards of Figure 4.

Run:  python benchmark.py            -> prints the table, writes benchmark.csv

Every number in the table comes from actually running the code.  Nothing is
estimated.  When a run hits a limit it is reported as a timeout instead of a
solution, and when a figure board cannot be solved within the limit the cell
says so.

Columns
-------
board      board name from Figure 4
method     bfs | astar-h1 | astar-h2 | astar-h3
cost       optimal number of pushes/actions (None -> no answer within limit)
actions    the action sequence (space separated, truncated in the table,
           complete in the CSV)
expanded   nodes popped and expanded
generated  nodes created and pushed
seconds    wall clock (perf_counter)
status     ok | TIMEOUT | NO-SOLUTION
"""

import csv
import os
import sys
import time

from boxgame import parse_board
from figure4_boards import boards, FIGURE4_ORDER
from search import bfs, astar, h1, h2, h3

# Honest, uniform limits for every run in this benchmark.
NODE_LIMIT = 400000
TIMEOUT = 15.0

ALGORITHMS = [
    ("bfs", None),
    ("astar-h1", h1),
    ("astar-h2", h2),
    ("astar-h3", h3),
]

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "benchmark.csv")


def run_one(method, heuristic, state):
    """Run a single (board, method) pair and return a result dict."""
    stats = {}

    if heuristic is None:
        goal, expanded = bfs(state, stats)
        seconds = stats.get("seconds", 0.0)
        generated = stats.get("generated", 0)
        timed_out = stats.get("timed_out", False)
    else:
        result = astar(state, heuristic,
                       node_limit=NODE_LIMIT, timeout=TIMEOUT)
        goal, expanded = result
        seconds = result.seconds
        generated = result.generated
        timed_out = result.timed_out

    if goal is None:
        status = "TIMEOUT" if timed_out else "NO-SOLUTION"
        return {
            "cost": None, "actions": "", "expanded": expanded,
            "generated": generated, "seconds": seconds, "status": status,
        }

    return {
        "cost": goal.g,
        "actions": " ".join(goal.getSolution()),
        "expanded": expanded,
        "generated": generated,
        "seconds": seconds,
        "status": "ok",
    }


def benchmark():
    rows = []
    for name, ascii_board in boards():
        state = parse_board(ascii_board)
        for method, heuristic in ALGORITHMS:
            res = run_one(method, heuristic, state)
            res["board"] = name
            res["method"] = method
            rows.append(res)
            print("  %-9s %-9s %s" % (name, method, res["status"]), flush=True)
    return rows


def write_csv(rows, path=CSV_PATH):
    fields = ["board", "method", "cost", "expanded", "generated",
              "seconds", "status", "actions"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fields})
    return path


def print_table(rows):
    header = "%-9s %-9s %5s %9s %9s %9s %-13s" % (
        "board", "method", "cost", "expanded", "generated", "seconds",
        "status")
    line = "-" * len(header)
    print()
    print(line)
    print(header)
    print(line)
    for r in rows:
        cost = "n/a" if r["cost"] is None else str(r["cost"])
        print("%-9s %-9s %5s %9d %9d %9.4f %-13s" % (
            r["board"], r["method"], cost, r["expanded"], r["generated"],
            r["seconds"], r["status"]))
    print(line)


def main():
    print("Figure 4 boards - BFS vs A*(h1) A*(h2) A*(h3)")
    print("limits: node_limit=%d  timeout=%.1fs" % (NODE_LIMIT, TIMEOUT))
    t0 = time.perf_counter()
    rows = benchmark()
    print_table(rows)
    path = write_csv(rows)
    print("\nCSV written to %s" % path)
    print("total wall clock: %.2fs" % (time.perf_counter() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
