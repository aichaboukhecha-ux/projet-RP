"""Runs BFS and the A* versions on the 7 boards and writes benchmark.csv.

The five main algorithms are BFS, A* h1, A* h2, A* h3 and A* h3+deadlock.
Two extra runs (A* h1+deadlock, A* h2+deadlock) show what the deadlock filter
does with the weaker heuristics (section 6 of report.md).

The printed comparison shows the theoretical complexity, the cost and the
nodes (expanded, generated).  benchmark.csv keeps every counter.

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

EXTRA = [
    ("A* h1+deadlock", h1, True),
    ("A* h2+deadlock", h2, True),
]

THEORY = {
    "BFS": "O(b^d) time / space",
    "A* h1": "O(b^d) h O(B)",
    "A* h2": "O(b^d) h O(B*T)",
    "A* h3": "O(b^d) h O(B^2*2^B)",
    "A* h3+deadlock": "O(b^d) h O(B^2*2^B) + O(B)",
    "A* h1+deadlock": "O(b^d) h O(B)",
    "A* h2+deadlock": "O(b^d) h O(B*T)",
}

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
        open_end = stats.get("open_size", 0)
        closed = stats.get("closed_size", 0)
        max_open = stats.get("max_open", 0)
        heuristic_calls = 0
        deadlock_checks = 0
    else:
        result = astar(state, heuristic, node_limit=DEFAULT_NODE_LIMIT,
                       use_deadlock=use_deadlock)
        goal, expanded = result
        generated = result.generated
        limit_reached = result.limit_reached
        open_end = result.open_size
        closed = result.closed_size
        max_open = result.max_open
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
        "closed": closed,
        "open_end": open_end,
        "max_open": max_open,
        "heuristic_calls": heuristic_calls,
        "deadlock_checks": deadlock_checks,
        "status": status,
    }


def benchmark():
    rows = []
    for board, ascii_board in all_boards():
        state = parse_board(ascii_board)
        for method, heuristic, use_deadlock in ALGORITHMS + EXTRA:
            result = run_one(method, heuristic, use_deadlock, state)
            result["board"] = board
            rows.append(result)
            print("  %-18s %-14s %s" % (board, method, result["status"]),
                  flush=True)
    return rows


def write_csv(rows, path=CSV_PATH):
    fields = ["board", "method", "cost", "expanded", "generated",
              "closed", "open_end", "max_open", "heuristic_calls", "deadlock_checks", "status", "actions"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["actions"] = " ".join(row["actions"])
            writer.writerow({key: out[key] for key in fields})
    return path


def print_table(rows):
    header = "%-18s %-16s %-28s %5s %9s %9s %-12s" % (
        "board", "method", "complexity", "cost", "expanded", "generated",
        "status")
    line = "-" * len(header)
    print()
    print(line)
    print(header)
    print(line)
    for row in rows:
        cost = "n/a" if row["cost"] is None else str(row["cost"])
        print("%-18s %-16s %-28s %5s %9d %9d %-12s" % (
            row["board"], row["method"], THEORY.get(row["method"], "-"),
            cost, row["expanded"], row["generated"], row["status"]))
    print(line)


def print_totals(rows):
    print("\nTotals over the seven boards (nodes)")
    for method, _, _ in ALGORITHMS:
        chosen = [r for r in rows if r["method"] == method]
        expanded = sum(r["expanded"] for r in chosen)
        generated = sum(r["generated"] for r in chosen)
        print("%-14s expanded=%-7d generated=%d"
              % (method, expanded, generated))


def print_deadlock_effect(rows):
    """Expanded nodes with and without the deadlock filter (report section 6)."""
    pairs = [("h1", "A* h1", "A* h1+deadlock"), ("h2", "A* h2", "A* h2+deadlock"),
             ("h3", "A* h3", "A* h3+deadlock")]
    print("\nExpanded nodes, without -> with the deadlock filter")
    boards = []
    for r in rows:
        if r["board"] not in boards:
            boards.append(r["board"])
    totals = {name: [0, 0] for name, _, _ in pairs}
    for board in boards:
        cells = []
        for name, plain, filtered in pairs:
            a = next(r for r in rows if r["board"] == board and r["method"] == plain)
            b = next(r for r in rows if r["board"] == board and r["method"] == filtered)
            totals[name][0] += a["expanded"]
            totals[name][1] += b["expanded"]
            cells.append("%s %6d -> %6d" % (name, a["expanded"], b["expanded"]))
        print("  %-16s %s" % (board, "   ".join(cells)))
    print("  %-16s %s" % ("TOTAL", "   ".join(
        "%s %6d -> %6d" % (n, t[0], t[1]) for n, t in totals.items())))


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
    print_deadlock_effect(rows)
    print_figure7(rows)
    path = write_csv(rows)
    print("\nCSV written to %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())