Level = [
    "OOOOO",
    "ORBSO",
    "O   O",
    "OOOOO",
]


class SokobanPuzzle:
  

    DIRECTIONS = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1),
    }

    def __init__(self, targets, walls, boxes, player, height, width):
        self.targets = frozenset(targets)
        self.walls = frozenset(walls)
        self.boxes = frozenset(boxes)
        self.player = player
        self.height = height
        self.width = width

    def isInside(self, position):
        row, col = position
        return 0 <= row < self.height and 0 <= col < self.width

    def isGoal(self):
        return self.targets <= self.boxes   # every target holds a box

    def stateKey(self):
        # player position + box positions fully identify a state
        return (self.player, tuple(sorted(self.boxes)))

    def __eq__(self, other):
        return self.stateKey() == other.stateKey()

    def __hash__(self):
        return hash(self.stateKey())

    def successorFunction(self):
        successors = []
        for action, (dr, dc) in self.DIRECTIONS.items():
            nxt = (self.player[0] + dr, self.player[1] + dc)

            if not self.isInside(nxt) or nxt in self.walls:
                continue

            new_boxes = set(self.boxes)
            if nxt in self.boxes:                      # push
                dest = (nxt[0] + dr, nxt[1] + dc)
                if (not self.isInside(dest) or dest in self.walls
                        or dest in self.boxes):
                    continue
                new_boxes.remove(nxt)
                new_boxes.add(dest)

            successors.append((action, SokobanPuzzle(
                self.targets, self.walls, new_boxes, nxt,
                self.height, self.width)))
        return successors

    def __str__(self):
        rows = []
        for r in range(self.height):
            line = ""
            for c in range(self.width):
                p = (r, c)
                if p in self.walls:
                    ch = "O"
                elif p == self.player:
                    ch = "." if p in self.targets else "R"
                elif p in self.boxes:
                    ch = "*" if p in self.targets else "B"
                elif p in self.targets:
                    ch = "S"
                else:
                    ch = " "
                line += ch
            rows.append(line)
        return "\n".join(rows)


def parse_board(board):
    walls, targets, boxes, player = set(), set(), set(), None
    height, width = len(board), len(board[0])

    for row in board:
        if len(row) != width:
            raise ValueError("All rows must have the same length.")

    for r in range(height):
        for c in range(width):
            s, pos = board[r][c], (r, c)
            if s == "O":
                walls.add(pos)
            elif s == "S":
                targets.add(pos)
            elif s in ("R", "."):
                if player is not None:
                    raise ValueError("There must be only one player.")
                player = pos
                if s == ".":
                    targets.add(pos)
            elif s in ("B", "*"):
                boxes.add(pos)
                if s == "*":
                    targets.add(pos)
            elif s != " ":
                raise ValueError(f"Unknown symbol: {s!r}")

    if player is None:
        raise ValueError("The board must contain a player.")
    if len(boxes) != len(targets):
        raise ValueError("The number of boxes and targets must be equal.")

    return SokobanPuzzle(targets, walls, boxes, player, height, width)


class Node:
    def __init__(self, state, parent=None, action=None, g=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.g = g

    def getPath(self):
        path, cur = [], self
        while cur is not None:
            path.append(cur.state)
            cur = cur.parent
        return path[::-1]

    def getSolution(self):
        actions, cur = [], self
        while cur.parent is not None:
            actions.append(cur.action)
            cur = cur.parent
        return actions[::-1]