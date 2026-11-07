"""Sokoban Fairy Puzzle - regression tests (off-screen, no screenshots).

    python tests.py          # dummy video driver, fully headless
    python tests.py --real   # real window, exercises actual fullscreen
"""
import os
import sys
import tempfile
import threading
import time

REAL = "--real" in sys.argv
if not REAL:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pygame

import gui
from levels import LEVELS
from boxgame import parse_board

# Must run before pygame.init(): SDL caches the desktop size on first use and
# reports a DPI-virtualised 1280x720 instead of the real 1920x1080 otherwise.
gui.enable_dpi_awareness()
pygame.init()
FAILURES = []


def check(label, condition, detail=""):
    print("  %-4s %s%s" % ("PASS" if condition else "FAIL", label,
                           ("  [%s]" % detail) if detail else ""))
    if not condition:
        FAILURES.append(label)


class Recorder:
    """Stands in for Audio so we can assert on the effects that fired."""

    def __init__(self):
        self.names = []

    def play(self, name):
        self.names.append(name)

    def start_music(self):
        self.names.append("music")

    def stop_music(self):
        self.names.append("stop_music")


print("\n== 1. levels are ordered facile -> difficile ==")
rows = []
for i, board in enumerate(LEVELS):
    puzzle = parse_board(board)
    goal, expanded = gui.bfs(puzzle)
    rows.append((i + 1, goal.g if goal else -1, expanded))
    print("     level %d  cost=%-3d expanded=%d" % rows[-1])

costs = [c for _, c, _ in rows]
check("the six original levels stay ordered by cost",
      all(costs[i] <= costs[i + 1] for i in range(5)),
      "costs=%s" % costs[:6])
check("13 levels present", len(LEVELS) == 13)
check("every level has a solution", all(c > 0 for c in costs),
      "costs=%s" % costs)
check("level names removed from levels.py",
      not hasattr(__import__("levels"), "LEVEL_NAMES"))


print("\n== 2. SPEED + really speeds up (the old code was inverted) ==")
gui.AUDIO = Recorder()
puzzle, player, _, _ = gui.load_level(0, 700)

check("starts at 700 ms", player.delay == 700, "%d ms" % player.delay)
player.faster()
check("+ makes it quicker", player.delay < 700, "%d ms" % player.delay)

start_index = player.speed_index
while player.speed_index < len(gui.SPEEDS) - 1:
    player.faster()
check("+ stops at the fastest step", player.delay == min(gui.SPEEDS),
      "%d ms" % player.delay)
player.faster()
check("+ at max is a no-op (not a wrap)", player.delay == min(gui.SPEEDS))
check("+ at max bumps", "bump" in gui.AUDIO.names)

while player.speed_index > 0:
    player.slower()
check("- stops at the slowest step", player.delay == max(gui.SPEEDS),
      "%d ms" % player.delay)
player.slower()
check("- at min is a no-op", player.delay == max(gui.SPEEDS))

# every press in the '+' direction must strictly shorten the delay
p2 = gui.SolutionPlayer([parse_board(LEVELS[0])], [], 0, 0, gui.SPEEDS[0])
seq = [p2.delay]
for _ in range(len(gui.SPEEDS) - 1):
    p2.faster()
    seq.append(p2.delay)
check("the '+' ladder walks every speed, slowest to quickest",
      seq == gui.SPEEDS, "ms=%s" % seq)
check("fastest step is 30 ms (quick)", seq[-1] <= 30, "ms=%s" % seq[-1])


print("\n== 3. sound effects fire on the right actions ==")
gui.AUDIO = Recorder()
puzzle, player, _, _ = gui.load_level(0, 1)        # 1 ms -> finishes instantly
player.play()
ticks = 1000
player._last = ticks
for _ in range(400):
    ticks += 5
    player.update(ticks)
    if player.status == player.SOLVED:
        break

fired = gui.AUDIO.names
check("reached SOLVED", player.status == player.SOLVED, player.status)
check("win sound played once", fired.count("win") == 1,
      str(fired.count("win")))
check("movement sound played", any(n in fired for n in ("step", "push")),
      str(sorted(set(fired))))
check("a box push was detected", "push" in fired, str(fired))
check("a box landing on its target chimed", "target" in fired, str(fired))

gui.AUDIO = Recorder()
puzzle, player, _, _ = gui.load_level(0, 500)
player.next_step()
check("next_step plays a movement sound", bool(gui.AUDIO.names),
      str(gui.AUDIO.names))
player.prev_step()
check("prev_step plays the undo sound", "undo" in gui.AUDIO.names,
      str(gui.AUDIO.names))
player.reset()
for _ in range(6):
    player.prev_step()
check("prev at step 0 bumps", "bump" in gui.AUDIO.names)


print("\n== 4. the WAV assets really load ==")
real = gui.Audio(os.path.join(gui.resource_dir(), "assets"))
if not real.ok:
    print("  SKIP no audio device on this machine - game runs silent")
else:
    check("all 7 sound effects loaded", len(real.sounds) == 7,
          str(sorted(real.sounds)))
    missing = [n for n in gui.Audio.SFX
               if not os.path.exists(os.path.join(
                   gui.resource_dir(), "assets", "sounds", n + ".wav"))]
    check("every referenced wav file exists", not missing, str(missing))
    music = os.path.join(gui.resource_dir(), "assets", "sounds", "music.wav")
    check("music.wav exists", os.path.exists(music))
    channel = real.sounds["step"].play()
    check("playback opens a channel", channel is not None, str(channel))
    check("mixer has channels for fast playback",
          pygame.mixer.get_num_channels() >= 8,
          str(pygame.mixer.get_num_channels()))
    if channel is not None:
        channel.stop()


print("\n== 5. window / fullscreen geometry ==")
puzzles = [parse_board(b) for b in LEVELS]
max_w = max(p.width for p in puzzles)
max_h = max(p.height for p in puzzles)
width, height, board_area, panel = gui.compute_geometry(max_w, max_h)
print("     logical frame = %dx%d" % (width, height))
check("the panel grew for the fullscreen button", gui.BUTTON_ROWS == 5)
check("the hint list documents the new keys", gui.HINT_LINES == 7)

buttons = gui.build_buttons(panel)
check("fullscreen button exists", "fullscreen" in buttons)
fs = buttons["fullscreen"].rect
check("fullscreen button fits inside the panel",
      panel.contains(fs), "%s in %s" % (fs, panel))
check("fullscreen button clears the hint block",
      fs.bottom <= panel.y + gui.HINTS_Y,
      "btn.bottom=%d hints.y=%d" % (fs.bottom, panel.y + gui.HINTS_Y))
check("every button stays inside the panel",
      all(panel.contains(b.rect) for b in buttons.values()))
check("title constant is the new name", gui.TITLE == "SOKOBAN FAIRY PUZZLE",
      gui.TITLE)


print("\n== 6. frame renders with the new header ==")
out = os.path.join(tempfile.gettempdir(), "sfp")
os.makedirs(out, exist_ok=True)
gui.AUDIO = Recorder()

pygame.display.set_mode((width, height))     # the game always has a window
frame = pygame.Surface((width, height))
assets = gui.Assets(os.path.join(gui.resource_dir(), "assets"))
check("real fairy sprites loaded (no silent fallback)",
      all(assets.player.get(d) is not None for d in ("up", "down", "left",
                                                     "right")))
check("fairy is the big %dpx sprite" % gui.PLAYER_SPRITE,
      assets.player.get("down") is not None
      and assets.player["down"].get_size() == (gui.PLAYER_SPRITE,
                                               gui.PLAYER_SPRITE),
      str(assets.player.get("down").get_size()
          if assets.player.get("down") else None))
check("wall + box + target loaded",
      assets.wall is not None and assets.box is not None
      and assets.target is not None)
puzzle, player, deco, results = gui.load_level(0, 400)
origin = gui.board_origin(board_area, puzzle)

frame.fill(gui.BG_DEEP)
gui.draw_header(frame, assets, width, 0)
gui.draw_board(frame, puzzle, assets, player.facing, deco, origin)
gui.draw_panel(frame, panel, assets, player, buttons, 0,
               mouse=(0, 0))
pygame.image.save(frame, os.path.join(out, "header.png"))
check("frame rendered", os.path.exists(os.path.join(out, "header.png")))

# the old title must be gone from the source
src = open(os.path.join(HERE, "gui.py"), encoding="utf-8").read()
check("no 'Enchanted Forest' left in gui.py",
      "ENCHANTED" not in src and "Enchanted" not in src)
check("caption uses the new name", gui.CAPTION == "Sokoban Fairy Puzzle",
      gui.CAPTION)


print("\n== 7. successor rules: the model really matches the spec ==")
from boxgame import Node, SokobanPuzzle            # noqa: E402
from search import (bfs, astar, h1, h2, h3,        # noqa: E402
                    dead_cells, has_deadlock, SearchResult,
                    DEFAULT_NODE_LIMIT)
from figure4_boards import boards as figure4_boards  # noqa: E402
from figure7_boards import FIGURE7                 # noqa: E402


def actions_of(state):
    return {a for a, _ in state.successorFunction()}


# open floor in front of the box: every direction is legal
b1 = parse_board(["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"])
succ = {a: s for a, s in b1.successorFunction()}
check("open floor: all four directions are successors",
      set(succ) == {"UP", "DOWN", "LEFT", "RIGHT"}, str(sorted(succ)))
check("a push moves the player into the box's old cell",
      succ["LEFT"].player == (2, 2), str(succ["LEFT"].player))
check("a push moves the box exactly one cell",
      succ["LEFT"].boxes == frozenset({(2, 1)}), str(sorted(succ["LEFT"].boxes)))
check("a push leaves walls and targets untouched",
      succ["LEFT"].walls == b1.walls and succ["LEFT"].targets == b1.targets)
check("no pull: the box stays put when the player walks away",
      all(succ[a].boxes == b1.boxes for a in ("UP", "DOWN", "RIGHT")))
check("no jump: every successor is a single step from the player",
      all(abs(succ[a].player[0] - b1.player[0])
          + abs(succ[a].player[1] - b1.player[1]) == 1 for a in succ))
check("the player never lands on top of a box",
      all(succ[a].player not in succ[a].boxes for a in succ))

# box with a wall directly behind it
b2 = parse_board(["OOOOOO", "O S  O", "OOBOR ", "O    O", "OOOOOO"])
check("no push into a wall", "LEFT" not in actions_of(b2),
      str(sorted(actions_of(b2))))

# two boxes side by side
b3 = parse_board(["OOOOOO", "O S  O", "O BBRO", "O S  O", "OOOOOO"])
check("no push into a second box", "LEFT" not in actions_of(b3),
      str(sorted(actions_of(b3))))
check("...and the legal moves still work",
      actions_of(b3) == {"UP", "DOWN"}, str(sorted(actions_of(b3))))

# the board edge is not a wall, so leaving the grid must be rejected too
b4 = parse_board(["  RB", "  S "])
check("no push off the grid", "RIGHT" not in actions_of(b4),
      str(sorted(actions_of(b4))))
check("no walk off the grid", "UP" not in actions_of(b4),
      str(sorted(actions_of(b4))))


print("\n== 8. isGoal: any box on any target, in any order ==")
on_target = parse_board(["OOOOOO", "O ** O", "O    O", "O R  O", "OOOOOO"])
check("every target covered -> goal", on_target.isGoal())

off_target = parse_board(["OOOOOO", "O *S O", "O  B O", "O R  O", "OOOOOO"])
check("one empty target -> not a goal", not off_target.isGoal(),
      str(sorted(off_target.targets - off_target.boxes)))

# which box sits on which target must not matter
swapped = SokobanPuzzle(targets={(1, 3), (2, 1)}, walls=frozenset(),
                        boxes={(1, 3), (2, 1)}, player=(3, 3),
                        height=4, width=4)
check("isGoal ignores which box is on which target", swapped.isGoal())

# documented reading of the spec: extra boxes beyond the targets still count,
# because parse_board enforces equal counts, so targets <= boxes and
# boxes <= targets are the same test on every board we can actually build.
extra = SokobanPuzzle(targets={(1, 1)}, walls=frozenset(),
                      boxes={(1, 1), (2, 2)}, player=(0, 0),
                      height=4, width=4)
check("isGoal only requires every target to hold a box", extra.isGoal())


print("\n== 9. Node.setF / getPath / getSolution ==")
root = Node(parse_board(["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"]))
check("a fresh node starts with f == g", root.f == root.g, str(root.f))
check("setF returns g + h(state)",
      root.setF(h1) == root.g + h1(root.state),
      "%d == %d + %d" % (root.f, root.g, h1(root.state)))
check("setF stores the value on the node", root.f == root.g + h1(root.state))

child_state = dict(root.state.successorFunction())["LEFT"]
child = Node(child_state, root, "LEFT", 1)
child.setF(h1)
check("child f = g + h through setF",
      child.f == child.g + h1(child.state),
      "%d == %d + %d" % (child.f, child.g, h1(child.state)))
check("setF works with any callable", Node(child_state, root, "LEFT", 1)
      .setF(lambda s: 42) == 1 + 42)

check("getPath returns the state chain root -> node",
      child.getPath()[0] is root.state and child.getPath()[-1] is child.state)
check("getPath length is depth + 1", len(child.getPath()) == 2,
      str(len(child.getPath())))
check("getSolution lists the actions in order",
      child.getSolution() == ["LEFT"], str(child.getSolution()))
check("solution length equals g", len(child.getSolution()) == child.g)
check("the root has an empty solution", root.getSolution() == [])
check("getPath states line up with the solution",
      [s.player for s in child.getPath()] == [root.state.player,
                                              child.state.player])


print("\n== 10. h1 / h2 / h3 on a hand-built board (h2 is inadmissible) ==")
# box two cells from its target, player already beside it, so two pushes win.
tiny = parse_board(["OOOOO", "OS BR", "OOOOO"])
print("     board: " + " / ".join(["OOOOO", "OS BR", "OOOOO"]))
print("     h1=%d  h2=%d  h3=%d" % (h1(tiny), h2(tiny), h3(tiny)))

check("h1 counts misplaced boxes", h1(tiny) == 1, str(h1(tiny)))
check("h2 = 2*left + distance sum", h2(tiny) == 4, str(h2(tiny)))
check("h3 = matching + player walk", h3(tiny) == 2, str(h3(tiny)))

tiny_goal, _ = bfs(tiny)
opt = tiny_goal.g
check("BFS optimum is 2 pushes", opt == 2, str(opt))
check("h1 <= optimum (admissible)", h1(tiny) <= opt,
      "%d <= %d" % (h1(tiny), opt))
check("h3 <= optimum (admissible)", h3(tiny) <= opt,
      "%d <= %d" % (h3(tiny), opt))
check("h2 > optimum, so h2 is INADMISSIBLE", h2(tiny) > opt,
      "h2=%d vs optimum=%d" % (h2(tiny), opt))

for label, heu, dead in (("h1", h1, False), ("h2", h2, False),
                         ("h3", h3, False), ("h3+deadlock", h3, True)):
    res = astar(tiny, heu, use_deadlock=dead)
    check("A*(%s) still reaches the goal" % label,
          res.goal is not None and not res.limit_reached, str(res.cost))


print("\n== 11. A* vs BFS, SearchResult, and honest node limits ==")
for name, ascii_board in figure4_boards():
    st = parse_board(ascii_board)
    bfs_goal, _ = bfs(st)
    costs = {}
    reached = True
    for label, heu, dead in (("h1", h1, False), ("h2", h2, False),
                             ("h3", h3, False), ("h3+deadlock", h3, True)):
        res = astar(st, heu, use_deadlock=dead)
        costs[label] = res.cost
        reached = reached and res.goal is not None and not res.limit_reached
    check("%s: all four A* variants reach a goal" % name, reached,
          str(costs))
    check("%s: every A* cost equals the BFS optimum" % name,
          bfs_goal is not None
          and all(c == bfs_goal.g for c in costs.values()),
          "bfs=%s %s" % (bfs_goal.g if bfs_goal else None, costs))

res = astar(parse_board(["OOOOOO", "O S  O", "O BR O", "O    O",
                         "OOOOOO"]), h1)
check("SearchResult unpacks exactly like bfs", len(res) == 2
      and res[0] is not None and isinstance(res[1], int))
check("SearchResult carries .generated", res.generated > 0,
      str(res.generated))
check("SearchResult carries .heuristic_calls", res.heuristic_calls > 0,
      str(res.heuristic_calls))
check("SearchResult carries .deadlock_checks", res.deadlock_checks == 0,
      str(res.deadlock_checks))
check("a finished run reports limit_reached False",
      res.limit_reached is False)
check("SearchResult.cost mirrors goal.g", res.cost == res.goal.g)
check("SearchResult.goal mirrors the pair", res.goal is res[0])

# --- node limit must be honoured exactly --------------------------------
limit_board = parse_board(list(figure4_boards())[-1][1])   # exemple5
limited = astar(limit_board, h1, node_limit=25)
check("A* node_limit=25 stops at exactly 25 expansions",
      limited[1] == 25, str(limited[1]))
check("A* reports the node limit as limit_reached",
      limited.limit_reached is True and limited.goal is None)

stats = {}
limited_bfs = bfs(limit_board, stats, node_limit=25)
check("BFS node_limit=25 stops at exactly 25 expansions",
      limited_bfs[1] == 25, str(limited_bfs[1]))
check("BFS reports limit_reached", stats.get("limit_reached") is True,
      str(stats))

# --- no solution at all -------------------------------------------------
unsolvable = parse_board(["OOOOOO", "OBOOOO", "OO    ", "OSR  O", "OOOOOO"])
u_goal, u_expanded = bfs(unsolvable)
check("BFS reports no solution", u_goal is None, str(u_expanded))
u_res = astar(unsolvable, h1, node_limit=DEFAULT_NODE_LIMIT)
check("A* reports NO-SOLUTION, not a limit",
      u_res.goal is None and u_res.limit_reached is False)
check("A* really exhausted the frontier", u_res[1] > 0,
      str(u_res[1]))

# --- bfs keeps its old contract ----------------------------------------
plain = bfs(parse_board(["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"]))
check("bfs() without stats still returns a plain pair",
      len(plain) == 2 and not hasattr(plain, "generated"))
stats = {}
bfs(parse_board(["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"]), stats)
check("bfs() fills the optional stats dict",
      stats.get("generated", 0) >= 1
      and stats.get("limit_reached") is False, str(stats))
check("the default node limit is the one we tested against",
      DEFAULT_NODE_LIMIT == 400000, str(DEFAULT_NODE_LIMIT))


print("\n== 12. deadlock cells match the red / yellow cells of Figures 5-6 ==")
fig7_1 = parse_board(FIGURE7["exemple1"])
fig7_2 = parse_board(FIGURE7["exemple2"])

red1 = {(1, 2), (1, 4), (1, 5), (5, 2), (5, 4), (5, 5)}
yellow1 = {(2, 5), (3, 5), (4, 5)}
dead1 = set(dead_cells(fig7_1))
check("Ex1: every red corner cell is dead", red1 <= dead1,
      str(sorted(red1 - dead1)))
check("Ex1: every yellow line cell is dead", yellow1 <= dead1,
      str(sorted(yellow1 - dead1)))
check("Ex1: exactly the red + yellow cells are dead",
      dead1 == red1 | yellow1, str(sorted(dead1 ^ (red1 | yellow1))))

red2 = {(1, 4), (2, 6), (3, 1), (4, 4), (4, 6)}
yellow2 = {(3, 6), (4, 5)}
dead2 = set(dead_cells(fig7_2))
check("Ex2: every red corner cell is dead", red2 <= dead2,
      str(sorted(red2 - dead2)))
check("Ex2: every yellow line cell is dead", yellow2 <= dead2,
      str(sorted(yellow2 - dead2)))
check("Ex2: exactly the red + yellow cells are dead",
      dead2 == red2 | yellow2, str(sorted(dead2 ^ (red2 | yellow2))))

corner_box = SokobanPuzzle(fig7_1.targets, fig7_1.walls,
                           frozenset({(1, 2)}), fig7_1.player,
                           fig7_1.height, fig7_1.width)
line_box = SokobanPuzzle(fig7_2.targets, fig7_2.walls,
                         frozenset({(4, 5)}), fig7_2.player,
                         fig7_2.height, fig7_2.width)
check("a box on a dead corner is a deadlock", has_deadlock(corner_box))
check("a box on a dead line cell is a deadlock", has_deadlock(line_box))
check("the Figure 7 start states are not deadlocked",
      not has_deadlock(fig7_1) and not has_deadlock(fig7_2))

corner_target = parse_board([
    "OOOOO",
    "O*  O",
    "O   O",
    "O  RO",
    "OOOOO",
])
check("a target in a corner is not marked dead",
      (1, 1) not in dead_cells(corner_target))
check("a box on a corner target is NOT a deadlock",
      not has_deadlock(corner_target))

for name, state in (("Figure 7 ex1", fig7_1), ("Figure 7 ex2", fig7_2)):
    plain3 = astar(state, h3)
    pruned3 = astar(state, h3, use_deadlock=True)
    check("%s: deadlock pruning keeps the optimum" % name,
          pruned3.cost == plain3.cost,
          "%s vs %s" % (pruned3.cost, plain3.cost))
    check("%s: with h3, pruning never expands more" % name,
          pruned3.expanded <= plain3.expanded,
          "%d -> %d" % (plain3.expanded, pruned3.expanded))
    check("%s: with h3, pruning generates fewer nodes" % name,
          pruned3.generated < plain3.generated,
          "%d -> %d" % (plain3.generated, pruned3.generated))
    plain1 = astar(state, h1)
    pruned1 = astar(state, h1, use_deadlock=True)
    check("%s: with h1, pruning expands fewer nodes" % name,
          pruned1.expanded < plain1.expanded,
          "%d -> %d" % (plain1.expanded, pruned1.expanded))
    check("%s: deadlock checks were counted" % name,
          pruned3.deadlock_checks > 0, str(pruned3.deadlock_checks))


print("\n== 12b. Figure 4 boards: sizes and known optimal costs ==")
from figure4_boards import FIGURE4
fig4_expected = {"exemple1": ((6, 6), 4), "exemple2": ((9, 9), 29),
                 "exemple3": ((7, 8), 33), "exemple4": ((9, 7), 30),
                 "exemple5": ((8, 9), 25)}
for name, (size, cost) in fig4_expected.items():
    state = parse_board(FIGURE4[name])
    check("%s: size %dx%d" % (name, size[0], size[1]),
          (state.height, state.width) == size,
          "%dx%d" % (state.height, state.width))
    goal, expanded = bfs(state)
    check("%s: BFS finds the optimum %d" % (name, cost),
          goal is not None and goal.g == cost,
          str(goal.g if goal else None))
    res = astar(state, h3, use_deadlock=True)
    check("%s: A*(h3+deadlock) reaches %d" % (name, cost),
          res.cost == cost, str(res.cost))


print("\n== 13. Figure 7 boards validate and solve ==")
for name in ("exemple1", "exemple2"):
    rows = FIGURE7[name]
    state = parse_board(rows)
    players = sum(row.count("R") + row.count(".") for row in rows)
    check("%s: rectangular" % name,
          all(len(row) == len(rows[0]) for row in rows))
    check("%s: exactly one player" % name, players == 1, str(players))
    check("%s: boxes == targets" % name,
          len(state.boxes) == len(state.targets),
          "%d / %d" % (len(state.boxes), len(state.targets)))
    check("%s: closed by walls" % name,
          rows[0] == "O" * len(rows[0])
          and rows[-1] == "O" * len(rows[0]))

known_costs = {"exemple1": 41, "exemple2": 55}
for name, cost in known_costs.items():
    state = parse_board(FIGURE7[name])
    goal, expanded = bfs(state)
    check("%s: BFS finds the known optimum %d" % (name, cost),
          goal is not None and goal.g == cost,
          "%s / %d expanded" % (goal.g if goal else None, expanded))
    actions = goal.getSolution()
    check("%s: one action per cost unit" % name, len(actions) == cost,
          "%d / %d" % (len(actions), cost))

    current = state
    for action in actions:
        current = dict(current.successorFunction())[action]
    check("%s: replaying the actions solves the board" % name,
          current.isGoal())

    for label, heu, dead in (("h1", h1, False), ("h2", h2, False),
                             ("h3", h3, False),
                             ("h3+deadlock", h3, True)):
        res = astar(state, heu, use_deadlock=dead)
        check("%s: A*(%s) reaches cost %d" % (name, label, cost),
              res.cost == cost, str(res.cost))


print("\n== 14. GUI algorithm picker and comparison screen ==")
check("five algorithms are listed", len(gui.ALGORITHMS) == 5,
      str([a[0] for a in gui.ALGORITHMS]))
check("five cached results for the loaded level", len(results) == 5)
check("all five solved level 1",
      all(result["goal"] is not None for result in results))
check("BFS reports no heuristic calls",
      results[0]["heuristic_calls"] == 0)
check("A* h1 counted its heuristic calls",
      results[1]["heuristic_calls"] > 0)
check("the deadlock run counted its checks",
      results[4]["deadlock_checks"] > 0)

picked = gui.make_player(puzzle, results, 4, 400)
check("choosing an algorithm relabels the player",
      picked.algorithm == "A* h3+deadlock", picked.algorithm)
check("generated nodes reach the panel",
      picked.generated == results[4]["generated"],
      "%d / %d" % (picked.generated, results[4]["generated"]))

limited = gui.run_all_algorithms(puzzle, node_limit=1)
limited_player = gui.make_player(puzzle, limited, 0, 400)
check("a node limit becomes LIMIT REACHED",
      limited_player.status == "LIMIT REACHED", limited_player.status)
check("a limited run has no actions", limited_player.total == 0)

comparison = pygame.Surface((width, height))
gui.draw_comparison(comparison, assets, results, 0)
comparison_path = os.path.join(out, "comparison.png")
pygame.image.save(comparison, comparison_path)
check("the comparison screen renders",
      os.path.exists(comparison_path))

search_src = open(os.path.join(HERE, "search.py"), encoding="utf-8").read()
gui_src = open(os.path.join(HERE, "gui.py"), encoding="utf-8").read()
bench_src = open(os.path.join(HERE, "benchmark.py"),
                 encoding="utf-8").read()
check("the solver uses a node limit, not a timeout",
      "timeout" not in search_src.lower())
check("no wall-clock seconds in the reported numbers",
      "seconds" not in search_src and "seconds" not in gui_src
      and "seconds" not in bench_src)


if REAL:
    print("\n== 15. real fullscreen: button + F11 ==")
    observed = {}

    def driver():
        """Stands in for a user: click FULLSCREEN, then press F11, then quit."""
        time.sleep(2.0)
        ww, wh = pygame.display.get_surface().get_size()
        observed["windowed"] = (ww, wh)

        # mirror gui's letterboxing so the click lands on the button
        if (ww, wh) == (width, height):
            ox, oy, tw, th = 0, 0, width, height
        else:
            scale = min(ww / width, wh / height)
            tw, th = int(width * scale), int(height * scale)
            ox, oy = (ww - tw) // 2, (wh - th) // 2
        btn = gui.build_buttons(panel)["fullscreen"].rect
        cx = int(ox + btn.centerx * tw / width)
        cy = int(oy + btn.centery * th / height)
        observed["click_at"] = (cx, cy)
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                             pos=(cx, cy), button=1))
        time.sleep(1.5)
        observed["after_button"] = pygame.display.get_surface().get_size()

        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_F11, mod=0))
        time.sleep(1.5)
        observed["after_f11"] = pygame.display.get_surface().get_size()

        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))

    threading.Thread(target=driver, daemon=True).start()
    gui.main()
    print("     observed:", observed)

    desktop = (1920, 1080)
    check("window opened at the true logical size (DPI order is right)",
          observed.get("windowed") == (width, height),
          "%s vs %sx%s" % (observed.get("windowed"), width, height))
    check("the FULLSCREEN button enters fullscreen",
          observed.get("after_button") != observed.get("windowed"),
          "%s -> %s" % (observed.get("windowed"),
                        observed.get("after_button")))
    check("it fills the desktop",
          max(observed.get("after_button", (0, 0))) >= 1920,
          str(observed.get("after_button")))
    check("F11 then leaves fullscreen",
          observed.get("after_f11") == observed.get("windowed"),
          "%s vs %s" % (observed.get("after_f11"),
                        observed.get("windowed")))

# ---------------------------------------------------------------------------
print("\n== 15. OPEN and CLOSED lists ==")
from search import OpenFIFO, OpenPriority, Closed   # noqa: E402
from boxgame import Node                              # noqa: E402

demo = parse_board(["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"])
a = Node(demo)
kids = [Node(st, a, act, 1) for act, st in demo.successorFunction()]

fifo = OpenFIFO()
for k in kids:
    fifo.push(k)
check("OpenFIFO knows the states it holds",
      all(k.state in fifo for k in kids) and a.state not in fifo)
check("OpenFIFO is first in, first out", fifo.pop() is kids[0])
check("a popped node leaves OPEN", kids[0].state not in fifo
      and len(fifo) == len(kids) - 1)

prio = OpenPriority()
for f, k in zip((5, 2, 9), kids):
    k.f = f
    prio.push(k)
check("OpenPriority gives the smallest f first", prio.pop() is kids[1])
better = Node(kids[0].state, a, kids[0].action, 1)
better.f = 1
prio.push(better)
check("a better node for the same state replaces the old one in OPEN",
      len(prio) == 2 and prio.get(kids[0].state) is better)
check("the replaced entry is skipped when popping",
      prio.pop() is better and prio.pop() is kids[2] and prio.pop() is None)

closed = Closed()
closed.add(a)
check("Closed stores and finds an expanded node",
      a.state in closed and closed.get(a.state) is a and len(closed) == 1)
closed.remove(a.state)
check("Closed.remove reopens a state", a.state not in closed)

stats = {}
goal_b, exp_b = bfs(demo, stats)
check("BFS reports OPEN / CLOSED sizes",
      stats["closed_size"] == exp_b - 1 and stats["open_size"] > 0
      and stats["max_open"] >= stats["open_size"], str(stats))
check("BFS: every generated node is in OPEN or CLOSED (+ the goal)",
      stats["generated"] == stats["open_size"] + stats["closed_size"] + 1,
      str(stats))
res = astar(demo, h3)
check("A* reports OPEN / CLOSED sizes",
      res.closed_size == res.expanded - 1 and res.max_open >= res.open_size,
      "closed=%d open=%d max_open=%d" % (res.closed_size, res.open_size,
                                         res.max_open))
check("A* never keeps a state in OPEN and CLOSED at the same time",
      res.generated >= res.open_size + res.closed_size)

# BFS and A* count iterations the same way: the goal is tested when it is
# expanded, so the goal node itself is one iteration for both.
tiny_state = parse_board(["OOOOOO", "OSBR O", "OOOOOO"])
tg, te = bfs(tiny_state)
ag = astar(tiny_state, h1)
check("BFS and A* h1 expand the same number of nodes on a 1-D corridor",
      te == ag.expanded, "%d vs %d" % (te, ag.expanded))

gui_results = gui.run_all_algorithms(parse_board(
    ["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"]))
check("the GUI results carry OPEN / CLOSED sizes",
      all(r["closed_size"] > 0 and r["max_open"] >= r["open_size"]
          for r in gui_results))
gui_player = gui.make_player(parse_board(
    ["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"]), gui_results, 3, 400)
check("OPEN / CLOSED reach the side panel",
      gui_player.open_size == gui_results[3]["open_size"]
      and gui_player.closed_size == gui_results[3]["closed_size"])

rt = parse_board(["OOOOOOO", "OS*B  O", "O   R O", "OOOOOOO"])
check("toGrid() gives the 2D grid of the subject's symbols",
      ["".join(r) for r in rt.toGrid()]
      == ["OOOOOOO", "OS*B  O", "O   R O", "OOOOOOO"])
dot = parse_board(["OOOOO", "O.B*O", "OOOOO"])
check("'.' (player on target) round-trips through toGrid()",
      dot.toGrid()[1][1] == "." and dot.toGrid()[1][3] == "*")

pygame.quit()

print("\n%s  (%d failed)" % ("ALL TESTS PASSED" if not FAILURES
                             else "FAILURES: " + ", ".join(FAILURES),
                             len(FAILURES)))
sys.exit(1 if FAILURES else 0)