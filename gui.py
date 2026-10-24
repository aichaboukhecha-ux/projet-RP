"""Sokoban Fairy Puzzle - Sokoban graphical interface (Part C).

A whimsical pixel-art fairy-forest GUI built on top of the existing solver.

    Run:  python gui.py

It uses ONLY the public API already present in the project:

    from boxgame import Level, parse_board      # board + SokobanPuzzle
    from search   import bfs, astar             # solvers

Nothing in boxgame.py, search.py, main.py or puzzle.py is modified.
"""

import math
import os
import random
import sys
import time

import pygame

from boxgame import parse_board
from levels import LEVELS
from search import bfs, astar


def log(message):
    """Print only when a console exists (a windowed .exe has no stdout)."""
    if getattr(sys, "stdout", None) is not None:
        print(message)


def resource_dir():
    """Folder holding ./assets - works as a script and inside a frozen exe."""
    if getattr(sys, "frozen", False):
        # PyInstaller: bundled data lives in sys._MEIPASS (onefile temp dir)
        # or next to the exe (onedir).
        return getattr(sys, "_MEIPASS",
                       os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


def enable_dpi_awareness():
    """Render at true physical pixels so the OS does not blur the pixel art
    and the window always fits the screen."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# --------------------------------------------------------------------------
# Layout constants
# --------------------------------------------------------------------------
TILE = 64              # one logical grid cell (px)
PLAYER_SPRITE = 48     # fairy displayed size (16x16 -> 48x48, exact 3x)
SPRITE = 32            # goal/target sprite displayed size (16x16 -> 32x32)
BOX_SPRITE = 48        # wooden box displayed size
MARGIN = 24
HEADER_H = 76
PANEL_W = 300
PANEL_PAD = 18
BUTTON_H = 40
BUTTON_GAP = 10
ROW_H = 42             # stats row pitch in the side panel

# --- side-panel vertical layout (all relative to panel_rect.y) ------------
STATS_TOP = PANEL_PAD
STAT_ROWS = 7                       # LEVEL, ALGORITHM, STEP, COST, ...
STATS_H = STAT_ROWS * ROW_H
BAR_Y = STATS_TOP + STATS_H + 4
CONTROLS_Y = BAR_Y + 14 + 14
BUTTONS_TOP = CONTROLS_Y + 30
BUTTON_ROWS = 6                     # transport, level, algorithm, fullscreen
BUTTONS_H = BUTTON_ROWS * BUTTON_H + (BUTTON_ROWS - 1) * BUTTON_GAP
HINTS_Y = BUTTONS_TOP + BUTTONS_H + 22
HINT_LINES = 6
HINTS_H = HINT_LINES * 21
PANEL_MIN_H = HINTS_Y + HINTS_H + PANEL_PAD

# ms between animation steps.  Index 0 is the SLOWEST, the last entry the
# quickest, so a higher speed_index always means a faster playback.
SPEEDS = [1000, 700, 450, 250, 120, 60, 30]
DEFAULT_SPEED = 1                        # index -> 700 ms

ACTION_TO_DIR = {
    "UP": "up",
    "DOWN": "down",
    "LEFT": "left",
    "RIGHT": "right",
}

TITLE = "SOKOBAN FAIRY PUZZLE"   # shown in the header, splash and caption
CAPTION = "Sokoban Fairy Puzzle"

# --------------------------------------------------------------------------
# Palette - dark purple / lavender / forest green / warm brown
# --------------------------------------------------------------------------
BG_DEEP      = (24, 15, 36)      # window background
PANEL_BG     = (43, 28, 64)      # side panel
PANEL_EDGE   = (110, 84, 154)
FLOOR_A      = (54, 38, 74)      # dark purple stone
FLOOR_B      = (60, 43, 82)
FLOOR_EDGE   = (44, 30, 61)
WALL_FALL    = (76, 47, 73)
LAVENDER     = (198, 175, 245)
LAVENDER_DIM = (139, 116, 186)
PINK         = (240, 150, 205)
GREEN        = (96, 168, 110)
BROWN        = (139, 90, 43)
TEXT         = (238, 230, 255)
TEXT_DIM     = (168, 152, 199)
AMBER        = (240, 196, 96)
GOLD         = (255, 220, 130)

STATUS_COLORS = {
    "READY":     LAVENDER,
    "SOLVING":   AMBER,
    "PLAYING":   GREEN,
    "PAUSED":    AMBER,
    "SOLVED":    GOLD,
    "NO SOLUTION": PINK,
}


# --------------------------------------------------------------------------
# Asset loading (never crashes - every failure falls back to a drawn shape)
# --------------------------------------------------------------------------
class Assets:
    """Loads PNG / TTF files from ./assets and pre-scales them for the board."""

    def __init__(self, base_dir):
        self.base = base_dir
        self.player = {}          # direction -> Surface (32x32) or None
        self.wall = None
        self.target = None
        self.box = None
        self.box_on_target = None
        self.mushroom = None
        self.fonts = {}

        for direction in ("up", "down", "left", "right"):
            self.player[direction] = self._scaled(
                "player_%s.png" % direction, (PLAYER_SPRITE, PLAYER_SPRITE))

        self.wall = self._scaled("wall.png", (TILE, TILE))
        self.target = self._scaled("target.png", (SPRITE, SPRITE))

        box = self._load("box.png")
        if box is not None:
            box = self._crop(box)
            box = pygame.transform.scale(box, (37, 37))     # true pixel grid
            self.box = pygame.transform.scale(box, (BOX_SPRITE, BOX_SPRITE))

        mush = self._load("mushroom.png")
        if mush is not None:
            mush = self._crop(mush)
            # keep the aspect ratio: never stretch non-uniformly
            h = 34
            w = max(1, int(round(mush.get_width() * h / mush.get_height())))
            self.mushroom = pygame.transform.scale(mush, (w, h))

    # -- helpers -----------------------------------------------------------
    def _load(self, filename):
        path = os.path.join(self.base, filename)
        if not os.path.isfile(path):
            return None
        try:
            image = pygame.image.load(path)
        except pygame.error:
            return None
        # convert_alpha() needs an active display mode.  Without one (a
        # headless test harness) keep the unconverted surface rather than
        # silently turning every sprite into a fallback shape.
        try:
            return image.convert_alpha()
        except pygame.error:
            return image

    def _scaled(self, filename, size):
        image = self._load(filename)
        if image is None:
            return None
        return pygame.transform.scale(image, size)

    @staticmethod
    def _crop(surface):
        """Trim transparent padding so the sprite fills its cell."""
        rect = surface.get_bounding_rect()
        return surface.subsurface(rect) if rect.width and rect.height else surface

    def font(self, name, size):
        """TTF from assets/fonts, with a safe system-font fallback."""
        key = (name, size)
        if key in self.fonts:
            return self.fonts[key]
        path = os.path.join(self.base, "fonts", name)
        try:
            font = pygame.font.Font(path, size) if os.path.isfile(path) \
                else pygame.font.SysFont(None, size)
        except (pygame.error, OSError):
            font = pygame.font.SysFont(None, size)
        self.fonts[key] = font
        return font


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# Audio - optional.  Every call degrades to a no-op when there is no sound
# device, so the game still runs (and the tests still pass) without one.
# --------------------------------------------------------------------------
class Audio:
    """Loads the WAVs shipped in ``assets/sounds`` and plays them on demand."""

    SFX = ("click", "step", "push", "target", "undo", "bump", "win")

    def __init__(self, base_dir):
        self.base = base_dir
        self.sounds = {}
        self.ok = False
        self.muted = False

        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
        except Exception:                      # no audio device present
            log("audio: mixer unavailable, running silent")
            return

        for name in self.SFX:
            path = os.path.join(base_dir, "sounds", name + ".wav")
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
                self.sounds[name].set_volume(0.55)
            except Exception as exc:
                log("audio: cannot load %s (%s)" % (name, exc))

        self.ok = bool(self.sounds)

    def play(self, name):
        """Fire-and-forget.  Silently does nothing when unavailable."""
        if self.muted:
            return
        snd = self.sounds.get(name)
        if snd is None:
            return
        try:
            snd.play()
        except Exception:
            pass

    def start_music(self):
        if not self.ok or self.muted:
            return
        path = os.path.join(self.base, "sounds", "music.wav")
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.25)
            pygame.mixer.music.play(-1, 0.0)       # loop forever
        except Exception as exc:
            log("audio: music unavailable (%s)" % exc)

    def stop_music(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass


AUDIO = None            # set by main(); kept global so SolutionPlayer can bark


def sfx(name):
    """Play a sound effect if audio is up."""
    if AUDIO is not None:
        AUDIO.play(name)


# Solution playback (timer based - no time.sleep() anywhere)
# --------------------------------------------------------------------------
class SolutionPlayer:
    """Steps through the states returned by Node.getPath()."""

    READY, PLAYING, PAUSED, SOLVED = "READY", "PLAYING", "PAUSED", "SOLVED"

    def __init__(self, path, actions, cost, expanded, delay):
        self.path = path                  # list[SokobanPuzzle], index 0 = start
        self.actions = actions            # list[str]  "UP"/"DOWN"/"LEFT"/"RIGHT"
        self.cost = cost                  # goal.g
        self.expanded = expanded          # nodes expanded by selected search
        self.total = len(actions)         # number of steps
        self.delay = delay                # ms per step
        self.speed_index = SPEEDS.index(delay) if delay in SPEEDS \
            else DEFAULT_SPEED
        self.step = 0
        self.status = self.READY
        self.facing = "down"
        self._last = pygame.time.get_ticks()

    # -- current frame -----------------------------------------------------
    @property
    def state(self):
        return self.path[self.step]

    def _sync_facing(self):
        if self.step == 0:
            self.facing = "down"
        else:
            self.facing = ACTION_TO_DIR.get(self.actions[self.step - 1],
                                            self.facing)

    def _advance(self):
        """Advance one step and fire the sound effect that matches it."""
        prev = self.path[self.step]
        self.step += 1
        self._sync_facing()

        cur = self.path[self.step]
        moved = [b for b in cur.boxes if b not in prev.boxes]
        if moved:                                  # a box was pushed
            sfx("push")
            if any(box in cur.targets for box in moved):
                sfx("target")                      # ...and it landed home
        else:
            sfx("step")

    def _finish(self):
        if self.status != self.SOLVED:
            sfx("win")
        self.status = self.SOLVED

    # -- commands ----------------------------------------------------------
    def update(self, now):
        if self.status != self.PLAYING:
            return
        while (self.step < self.total
               and now - self._last >= self.delay):
            self._last += self.delay
            self._advance()
        if self.step >= self.total and self.total > 0:
            self._finish()
        elif self.step >= self.total:
            self.status = self.READY

    def play(self):
        if self.total == 0:
            return
        if self.step >= self.total:
            self.reset()
        self.status = self.PLAYING
        self._last = pygame.time.get_ticks()

    def pause(self):
        if self.status == self.PLAYING:
            self.status = self.PAUSED

    def toggle(self):
        if self.status == self.PLAYING:
            self.pause()
        else:
            self.play()

    def reset(self):
        self.step = 0
        self.facing = "down"
        self.status = self.READY
        self._last = pygame.time.get_ticks()

    def next_step(self):
        if self.step < self.total:
            self._advance()
            if self.step >= self.total:
                self._finish()
            else:
                self.status = self.PAUSED

    def prev_step(self):
        if self.step > 0:
            self.step -= 1
            self._sync_facing()
            self.status = self.PAUSED
            sfx("undo")
        elif self.total > 0:
            sfx("bump")                       # already at the start

    def faster(self):
        """SPEED + : a lower ms delay, i.e. a quicker playback."""
        if self.speed_index < len(SPEEDS) - 1:
            self.speed_index += 1
            self.delay = SPEEDS[self.speed_index]
        else:
            sfx("bump")                       # already at maximum speed

    def slower(self):
        """SPEED - : a higher ms delay, i.e. a calmer playback."""
        if self.speed_index > 0:
            self.speed_index -= 1
            self.delay = SPEEDS[self.speed_index]
        else:
            sfx("bump")                       # already at minimum speed


# --------------------------------------------------------------------------
# Decorations - computed once, drawn under the game objects
# --------------------------------------------------------------------------
def pick_decorations(initial_state, path, rng_seed=20261017):
    """Cells that never hold a wall, target, box or the player.

    Decorations are therefore guaranteed to sit only on plain floor and can
    never hide a game object, even before considering the draw order.
    """
    busy = set(initial_state.walls)
    busy.update(initial_state.targets)
    for state in path:
        busy.add(state.player)
        busy.update(state.boxes)

    free = [(r, c)
            for r in range(initial_state.height)
            for c in range(initial_state.width)
            if (r, c) not in busy]

    rng = random.Random(rng_seed)
    rng.shuffle(free)

    kinds = ("mushroom", "flower", "moss", "sparkle")
    chosen = free[:max(2, len(free) // 3)]

    return [(pos, kinds[i % len(kinds)]) for i, pos in enumerate(chosen)]


# --------------------------------------------------------------------------
# Fallback drawings (used only when a PNG is missing)
# --------------------------------------------------------------------------
def draw_fallback_wall(surface, rect):
    pygame.draw.rect(surface, WALL_FALL, rect)
    pygame.draw.line(surface, (104, 70, 100), rect.topleft,
                     rect.topright, 2)
    pygame.draw.line(surface, (50, 30, 48), rect.bottomleft,
                     rect.bottomright, 3)
    for x in range(rect.x + TILE // 2, rect.right, TILE):
        pygame.draw.line(surface, (50, 30, 48), (x, rect.y),
                         (x, rect.bottom), 2)


def draw_fallback_player(surface, rect, facing):
    center = (rect.x + TILE // 2, rect.y + TILE // 2)
    pygame.draw.circle(surface, (176, 140, 235), center, PLAYER_SPRITE // 2)
    pygame.draw.circle(surface, (60, 44, 90), center, PLAYER_SPRITE // 2, 2)
    ex, ey = center
    dx = {"left": -5, "right": 5}.get(facing, 0)
    dy = {"up": -5, "down": 5}.get(facing, 0)
    for ox in (-5, 5):
        pygame.draw.circle(surface, (255, 255, 255), (ex + ox + dx // 3,
                                                      ey + dy // 3), 4)
        pygame.draw.circle(surface, (40, 30, 60),
                           (ex + ox + dx // 3, ey + dy // 3), 2)


def draw_fallback_box(surface, rect, on_target):
    inner = rect.inflate(-TILE + BOX_SPRITE, -TILE + BOX_SPRITE)
    inner.center = rect.center
    pygame.draw.rect(surface, BROWN, inner, border_radius=6)
    pygame.draw.rect(surface, (196, 143, 78), inner.inflate(-10, -10),
                     border_radius=4)
    pygame.draw.rect(surface, (92, 58, 26), inner, 3, border_radius=6)
    if on_target:
        pygame.draw.rect(surface, PINK, inner, 3, border_radius=6)


def draw_fallback_target(surface, rect, glow):
    center = rect.center
    pygame.draw.circle(surface, glow, center, TILE // 3)
    pygame.draw.circle(surface, LAVENDER, center, TILE // 3, 2)


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------
def draw_header(surface, assets, width, level_index):
    """Title bar with the current level number and a few twinkling stars."""
    font = assets.font("PressStart2P-Regular.ttf", 18)
    title = font.render(TITLE, True, LAVENDER)
    shadow = font.render(TITLE, True, (60, 40, 92))
    x = (width - title.get_width()) // 2
    y = 14
    surface.blit(shadow, (x + 3, y + 3))
    surface.blit(title, (x, y))

    name_font = assets.font("Silkscreen-Regular.ttf", 17)
    name = name_font.render(
        "LEVEL %d / %d" % (level_index + 1, len(LEVELS)),
        True, PINK)
    surface.blit(name, name.get_rect(centerx=width // 2, y=46))

    t = pygame.time.get_ticks() / 1000.0
    rng = random.Random(7)
    for i in range(14):
        sx = rng.randint(8, width - 8)
        sy = rng.randint(6, HEADER_H - 6)
        alpha = 90 + int(90 * math.sin(t * 2 + i))
        star = pygame.Surface((4, 4), pygame.SRCALPHA)
        star.fill((220, 200, 255, max(30, min(255, alpha))))
        surface.blit(star, (sx, sy))


def draw_floor_and_walls(surface, state, assets, board_origin):
    ox, oy = board_origin
    for row in range(state.height):
        for col in range(state.width):
            rect = pygame.Rect(ox + col * TILE, oy + row * TILE, TILE, TILE)
            shade = FLOOR_A if (row + col) % 2 == 0 else FLOOR_B
            pygame.draw.rect(surface, shade, rect)
            pygame.draw.rect(surface, FLOOR_EDGE, rect, 1)

            if (row, col) in state.walls:
                if assets.wall is not None:
                    surface.blit(assets.wall, rect)
                else:
                    draw_fallback_wall(surface, rect)


def draw_decorations(surface, assets, decorations, board_origin, now):
    ox, oy = board_origin
    pulse = 0.5 + 0.5 * math.sin(now / 400.0)

    for (row, col), kind in decorations:
        rect = pygame.Rect(ox + col * TILE, oy + row * TILE, TILE, TILE)

        if kind == "mushroom" and assets.mushroom is not None:
            sprite = assets.mushroom
            surface.blit(sprite, (rect.x + (TILE - sprite.get_width()) // 2,
                                  rect.bottom - sprite.get_height() - 6))

        elif kind == "flower":
            base = (rect.x + TILE // 2, rect.bottom - 10)
            pygame.draw.line(surface, (74, 138, 84), base,
                             (base[0], base[1] - 10), 2)
            petal = PINK if (row + col) % 2 else LAVENDER
            for dx, dy in ((0, -4), (-4, 0), (4, 0), (0, 4)):
                pygame.draw.circle(surface, petal,
                                   (base[0] + dx, base[1] - 10 + dy), 3)
            pygame.draw.circle(surface, GOLD, (base[0], base[1] - 10), 2)

        elif kind == "moss":
            moss = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            pygame.draw.ellipse(moss, (74, 138, 84, 110),
                                (10, TILE - 22, TILE - 20, 16))
            pygame.draw.ellipse(moss, (96, 168, 110, 130),
                                (18, TILE - 18, TILE - 30, 10))
            surface.blit(moss, rect.topleft)

        else:  # tiny floor sparkle
            sparkle = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            cx, cy = rect.centerx - 8, rect.centery - 6
            a = int(70 + 90 * pulse)
            pygame.draw.line(sparkle, (226, 210, 255, a), (cx - 4, cy),
                             (cx + 4, cy), 2)
            pygame.draw.line(sparkle, (226, 210, 255, a), (cx, cy - 4),
                             (cx, cy + 4), 2)
            surface.blit(sparkle, rect.topleft)


def draw_targets(surface, assets, state, board_origin, now):
    ox, oy = board_origin
    pulse = 0.5 + 0.5 * math.sin(now / 350.0)

    for (row, col) in sorted(state.targets):
        rect = pygame.Rect(ox + col * TILE, oy + row * TILE, TILE, TILE)

        glow = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        radius = 24 + int(3 * pulse)
        pygame.draw.circle(glow, (214, 150, 235, 70 + int(45 * pulse)),
                           rect.center, radius)
        pygame.draw.circle(glow, (245, 175, 220, 120 + int(60 * pulse)),
                           rect.center, radius - 7)
        surface.blit(glow, rect.topleft)

        if assets.target is not None:
            sprite = assets.target
            surface.blit(sprite, sprite.get_rect(center=rect.center))
        else:
            draw_fallback_target(surface, rect, PINK)


def draw_boxes(surface, assets, state, board_origin):
    ox, oy = board_origin

    for (row, col) in sorted(state.boxes):
        rect = pygame.Rect(ox + col * TILE, oy + row * TILE, TILE, TILE)
        on_target = (row, col) in state.targets

        shadow = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (18, 10, 28, 150),
                            (rect.x + 12, rect.bottom - 16, TILE - 24, 12))
        surface.blit(shadow, rect.topleft)

        if on_target:                       # glow ring under the box
            ring = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 200, 240, 190), rect.center,
                               BOX_SPRITE // 2 + 4, 3)
            surface.blit(ring, rect.topleft)

        if assets.box is not None:
            sprite = assets.box
            surface.blit(sprite, sprite.get_rect(center=rect.center))
        else:
            draw_fallback_box(surface, rect, on_target)

        if on_target:
            border = pygame.Rect(0, 0, BOX_SPRITE, BOX_SPRITE)
            border.center = rect.center
            pygame.draw.rect(surface, GOLD, border, 2, border_radius=4)


def draw_player(surface, assets, state, facing, board_origin):
    ox, oy = board_origin
    row, col = state.player
    rect = pygame.Rect(ox + col * TILE, oy + row * TILE, TILE, TILE)

    shadow = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (18, 10, 28, 130),
                        (rect.x + 14, rect.bottom - 15, TILE - 28, 10))
    surface.blit(shadow, rect.topleft)

    sprite = assets.player.get(facing)
    if sprite is not None:
        surface.blit(sprite, sprite.get_rect(center=rect.center))
    else:
        draw_fallback_player(surface, rect, facing)


def draw_board(surface, state, assets, facing, decorations, board_origin):
    draw_floor_and_walls(surface, state, assets, board_origin)
    draw_decorations(surface, assets, decorations, board_origin,
                     pygame.time.get_ticks())
    draw_targets(surface, assets, state, board_origin, pygame.time.get_ticks())
    draw_boxes(surface, assets, state, board_origin)
    draw_player(surface, assets, state, facing, board_origin)

    frame = pygame.Rect(board_origin[0], board_origin[1],
                        state.width * TILE, state.height * TILE)
    pygame.draw.rect(surface, LAVENDER_DIM, frame, 3)


# --------------------------------------------------------------------------
# Buttons
# --------------------------------------------------------------------------
class Button:
    def __init__(self, key, rect, label):
        self.key = key
        self.rect = rect
        self.label = label

    def draw(self, surface, font, mouse):
        hovered = self.rect.collidepoint(mouse)
        base = (86, 62, 128) if hovered else (63, 45, 94)
        pygame.draw.rect(surface, base, self.rect, border_radius=8)
        pygame.draw.rect(surface, LAVENDER if hovered else LAVENDER_DIM,
                         self.rect, 2, border_radius=8)
        text = font.render(self.label, True, TEXT if hovered else TEXT_DIM)
        surface.blit(text, text.get_rect(center=self.rect.center))


def build_buttons(panel_rect):
    x = panel_rect.x + PANEL_PAD
    top = panel_rect.y + BUTTONS_TOP
    inner = PANEL_W - 2 * PANEL_PAD
    col_w = (inner - BUTTON_GAP) // 2

    def cell(col, row):
        return pygame.Rect(x + col * (col_w + BUTTON_GAP),
                           top + row * (BUTTON_H + BUTTON_GAP),
                           col_w, BUTTON_H)

    return {
        "play":      Button("play", cell(0, 0), "PLAY"),
        "reset":     Button("reset", cell(1, 0), "RESET"),
        "prev":      Button("prev", cell(0, 1), "<<  PREV"),
        "next":      Button("next", cell(1, 1), "NEXT  >>"),
        "slower":    Button("slower", cell(0, 2), "SPEED -"),
        "faster":    Button("faster", cell(1, 2), "SPEED +"),
        "level_prev": Button("level_prev", cell(0, 3), "LEVEL -"),
        "level_next": Button("level_next", cell(1, 3), "LEVEL +"),
        "fullscreen": Button("fullscreen",
                             pygame.Rect(x, top + 4 * (BUTTON_H + BUTTON_GAP),
                                         inner, BUTTON_H),
                             "FULLSCREEN"),
        "algorithm": Button("algorithm",
                            pygame.Rect(x, top + 5 * (BUTTON_H + BUTTON_GAP),
                                        inner, BUTTON_H),
                            "SEARCH: BFS"),
    }


# --------------------------------------------------------------------------
# Side panel
# --------------------------------------------------------------------------
def draw_panel(surface, panel_rect, assets, player, buttons, level_index,
               mouse=None):
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=12)
    pygame.draw.rect(surface, PANEL_EDGE, panel_rect, 2, border_radius=12)

    label_font = assets.font("Silkscreen-Regular.ttf", 15)
    value_font = assets.font("Silkscreen-Bold.ttf", 22)
    small_font = assets.font("Silkscreen-Regular.ttf", 15)
    button_font = assets.font("Silkscreen-Bold.ttf", 16)

    x = panel_rect.x + PANEL_PAD
    y = panel_rect.y + STATS_TOP

    rows = [
        ("LEVEL",            "%d / %d" % (level_index + 1, len(LEVELS)),
         LAVENDER),
        ("ALGORITHM",        player.algorithm, LAVENDER),
        ("STEP",             "%d / %d" % (player.step, player.total), TEXT),
        ("SOLUTION COST",    str(player.cost), TEXT),
        ("STATUS",           player.status,
                             STATUS_COLORS.get(player.status, TEXT)),
        ("EXPANDED NODES",   str(player.expanded), TEXT),
        ("GENERATED NODES",  "n/a", TEXT_DIM),
    ]

    for label, value, color in rows:
        surface.blit(label_font.render(label, True, TEXT_DIM), (x, y))
        surface.blit(value_font.render(str(value), True, color),
                     (x, y + 17))
        y += ROW_H

    # progress bar
    bar = pygame.Rect(x, panel_rect.y + BAR_Y,
                      PANEL_W - 2 * PANEL_PAD, 14)
    pygame.draw.rect(surface, (33, 21, 49), bar, border_radius=7)
    if player.total > 0:
        fill = bar.copy()
        fill.width = max(8, int(bar.width * player.step / player.total))
        pygame.draw.rect(surface, GREEN if player.status == "SOLVED"
                         else LAVENDER, fill, border_radius=7)
    pygame.draw.rect(surface, PANEL_EDGE, bar, 1, border_radius=7)

    # controls
    surface.blit(label_font.render("CONTROLS", True, TEXT_DIM),
                 (x, panel_rect.y + CONTROLS_Y))
    speed_text = "%d ms" % player.delay
    speed_surf = small_font.render(speed_text, True, LAVENDER)
    surface.blit(speed_surf, (panel_rect.right - PANEL_PAD
                              - speed_surf.get_width(),
                              panel_rect.y + CONTROLS_Y))
    buttons["play"].label = ("PAUSE" if player.status == "PLAYING"
                             else "PLAY")
    buttons["level_prev"].label = "LEVEL -"
    buttons["level_next"].label = "LEVEL +"
    buttons["algorithm"].label = "SEARCH: %s  (CLICK)" % player.algorithm
    if mouse is None:
        mouse = pygame.mouse.get_pos()
    for button in buttons.values():
        button.draw(surface, button_font, mouse)

    # help lines
    y = panel_rect.y + HINTS_Y
    hints = [
        "SPACE   play / pause",
        "R       reset",
        "< / >   prev / next step",
        "- / +   speed   [ ] level",
        "F11     fullscreen",
        "ESC     quit",
    ]
    for hint in hints:
        surface.blit(small_font.render(hint, True, TEXT_DIM), (x, y))
        y += 21


def draw_status_message(surface, assets, rect, player):
    if player.status == "SOLVED":
        font = assets.font("PressStart2P-Regular.ttf", 14)
        text = font.render("PUZZLE SOLVED!", True, GOLD)
        pos = text.get_rect(midtop=(rect.centerx, rect.bottom + 14))
        surface.blit(text, pos)
    elif player.status == "NO SOLUTION":
        font = assets.font("PressStart2P-Regular.ttf", 12)
        text = font.render("NO SOLUTION", True, PINK)
        surface.blit(text, text.get_rect(center=rect.center))


def draw_splash(surface, assets, text):
    surface.fill(BG_DEEP)
    big = assets.font("PressStart2P-Regular.ttf", 18)
    small = assets.font("Silkscreen-Regular.ttf", 20)
    title = big.render(TITLE, True, LAVENDER)
    line = small.render(text, True, TEXT_DIM)
    surface.blit(title, title.get_rect(centerx=surface.get_width() // 2,
                                       centery=surface.get_height() // 2 - 20))
    surface.blit(line, line.get_rect(centerx=surface.get_width() // 2,
                                     centery=surface.get_height() // 2 + 24))
    pygame.display.flip()


# --------------------------------------------------------------------------
# Window geometry (adapts to the board size)
# --------------------------------------------------------------------------
def max_board_size(puzzles):
    """Widest / tallest board across all levels (drives one fixed window)."""
    return (max(p.width for p in puzzles),
            max(p.height for p in puzzles))


def compute_geometry(max_w, max_h):
    """One window big enough for every level, so it never resizes mid-play."""
    board_w = max_w * TILE
    board_h = max_h * TILE
    content_h = max(board_h, PANEL_MIN_H)

    width = MARGIN + board_w + MARGIN + PANEL_W + MARGIN
    height = HEADER_H + content_h + MARGIN

    board_area = pygame.Rect(MARGIN, HEADER_H + (content_h - board_h) // 2,
                             board_w, board_h)
    panel = pygame.Rect(MARGIN + board_w + MARGIN, HEADER_H + 8,
                        PANEL_W, content_h - 8)
    return width, height, board_area, panel


def board_origin(board_area, state):
    """Centre this level's board inside the fixed board area."""
    w = state.width * TILE
    h = state.height * TILE
    return (board_area.x + (board_area.width - w) // 2,
            board_area.y + (board_area.height - h) // 2)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def load_level(index, delay, algorithm="BFS"):
    """Parse and solve one level with BFS or A*."""
    puzzle = parse_board(LEVELS[index])

    started = time.perf_counter()
    solver = bfs if algorithm == "BFS" else astar
    goal_node, expanded = solver(puzzle)
    elapsed = time.perf_counter() - started
    log("Level %d: %s %d expanded nodes in %.4f s"
        % (index + 1, algorithm, expanded, elapsed))

    if goal_node is None:
        # solver failed: keep the window usable, but never fake a solution
        player = SolutionPlayer([puzzle], [], 0, expanded, delay)
        player.status = "NO SOLUTION"
        player.total = 0
    else:
        player = SolutionPlayer(goal_node.getPath(),      # list[SokobanPuzzle]
                                goal_node.getSolution(),  # list[str]
                                goal_node.g, expanded, delay)

    player.algorithm = algorithm

    return puzzle, player, pick_decorations(puzzle, player.path)


def main():
    global AUDIO

    enable_dpi_awareness()

    pygame.init()

    assets_dir = os.path.join(resource_dir(), "assets")

    # parse every level once: they drive the fixed window geometry
    puzzles = [parse_board(b) for b in LEVELS]
    max_w, max_h = max_board_size(puzzles)
    width, height, board_area, panel_rect = compute_geometry(max_w, max_h)

    # desktop resolution, captured before we ever enter fullscreen
    info = pygame.display.Info()
    desktop = (max(1, info.current_w), max(1, info.current_h))

    # Window: as large as asked, but never larger than the screen.  `frame`
    # below is letterboxed into whatever window we get, so the whole layout
    # stays visible even on a small display.
    if desktop[0] >= width and desktop[1] >= height:
        win_w, win_h = width, height
        if desktop[0] > width and desktop[1] > height:
            os.environ["SDL_VIDEO_WINDOW_POS"] = "%d,%d" % (
                (desktop[0] - width) // 2, (desktop[1] - height) // 2)
    else:
        fit = min(desktop[0] / width, desktop[1] / height)
        win_w, win_h = max(1, int(width * fit)), max(1, int(height * fit))

    surface = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption(CAPTION)

    assets = Assets(assets_dir)
    AUDIO = Audio(assets_dir)

    # Everything is drawn into `frame` at one fixed logical size and then
    # scaled into the window.  That is what makes fullscreen (and small
    # screens) work without touching a single drawing routine.
    frame = pygame.Surface((width, height))
    fullscreen = False
    present_rect = pygame.Rect(0, 0, width, height)

    def update_present():
        """Where `frame` lands inside the real window (aspect-fit)."""
        nonlocal present_rect
        ww, wh = surface.get_size()
        if ww == width and wh == height:
            present_rect = pygame.Rect(0, 0, width, height)
            return
        scale = min(ww / width, wh / height)
        tw, th = max(1, int(width * scale)), max(1, int(height * scale))
        present_rect = pygame.Rect((ww - tw) // 2, (wh - th) // 2, tw, th)

    def to_logical(pos):
        """Window pixels -> logical frame pixels, for mouse hit-testing."""
        if present_rect.width <= 0 or present_rect.height <= 0:
            return pos
        return ((pos[0] - present_rect.x) * width / present_rect.width,
                (pos[1] - present_rect.y) * height / present_rect.height)

    def set_fullscreen(flag):
        """F11 / the FULLSCREEN button.  Never raises: worst case we stay put."""
        nonlocal surface, fullscreen
        try:
            if flag:
                surface = pygame.display.set_mode(desktop, pygame.FULLSCREEN)
            else:
                surface = pygame.display.set_mode((win_w, win_h))
            fullscreen = flag
            log("display: %s (%dx%d)" %
                ("fullscreen" if flag else "windowed",
                 surface.get_size()[0], surface.get_size()[1]))
        except Exception as exc:
            log("fullscreen: unavailable (%s)" % exc)
            fullscreen = False
            surface = pygame.display.get_surface() or surface
        update_present()
        buttons["fullscreen"].label = "WINDOWED" if fullscreen else "FULLSCREEN"

    def present():
        if present_rect.size != surface.get_size():
            surface.fill(BG_DEEP)
        if present_rect.size == (width, height):
            surface.blit(frame, present_rect.topleft)
        else:
            surface.blit(pygame.transform.scale(frame, present_rect.size),
                         present_rect.topleft)
        pygame.display.flip()

    update_present()
    AUDIO.start_music()

    # Show the selected solver while the initial level is being solved.
    algorithm = "BFS"
    draw_splash(frame, assets, "Solving with %s ..." % algorithm)
    present()

    level_index = 0
    delay = SPEEDS[DEFAULT_SPEED]
    puzzle, player, decorations = load_level(level_index, delay, algorithm)
    buttons = build_buttons(panel_rect)

    def switch_level(new_index):
        """Move to another level, keeping the current animation speed."""
        nonlocal level_index, puzzle, player, decorations
        level_index = (new_index % len(LEVELS))
        puzzle, player, decorations = load_level(level_index, delay, algorithm)
        sfx("click")

    def toggle_algorithm():
        """Switch solver and compute a fresh solution for the current level."""
        nonlocal algorithm, puzzle, player, decorations
        algorithm = "A*" if algorithm == "BFS" else "BFS"
        draw_splash(frame, assets, "Solving with %s ..." % algorithm)
        present()
        puzzle, player, decorations = load_level(level_index, delay, algorithm)
        sfx("click")

    clock = pygame.time.Clock()
    running = True

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hit = to_logical(event.pos)
                for button in buttons.values():
                    if button.rect.collidepoint(hit):
                        sfx("click")
                        if button.key == "play":
                            player.toggle()
                        elif button.key == "reset":
                            player.reset()
                        elif button.key == "prev":
                            player.prev_step()
                        elif button.key == "next":
                            player.next_step()
                        elif button.key == "faster":
                            player.faster()
                            delay = player.delay
                        elif button.key == "slower":
                            player.slower()
                            delay = player.delay
                        elif button.key == "level_next":
                            switch_level(level_index + 1)
                        elif button.key == "level_prev":
                            switch_level(level_index - 1)
                        elif button.key == "fullscreen":
                            set_fullscreen(not fullscreen)
                        elif button.key == "algorithm":
                            toggle_algorithm()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_F11, pygame.K_f):
                    set_fullscreen(not fullscreen)
                elif event.key == pygame.K_SPACE:
                    player.toggle()
                elif event.key == pygame.K_r:
                    player.reset()
                elif event.key in (pygame.K_LEFT, pygame.K_COMMA):
                    player.prev_step()
                elif event.key in (pygame.K_RIGHT, pygame.K_PERIOD):
                    player.next_step()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS,
                                   pygame.K_UP):
                    player.faster()
                    delay = player.delay
                elif event.key in (pygame.K_MINUS, pygame.K_DOWN):
                    player.slower()
                    delay = player.delay
                elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_n,
                                   pygame.K_PAGEDOWN):
                    switch_level(level_index + 1)
                elif event.key in (pygame.K_LEFTBRACKET, pygame.K_p,
                                   pygame.K_PAGEUP):
                    switch_level(level_index - 1)
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    switch_level(event.key - pygame.K_1)

        player.update(now)

        origin = board_origin(board_area, player.state)

        # ---- draw into the logical frame --------------------------------
        frame.fill(BG_DEEP)
        draw_header(frame, assets, width, level_index)
        draw_board(frame, player.state, assets, player.facing,
                   decorations, origin)
        draw_panel(frame, panel_rect, assets, player, buttons, level_index,
                   mouse=to_logical(pygame.mouse.get_pos()))
        draw_status_message(frame, assets,
                            pygame.Rect(origin[0], origin[1],
                                        player.state.width * TILE,
                                        player.state.height * TILE),
                            player)

        present()
        clock.tick(60)

    AUDIO.stop_music()
    pygame.quit()


if __name__ == "__main__":
    main()
