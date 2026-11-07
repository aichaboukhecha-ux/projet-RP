"""Runs BFS and the four A* versions on the 7 boards and writes benchmark.csv.

Run: python benchmark.py
"""

import csv
import os
import sys

from boxgame import parse_board
from figure4_boards import boards as figure4_boards
from figure7_boards import boards as figure7_boards
from search import astar, bfs, h1, h2, h3, DEFAULT_NODE_LIMIT

ALGORITHMS = [
    ("BFS", None, False),
    ("A* h1", h1, False),
    ("A* h2", h2, False),
    ("A* h3", h3, False),
    ("A* h3+deadlock", h3, True),
]

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "benchmark.csv")


def all_boards():
    for name, rows in figure4_boards():
        yield "fig4-" + name, rows
    for name, rows in figure7_boards():
        yield "fig7-" + name, rows


def run_one(method, heuristic, use_deadlock, state):
    if heuristic is None:
        stats = {}
        goal, expanded = bfs(state, stats, node_limit=DEFAULT_NODE_LIMIT)
        generated = stats.get("generated", 0)
        limit_reached = stats.get("limit_reached", False)
        heuristic_calls = 0
        deadlock_checks = 0
    else:
        result = astar(state, heuristic, node_limit=DEFAULT_NODE_LIMIT,
                       use_deadlock=use_deadlock)
        goal, expanded = result
        generated = result.generated
        limit_reached = result.limit_reached
        heuristic_calls = result.heuristic_calls
        deadlock_checks = result.deadlock_checks

    if goal is None:
        status = "LIMIT" if limit_reached else "NO-SOLUTION"
        cost = None
        actions = []
    else:
        status = "ok"
        cost = goal.g
        actions = goal.getSolution()

    return {
        "method": method,
        "cost": cost,
        "actions": actions,
        "expanded": expanded,
        "generated": generated,
        "heuristic_calls": heuristic_calls,
        "deadlock_checks": deadlock_checks,
        "status": status,
    }


def benchmark():
    rows = []
    for board, ascii_board in all_boards():
        state = parse_board(ascii_board)
        for method, heuristic, use_deadlock in ALGORITHMS:
            result = run_one(method, heuristic, use_deadlock, state)
            result["board"] = board
            rows.append(result)
            print("  %-18s %-14s %s" % (board, method, result["status"]),
                  flush=True)
    return rows


def write_csv(rows, path=CSV_PATH):
    fields = ["board", "method", "cost", "expanded", "generated",
              "heuristic_calls", "deadlock_checks", "status", "actions"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["actions"] = " ".join(row["actions"])
            writer.writerow({key: out[key] for key in fields})
    return path


def preview(actions, count=6):
    if len(actions) <= count:
        return " ".join(actions)
    return " ".join(actions[:count]) + " ..."


def print_table(rows):
    header = "%-18s %-14s %5s %9s %9s %10s %10s %-12s %s" % (
        "board", "method", "cost", "expanded", "generated",
        "heuristic", "deadlock", "status", "solution")
    line = "-" * len(header)
    print()
    print(line)
    print(header)
    print(line)
    for row in rows:
        cost = "n/a" if row["cost"] is None else str(row["cost"])
        print("%-18s %-14s %5s %9d %9d %10d %10d %-12s %s" % (
            row["board"], row["method"], cost, row["expanded"],
            row["generated"], row["heuristic_calls"],
            row["deadlock_checks"], row["status"],
            preview(row["actions"])))
    print(line)


def print_totals(rows):
    print("\nTotals over the seven boards")
    for method, _, _ in ALGORITHMS:
        chosen = [r for r in rows if r["method"] == method]
        expanded = sum(r["expanded"] for r in chosen)
        generated = sum(r["generated"] for r in chosen)
        heuristic = sum(r["heuristic_calls"] for r in chosen)
        deadlock = sum(r["deadlock_checks"] for r in chosen)
        print("%-14s expanded=%-7d generated=%-7d heuristic=%-7d deadlock=%d"
              % (method, expanded, generated, heuristic, deadlock))


def print_figure7(rows):
    print("\nFigure 7 solutions")
    for board in ("fig7-exemple1", "fig7-exemple2"):
        print("\n%s" % board)
        for method, _, _ in ALGORITHMS:
            row = next(r for r in rows
                       if r["board"] == board and r["method"] == method)
            if row["status"] != "ok":
                print("  %-14s %s" % (method, row["status"]))
                continue
            print("  %-14s cost=%d expanded=%d generated=%d"
                  % (method, row["cost"], row["expanded"],
                     row["generated"]))
            print("    " + " ".join(row["actions"]))


def main():
    print("Figure 4 and Figure 7 boards")
    print("node limit: %d" % DEFAULT_NODE_LIMIT)
    rows = benchmark()
    print_table(rows)
    print_totals(rows)
    print_figure7(rows)
    path = write_csv(rows)
    print("\nCSV written to %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
