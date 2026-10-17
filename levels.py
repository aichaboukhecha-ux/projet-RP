"""Level definitions for "Sokoban Fairy Puzzle" (Part C).

Every level is a ``list[str]`` in the exact ASCII format understood by
``boxgame.parse_board``:

    O   wall            R   player            B   box
    S   target/floor    .   player on target  *   box on target
    ' ' floor

The levels carry no display names: the header only ever shows the level
number.  They are stored here in ascending difficulty (facile -> difficile),
ordered by the BFS figures below, so level 1 is the gentlest warm-up and
level 6 the hardest:

    level   solution cost   nodes expanded   boxes   size
      1          7               30            1      7x6
      2          8               42            1      8x8
      3          8              212            2      8x8
      4         10              630            2      8x8
      5         12             2010            2      8x7
      6         13             1139            2      8x8

Level 4 is the team's original board, imported straight from boxgame so the
board itself is preserved unchanged.  boxgame.py and search.py are never
modified.
"""

from boxgame import Level as ORIGINAL_LEVEL


LEVELS = [
    # 1 ------------------------------------------------ easiest: 1 box, 7 pushes
    [
        "OOOOOOO",
        "OR    O",
        "O     O",
        "O  B  O",
        "O   S O",
        "OOOOOOO",
    ],

    # 2 ------------------------------------------------ 1 box, walled column
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

    # 3 ------------------------------------------------ 2 boxes, 8 pushes
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

    # 4 ------------------------------------------------ the team's original board
    ORIGINAL_LEVEL,

    # 5 ------------------------------------------------ two clean lanes, 12 pushes
    [
        "OOOOOOOO",
        "OR     O",
        "O B  S O",
        "O      O",
        "O B  S O",
        "O      O",
        "OOOOOOOO",
    ],

    # 6 ------------------------------------------------ hardest: 13 pushes, 1139 nodes
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


def level_count():
    return len(LEVELS)
