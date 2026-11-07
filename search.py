"""Search algorithms for Sokoban: BFS and A*, both written with the classic
OPEN and CLOSED lists of the course.

OPEN   = nodes that are generated but not expanded yet (the frontier).
CLOSED = nodes that were already expanded.

    OPEN   <- [root]          CLOSED <- {}
    while OPEN is not empty:
        n <- take the next node out of OPEN      (BFS: oldest / A*: smallest f)
        if n is a goal: return n                 (goal test when n is expanded)
        put n in CLOSED
        for every successor c of n:
            if c is neither in OPEN nor in CLOSED: put c in OPEN
            A* only: if c is already known with a worse g, keep the better one
                     (a CLOSED node with a better g goes back to OPEN)
"""

from collections import deque
from heapq import heappush, heappop
from itertools import count
from boxgame import Node

DEFAULT_NODE_LIMIT = 400000
UNREACHABLE = 1000


# --------------------------------------------------------------------------
# OPEN and CLOSED
# --------------------------------------------------------------------------
class Closed:
    """CLOSED list: the expanded nodes, found again by their state."""

    def __init__(self):
        self.nodes = {}

    def add(self, node):
        self.nodes[node.state.stateKey()] = node

    def get(self, state):
        return self.nodes.get(state.stateKey())

    def remove(self, state):
        del self.nodes[state.stateKey()]

    def contains(self, state):
        return state.stateKey() in self.nodes

    def __contains__(self, state):
        return self.contains(state)

    def __len__(self):
        return len(self.nodes)


class OpenFIFO:
    """OPEN list of BFS: a queue, the oldest node leaves first."""

    def __init__(self):
        self.queue = deque()
        self.keys = set()           # states waiting in the queue

    def push(self, node):
        self.queue.append(node)
        self.keys.add(node.state.stateKey())

    def pop(self):
        node = self.queue.popleft()
        self.keys.discard(node.state.stateKey())
        return node

    def contains(self, state):
        return state.stateKey() in self.keys

    def __contains__(self, state):
        return self.contains(state)

    def __len__(self):
        return len(self.queue)


class OpenPriority:
    """OPEN list of A*: a priority queue, the node with the smallest f leaves
    first.  Only one node per state is alive; when a better path to the same
    state is pushed, the older entry stays in the heap but is ignored."""

    def __init__(self):
        self.heap = []
        self.live = {}              # state key -> the node that counts
        self.tie = count()

    def push(self, node):
        self.live[node.state.stateKey()] = node
        heappush(self.heap, (node.f, next(self.tie), node))

    def pop(self):
        while self.heap:
            _, _, node = heappop(self.heap)
            key = node.state.stateKey()
            if self.live.get(key) is node:      # skip replaced entries
                del self.live[key]
                return node
        return None

    def get(self, state):
        return self.live.get(state.stateKey())

    def contains(self, state):
        return state.stateKey() in self.live

    def __contains__(self, state):
        return self.contains(state)

    def __len__(self):
        return len(self.live)


# --------------------------------------------------------------------------
# Deadlocks
# --------------------------------------------------------------------------
def dead_cells(state):
    walls, targets = state.walls, state.targets
    corners = set()
    for row in range(state.height):
        for col in range(state.width):
            pos = (row, col)
            if pos in walls or pos in targets:
                continue
            vertical = (row - 1, col) in walls or (row + 1, col) in walls
            horizontal = (row, col - 1) in walls or (row, col + 1) in walls
            if vertical and horizontal:
                corners.add(pos)

    dead = set(corners)
    for a in corners:
        for b in corners:
            if a < b:
                dead |= dead_line(a, b, walls, targets)
    return frozenset(dead)


def dead_line(a, b, walls, targets):
    if a[0] == b[0]:
        cells = [(a[0], col) for col in range(a[1], b[1] + 1)]
        sides = [(-1, 0), (1, 0)]
    elif a[1] == b[1]:
        cells = [(row, a[1]) for row in range(a[0], b[0] + 1)]
        sides = [(0, -1), (0, 1)]
    else:
        return set()

    if len(cells) < 3:
        return set()
    if any(p in walls or p in targets for p in cells):
        return set()
    for dr, dc in sides:
        if all((r + dr, c + dc) in walls for r, c in cells):
            return set(cells)
    return set()


def has_deadlock(state, dead=None):
    if dead is None:
        dead = dead_cells(state)
    return any(box in dead and box not in state.targets
               for box in state.boxes)


# --------------------------------------------------------------------------
# BFS
# --------------------------------------------------------------------------
def bfs(initial_state, stats=None, node_limit=DEFAULT_NODE_LIMIT):
    """Breadth-first search with OPEN (FIFO) and CLOSED.

    Returns (goal_node, expanded).  `stats`, if given, receives generated,
    limit_reached, open_size, closed_size and max_open.
    """
    root = Node(initial_state)
    open_list, closed = OpenFIFO(), Closed()
    open_list.push(root)
    generated, expanded, max_open = 1, 0, 1
    limit_reached = False
    goal = None

    while len(open_list) > 0:
        if node_limit is not None and expanded >= node_limit:
            limit_reached = True
            break

        node = open_list.pop()
        expanded += 1

        if node.state.isGoal():                 # goal test on expansion
            goal = node
            break

        closed.add(node)
        for action, child_state in node.state.successorFunction():
            if child_state in open_list or child_state in closed:
                continue
            open_list.push(Node(child_state, node, action, node.g + 1))
            generated += 1
        max_open = max(max_open, len(open_list))

    if stats is not None:
        stats.update(generated=generated, limit_reached=limit_reached,
                     open_size=len(open_list), closed_size=len(closed),
                     max_open=max_open)
    return goal, expanded


def h1(state):
    return len(state.boxes - state.targets)


def h2(state):
    misplaced = len(state.boxes - state.targets)
    distances = 0
    for box in state.boxes:
        distances += min(abs(box[0] - t[0]) + abs(box[1] - t[1])
                         for t in state.targets)
    return 2 * misplaced + distances


push_tables = {}


def push_distances(state):
    """For each target, the pushes needed to bring a box from every cell."""
    key = (state.walls, state.targets)
    if key in push_tables:
        return push_tables[key]

    tables = {}
    for target in state.targets:
        dist = {target: 0}
        queue = deque([target])
        while queue:
            row, col = queue.popleft()
            for dr, dc in state.DIRECTIONS.values():
                box = (row - dr, col - dc)
                player = (row - 2 * dr, col - 2 * dc)
                if box in dist or not state.isInside(player):
                    continue
                if box in state.walls or player in state.walls:
                    continue
                dist[box] = dist[(row, col)] + 1
                queue.append(box)
        tables[target] = dist
    push_tables[key] = tables
    return tables


def cheapest_assignment(costs):
    """Cheapest way to give each box its own target (costs[box][target])."""
    size = len(costs)
    best = {0: 0}
    for box in range(size):
        following = {}
        for used, total in best.items():
            for target in range(size):
                if used >> target & 1:
                    continue
                new_used = used | 1 << target
                new_total = total + costs[box][target]
                if new_total < following.get(new_used, float("inf")):
                    following[new_used] = new_total
        best = following
    return best[(1 << size) - 1]


def h3(state):
    tables = push_distances(state)
    boxes = list(state.boxes)
    targets = list(state.targets)
    costs = [[tables[t].get(b, UNREACHABLE) for t in targets] for b in boxes]
    pushes = cheapest_assignment(costs)

    misplaced = [b for b in boxes if b not in state.targets]
    if not misplaced:
        return pushes
    row, col = state.player
    walk = min(abs(row - b[0]) + abs(col - b[1]) for b in misplaced) - 1
    return pushes + max(walk, 0)


# --------------------------------------------------------------------------
# A*
# --------------------------------------------------------------------------
class SearchResult(tuple):
    """(goal_node, expanded) plus the other counters."""

    def __new__(cls, goal_node, expanded, generated=0, limit_reached=False,
                heuristic_calls=0, deadlock_checks=0, open_size=0,
                closed_size=0, max_open=0):
        result = super().__new__(cls, (goal_node, expanded))
        result.generated = generated
        result.limit_reached = limit_reached
        result.heuristic_calls = heuristic_calls
        result.deadlock_checks = deadlock_checks
        result.open_size = open_size        # nodes left in OPEN at the end
        result.closed_size = closed_size    # nodes in CLOSED at the end
        result.max_open = max_open          # biggest OPEN during the search
        return result

    @property
    def goal(self):
        return self[0]

    @property
    def expanded(self):
        return self[1]

    @property
    def cost(self):
        return self[0].g if self[0] is not None else None


def astar(initial_state, heuristic=h1, node_limit=DEFAULT_NODE_LIMIT,
          use_deadlock=False, dead=None):
    """A* with OPEN (priority queue on f = g + h) and CLOSED.

    A successor already in OPEN or CLOSED is kept only if this path to it is
    cheaper; a CLOSED node that gets a cheaper path is reopened (needed
    because h2 is not admissible).  With use_deadlock=True, a successor with
    a box on a dead cell is never put in OPEN.
    """
    if use_deadlock and dead is None:
        dead = dead_cells(initial_state)

    root = Node(initial_state)
    root.setF(heuristic)
    heuristic_calls = 1
    deadlock_checks = 0
    open_list, closed = OpenPriority(), Closed()

    def result(goal, expanded, generated, limit):
        return SearchResult(goal, expanded, generated, limit, heuristic_calls,
                            deadlock_checks, len(open_list), len(closed),
                            max_open)

    max_open = 1
    if use_deadlock:
        deadlock_checks += 1
        if has_deadlock(root.state, dead):
            return result(None, 0, 1, False)

    open_list.push(root)
    expanded, generated = 0, 1

    while len(open_list) > 0:
        if node_limit is not None and expanded >= node_limit:
            return result(None, expanded, generated, True)

        node = open_list.pop()
        expanded += 1

        if node.state.isGoal():                 # goal test on expansion
            return result(node, expanded, generated, False)

        closed.add(node)
        for action, child_state in node.state.successorFunction():
            child_g = node.g + 1

            old = open_list.get(child_state)
            if old is None:
                old = closed.get(child_state)
            if old is not None and old.g <= child_g:
                continue                        # a path at least as good exists

            if use_deadlock:
                deadlock_checks += 1
                if has_deadlock(child_state, dead):
                    continue

            if closed.contains(child_state):
                closed.remove(child_state)      # reopen with the better g
            child = Node(child_state, node, action, child_g)
            child.setF(heuristic)
            heuristic_calls += 1
            generated += 1
            open_list.push(child)
        max_open = max(max_open, len(open_list))

    return result(None, expanded, generated, False)