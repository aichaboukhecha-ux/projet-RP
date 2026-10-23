
from collections import deque
from heapq import heappush, heappop
from itertools import count
from boxgame import Node


# =========================
# 1. BREADTH-FIRST SEARCH
# =========================
def bfs(initial_state):
    """Returns (goal_node, nodes_expanded) or (None, n)."""

    root = Node(initial_state)

    if root.state.isGoal():
        return root, 0

    frontier = deque([root])
    explored = {root.state.stateKey()}
    expanded = 0

    while frontier:
        node = frontier.popleft()
        expanded += 1

        for action, child_state in node.state.successorFunction():
            key = child_state.stateKey()

            if key in explored:
                continue

            child = Node(child_state, node, action, node.g + 1)

            if child_state.isGoal():
                return child, expanded

            explored.add(key)
            frontier.append(child)

    return None, expanded


# =========================
# 2. HEURISTIC h1
# =========================
def h1(state):
    """Number of boxes not on target positions."""
    return len(state.boxes - state.targets)


# =========================
# 3. HEURISTIC h2
# =========================
def h2(state):
    """Heuristic formula given in the assignment."""

    boxes_left = len(state.boxes - state.targets)
    distance_sum = 0

    for box in state.boxes:
        if state.targets:
            nearest_distance = min(
                abs(box[0] - target[0]) +
                abs(box[1] - target[1])
                for target in state.targets
            )

            distance_sum += nearest_distance

    return 2 * boxes_left + distance_sum


# =========================
# 4. A* SEARCH
# =========================
def astar(initial_state, heuristic=h1):
    """Returns (goal_node, nodes_expanded) or (None, n)."""

    root = Node(initial_state)

    # Priority queue: (f, tie_breaker, node)
    frontier = []
    tie_breaker = count()

    # Lowest known path cost for each state
    root_key = root.state.stateKey()
    best_g = {root_key: 0}

    # f(n) = g(n) + h(n)
    root_f = root.g + heuristic(root.state)

    heappush(
        frontier,
        (root_f, next(tie_breaker), root)
    )

    expanded = 0

    while frontier:
        f_value, _, node = heappop(frontier)

        key = node.state.stateKey()

        # Ignore an outdated, more expensive path
        if node.g != best_g.get(key):
            continue

        expanded += 1

        # Check whether we reached the goal
        if node.state.isGoal():
            return node, expanded

        # Generate all legal moves
        for action, child_state in node.state.successorFunction():

            child_g = node.g + 1
            child_key = child_state.stateKey()

            # Only keep a better path to this state
            if child_g < best_g.get(child_key, float("inf")):

                best_g[child_key] = child_g

                child = Node(
                    child_state,
                    node,
                    action,
                    child_g
                )

                child_f = child_g + heuristic(child_state)

                heappush(
                    frontier,
                    (child_f, next(tie_breaker), child)
                )

    return None, expanded
