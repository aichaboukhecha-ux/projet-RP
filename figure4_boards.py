"""The five example boards of Figure 4 - Project 1, Part 3.

Transcribed by hand from the images embedded in ``Project 1 Part 3.pdf``
(page 5, Figure 4).  Same ASCII format as ``levels.py``:

    O  wall          R  player          B  box
    .  player on target (* would be box on target)
    S  target        ' ' empty

Every board was checked against the spec before being accepted:
rectangular grid, walls on all sides, exactly one player, and exactly as
many boxes as targets.

AMBIGUITY - read this before trusting the numbers
--------------------------------------------------
The figures are rendered pictures, not text, so the cell grid had to be
recovered by measuring the image (cell pitch, brick boundaries) and then
reading each board cell by cell.  Grid size and object placement were
cross-checked twice - once by colour-classifying every cell of the picture,
once by viewing an overlaid grid - and the two readings agree for all five
boards.

Two details are still judgements rather than certainties, and they are
flagged here instead of being hidden:

  * Figure 4 / Exemple 2: the crate sits in the lower-left.  Its centre falls
    within 1 cell of the c2/c3 border; this transcription puts it at (5,2).
    Reading: c2.  Confidence: medium.

  * Figure 4 / Exemple 3 and 5: the boards are not rectangular - part of the
    bounding box is simply not drawn (white in the figure).  Those cells are
    transcribed as walls ``O``.  That is behaviour-preserving (the player can
    never enter them either way) and it keeps the "walls on all sides"
    invariant the spec asks for.

Everything else is high confidence: the grid sizes were confirmed by overlaying
the candidate grid on the picture and checking the lines fall on brick edges.
"""

FIGURE4 = {
    # 6x6 - target (1,1), crate (1,3), player (2,3) with a wall at (2,2).
    # Verified: 1 box, 1 target, 1 player.
    "exemple1": [
        "OOOOOO",
        "OS B O",
        "O OR O",
        "O    O",
        "O    O",
        "OOOOOO",
    ],

    # 8x8 - wall block (2,2)-(2,4), wall column (4,5)-(6,5),
    # player standing on the single target at (3,5), crate at (5,2).
    # Verified: 1 box, 1 target, 1 player.
    "exemple2": [
        "OOOOOOOO",
        "O      O",
        "O OOO  O",
        "O    . O",
        "O    O O",
        "O B  O O",
        "O    O O",
        "OOOOOOOO",
    ],

    # 8x7 - two crates (2,3) and (3,4), player (2,4), targets (4,6) and (5,6).
    # The bottom-left 4x2 block of the bounding box is not part of the board.
    # Verified: 2 boxes, 2 targets, 1 player.
    "exemple3": [
        "OOOOOOOO",
        "O   O  O",
        "O  BR  O",
        "O   B  O",
        "OOOOO SO",
        "OOOOO SO",
        "OOOOOOOO",
    ],

    # 7x9 - THE example with a box already on a target: the yellow crate at
    # (3,3) is drawn as a box on a target, so it is written '*'.
    # Crates: (3,3) on target, (4,2), (4,4).  Targets: (3,3), (5,2), (5,4).
    # Player (5,3) between two targets.
    # Verified: 3 boxes, 3 targets, 1 player.
    "exemple4": [
        "OOOOOOO",
        "OO  OOO",
        "OO  OOO",
        "OO *  O",
        "OOBOB O",
        "O SRS O",
        "O    OO",
        "OOO  OO",
        "OOOOOOO",
    ],

    # 9x8 - three crates (2,5), (3,2), (5,3); targets (1,3), (3,7), (6,6);
    # player (3,4).
    # Verified: 3 boxes, 3 targets, 1 player.
    "exemple5": [
        "OOOOOOOOO",
        "OOOSO  OO",
        "O    B OO",
        "O B R  SO",
        "OOO O OOO",
        "OOOBO OOO",
        "OOO   SOO",
        "OOOOOOOOO",
    ],
}

# Display order used by the benchmark and the report.
FIGURE4_ORDER = ["exemple1", "exemple2", "exemple3", "exemple4", "exemple5"]


def boards():
    """Yield (name, ascii_board) for the five Figure 4 boards, in order."""
    for name in FIGURE4_ORDER:
        yield name, FIGURE4[name]


if __name__ == "__main__":
    # Self-check: parse every board and report the invariants.
    from boxgame import parse_board

    for name, rows in boards():
        state = parse_board(rows)
        print("%-9s %dx%d  boxes=%d targets=%d player=%s"
              % (name, state.width, state.height,
                 len(state.boxes), len(state.targets), state.player))
        assert len(state.boxes) == len(state.targets), name
        for r in rows:
            assert len(r) == len(rows[0]), (name, r)
        for r in rows:
            assert r[0] == "O" and r[-1] == "O", (name, r)
            assert set(r) <= set("OBRS. *"), (name, r)
        assert rows[0] == "O" * len(rows[0]), name
        assert rows[-1] == "O" * len(rows[0]), name
        print("           OK: " + " / ".join(rows))
    print("all 5 Figure 4 boards validate")
