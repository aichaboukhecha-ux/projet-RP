"""The 13 levels: 6 original, then the 5 boards of Figure 4, then the 2 of Figure 7.

O wall, R player, B box, S target, . player on target, * box on target.
"""

from boxgame import Level as ORIGINAL_LEVEL
from figure4_boards import FIGURE4, FIGURE4_ORDER
from figure7_boards import FIGURE7, FIGURE7_ORDER


LEVELS = [
    # 1 - easiest: 1 box, 7 pushes
    [
        "OOOOOOO",
        "OR    O",
        "O     O",
        "O  B  O",
        "O   S O",
        "OOOOOOO",
    ],

    # 2 - 1 box, walled column
    [
        "OOOOOOOO",
        "OR     O",
        "O  O   O",
        "O  B   O",
        "O  O S O",
        "O      O",
        "O      O",
        "OOOOOOOO",
    ],

    # 3 - 2 boxes, 8 pushes
    [
        "OOOOOOOO",
        "OR   O O",
        "O B    O",
        "O   OO O",
        "O S    O",
        "O   B SO",
        "O      O",
        "OOOOOOOO",
    ],

    # 4 - the team's original board
    ORIGINAL_LEVEL,

    # 5 - two clean lanes, 12 pushes
    [
        "OOOOOOOO",
        "OR     O",
        "O B  S O",
        "O      O",
        "O B  S O",
        "O      O",
        "OOOOOOOO",
    ],

    # 6 - hardest: 13 pushes, 1139 nodes
    [
        "OOOOOOOO",
        "OR     O",
        "O   B  O",
        "O   S  O",
        "O  O   O",
        "O B  S O",
        "O      O",
        "OOOOOOOO",
    ],
]

# 7-11: Figure 4.  12-13: Figure 7.
LEVELS += [FIGURE4[name] for name in FIGURE4_ORDER]
LEVELS += [FIGURE7[name] for name in FIGURE7_ORDER]


def level_count():
    return len(LEVELS)
