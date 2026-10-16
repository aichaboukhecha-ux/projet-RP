from collections import deque
from boxgame import Node


def bfs(initial_state):
    """Breadth-first graph search. Returns (goal_node, nodes_expanded) or (None, n)."""
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