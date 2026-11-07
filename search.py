from collections import deque
from heapq import heappush, heappop
from itertools import count
from boxgame import Node

DEFAULT_NODE_LIMIT = 400000
UNREACHABLE = 1000


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


def bfs(initial_state, stats=None, node_limit=DEFAULT_NODE_LIMIT):
    root = Node(initial_state)
    generated = 1
    expanded = 0
    limit_reached = False
    goal = None

    if root.state.isGoal():
        goal = root
    frontier = deque([root])
    explored = {root.state.stateKey()}

    while frontier and goal is None:
        if node_limit is not None and expanded >= node_limit:
            limit_reached = True
            break

        node = frontier.popleft()
        expanded += 1

        for action, child_state in node.state.successorFunction():
            key = child_state.stateKey()
            if key in explored:
                continue
            child = Node(child_state, node, action, node.g + 1)
            generated += 1
            if child_state.isGoal():
                goal = child
                break
            explored.add(key)
            frontier.append(child)

    if stats is not None:
        stats.update(generated=generated, limit_reached=limit_reached)
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


class SearchResult(tuple):
    """(goal_node, expanded) plus the other counters."""

    def __new__(cls, goal_node, expanded, generated=0, limit_reached=False,
                heuristic_calls=0, deadlock_checks=0):
        result = super().__new__(cls, (goal_node, expanded))
        result.generated = generated
        result.limit_reached = limit_reached
        result.heuristic_calls = heuristic_calls
        result.deadlock_checks = deadlock_checks
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
    if use_deadlock and dead is None:
        dead = dead_cells(initial_state)

    root = Node(initial_state)
    root.setF(heuristic)
    heuristic_calls = 1
    deadlock_checks = 0

    if use_deadlock:
        deadlock_checks += 1
        if has_deadlock(root.state, dead):
            return SearchResult(None, 0, 1, False, heuristic_calls,
                                deadlock_checks)

    frontier = [(root.f, 0, root)]
    tie_breaker = count(1)
    best_g = {root.state.stateKey(): 0}
    expanded = 0
    generated = 1

    while frontier:
        if node_limit is not None and expanded >= node_limit:
            return SearchResult(None, expanded, generated, True,
                                heuristic_calls, deadlock_checks)

        _, _, node = heappop(frontier)
        if node.g != best_g.get(node.state.stateKey()):
            continue
        expanded += 1

        if node.state.isGoal():
            return SearchResult(node, expanded, generated, False,
                                heuristic_calls, deadlock_checks)

        for action, child_state in node.state.successorFunction():
            child_g = node.g + 1
            child_key = child_state.stateKey()
            if child_g >= best_g.get(child_key, float("inf")):
                continue

            if use_deadlock:
                deadlock_checks += 1
                if has_deadlock(child_state, dead):
                    continue

            best_g[child_key] = child_g
            child = Node(child_state, node, action, child_g)
            child.setF(heuristic)
            heuristic_calls += 1
            generated += 1
            heappush(frontier, (child.f, next(tie_breaker), child))

    return SearchResult(None, expanded, generated, False,
                        heuristic_calls, deadlock_checks)
