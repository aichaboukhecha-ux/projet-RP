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
if REAL:
    print("\n== 7. real fullscreen: button + F11 ==")
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
