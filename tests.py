"""Sokoban Fairy Puzzle - regression tests (off-screen, no screenshots).

    python tests.py          # dummy video driver, fully headless
    python tests.py --real   # real window, exercises actual fullscreen
"""
import os
import sys
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


# ---------------------------------------------------------------------------
print("\n== 1. levels are ordered facile -> difficile ==")
rows = []
for i, board in enumerate(LEVELS):
    puzzle = parse_board(board)
    goal, expanded = gui.bfs(puzzle)
    rows.append((i + 1, goal.g if goal else -1, expanded))
    print("     level %d  cost=%-3d expanded=%d" % rows[-1])

costs = [c for _, c, _ in rows]
check("solution cost never decreases", all(costs[i] <= costs[i + 1]
                                            for i in range(len(costs) - 1)),
      "costs=%s" % costs)
check("6 levels present", len(LEVELS) == 6)
check("level names removed from levels.py",
      not hasattr(__import__("levels"), "LEVEL_NAMES"))


# ---------------------------------------------------------------------------
print("\n== 2. SPEED + really speeds up (the old code was inverted) ==")
gui.AUDIO = Recorder()
puzzle, player, _ = gui.load_level(0, 700)

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


# ---------------------------------------------------------------------------
print("\n== 3. sound effects fire on the right actions ==")
gui.AUDIO = Recorder()
puzzle, player, _ = gui.load_level(0, 1)          # 1 ms -> finishes instantly
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
puzzle, player, _ = gui.load_level(0, 500)
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


# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
print("\n== 5. window / fullscreen geometry ==")
puzzles = [parse_board(b) for b in LEVELS]
max_w = max(p.width for p in puzzles)
max_h = max(p.height for p in puzzles)
width, height, board_area, panel = gui.compute_geometry(max_w, max_h)
print("     logical frame = %dx%d" % (width, height))
check("the panel grew for the fullscreen button", gui.BUTTON_ROWS == 5)
check("the hint list documents F11", gui.HINT_LINES == 6)

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


# ---------------------------------------------------------------------------
print("\n== 6. frame renders with the new header ==")
os.makedirs(os.path.join(os.environ.get("TEMP", "."), "sfp"), exist_ok=True)
out = os.path.join(os.environ["TEMP"], "sfp")
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
puzzle, player, deco = gui.load_level(0, 400)
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


# ---------------------------------------------------------------------------
print("\n== 7. successor rules: the model really matches the spec ==")
from boxgame import Node, SokobanPuzzle            # noqa: E402
from search import (bfs, astar, h1, h2, h3,        # noqa: E402
                    SearchResult, DEFAULT_NODE_LIMIT, DEFAULT_TIMEOUT)
from figure4_boards import boards as figure4_boards  # noqa: E402


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


# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
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

for label, heu in (("h1", h1), ("h2", h2), ("h3", h3)):
    res = astar(tiny, heu)
    check("A*(%s) still reaches the goal" % label,
          res.goal is not None and not res.timed_out, str(res.cost))


# ---------------------------------------------------------------------------
print("\n== 11. A* vs BFS, SearchResult, and honest limits ==")
for name, ascii_board in figure4_boards():
    st = parse_board(ascii_board)
    bfs_goal, _ = bfs(st)
    costs = {}
    reached = True
    for label, heu in (("h1", h1), ("h2", h2), ("h3", h3)):
        res = astar(st, heu)
        costs[label] = res.cost
        reached = reached and res.goal is not None and not res.timed_out
    check("%s: all three A* variants reach a goal" % name, reached,
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
check("SearchResult carries .seconds", res.seconds > 0.0,
      "%.6f" % res.seconds)
check("a finished run reports timed_out False", res.timed_out is False)
check("SearchResult.cost mirrors goal.g", res.cost == res.goal.g)
check("SearchResult.goal mirrors the pair", res.goal is res[0])

# --- node limit must be honoured exactly --------------------------------
limit_board = parse_board(list(figure4_boards())[-1][1])   # exemple5
limited = astar(limit_board, h1, node_limit=25, timeout=None)
check("node_limit=25 stops at exactly 25 expansions",
      limited[1] == 25, str(limited[1]))
check("a node limit is reported as timed_out",
      limited.timed_out is True and limited.goal is None)

# --- wall clock limit ---------------------------------------------------
rushed = astar(limit_board, h1, node_limit=None, timeout=1e-4)
check("a 0.1 ms timeout stops the search",
      rushed.timed_out is True and rushed.goal is None,
      "expanded=%d" % rushed[1])
check("a timeout still reports honest counts",
      rushed[1] >= 0 and rushed.generated >= 1,
      "expanded=%d generated=%d" % (rushed[1], rushed.generated))

# --- no solution at all -------------------------------------------------
unsolvable = parse_board(["OOOOOO", "OBOOOO", "OO    ", "OSR  O", "OOOOOO"])
u_goal, u_expanded = bfs(unsolvable)
check("BFS reports no solution", u_goal is None, str(u_expanded))
u_res = astar(unsolvable, h1, node_limit=DEFAULT_NODE_LIMIT,
              timeout=DEFAULT_TIMEOUT)
check("A* reports NO-SOLUTION, not a timeout",
      u_res.goal is None and u_res.timed_out is False)
check("A* really exhausted the frontier", u_res[1] > 0,
      str(u_res[1]))

# --- bfs keeps its old contract ----------------------------------------
plain = bfs(parse_board(["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"]))
check("bfs() without stats still returns a plain pair",
      len(plain) == 2 and not hasattr(plain, "generated"))
stats = {}
bfs(parse_board(["OOOOOO", "O S  O", "O BR O", "O    O", "OOOOOO"]), stats)
check("bfs() fills the optional stats dict",
      stats.get("generated", 0) >= 1 and stats.get("seconds", 0.0) > 0.0
      and stats.get("timed_out") is False, str(stats))
check("the published limits are the ones we tested against",
      DEFAULT_NODE_LIMIT == 400000 and DEFAULT_TIMEOUT == 15.0,
      "%s / %s" % (DEFAULT_NODE_LIMIT, DEFAULT_TIMEOUT))


# ---------------------------------------------------------------------------
if REAL:
    print("\n== 12. real fullscreen: button + F11 ==")
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

pygame.quit()

print("\n%s  (%d failed)" % ("ALL TESTS PASSED" if not FAILURES
                             else "FAILURES: " + ", ".join(FAILURES),
                             len(FAILURES)))
sys.exit(1 if FAILURES else 0)
