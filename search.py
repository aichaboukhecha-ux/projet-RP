import time
from collections import deque
from heapq import heappush, heappop
from itertools import count, permutations
from boxgame import Node


# =========================
# 1. BREADTH-FIRST SEARCH
# =========================
def bfs(initial_state, stats=None):
    """Returns (goal_node, nodes_expanded) or (None, n).

    Optional ``stats`` dict, when given, is filled with the measurements the
    assignment asks for: ``generated``, ``seconds`` and ``timed_out``.
    Leaving it out keeps every existing call site working unchanged.
    """
    started = time.perf_counter()

    root = Node(initial_state)
    generated = 1                     # the root counts as generated

    def done(goal, expanded):
        if stats is not None:
            stats.update(generated=generated,
                         seconds=time.perf_counter() - started,
                         timed_out=False)
        return goal, expanded

    if root.state.isGoal():
        return done(root, 0)

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
            generated += 1

            if child_state.isGoal():
                return done(child, expanded)

            explored.add(key)
            frontier.append(child)

    return done(None, expanded)


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
# 5. HEURISTIC h3  
# =========================
def _match_cost(boxes, targets):
    """Minimum-cost one-to-one assignment of boxes onto DISTINCT targets.

    Exact optimum over every permutation.  The boards used here have at most
    4 boxes, so that is 4! = 24 comparisons; we allow up to 6 boxes (720).
    Beyond that we relax to "each box to its closest target", which lets two
    boxes claim the same target - a weaker but still cheap estimate.
    """
    boxes = list(boxes)
    targets = list(targets)

    if len(boxes) == len(targets) and 0 < len(boxes) <= 6:
        best = None
        for perm in permutations(targets):
            cost = 0
            for i, box in enumerate(boxes):
                tgt = perm[i]
                cost += abs(box[0] - tgt[0]) + abs(box[1] - tgt[1])
            if best is None or cost < best:
                best = cost
        return best

    return sum(min(abs(box[0] - tgt[0]) + abs(box[1] - tgt[1])
                   for tgt in targets)
               for box in boxes)


def h3(state):
    """h3 = (min-cost one-to-one box->target matching, Manhattan)
            + max(0, player -> nearest misplaced box, Manhattan - 1)

    Why it is better than h2
    ------------------------
    h2's distance sum is a *relaxation*: every box is charged its distance to
    its own nearest target, so two boxes may both claim the SAME target. The
    second box's real (longer) trip to some other target is never paid for,
    so that term is optimistic and therefore weak. h3 instead charges a
    bijection - every target used exactly once - which is a lower bound that
    is always >= h2's distance term (it minimises over a subset of
    assignments) yet still <= the pushes any solution must contain, so it is
    tighter without ever overshooting. h3 also adds the player's walk to the
    first box it can push, information h2 ignores completely; without it A*
    expands nodes whose true cost already includes that walk.

    Admissibility (honest statement)
    --------------------------------
    The matching term is admissible: a solution realises some bijection
    boxes->targets, each push moves one box one cell, so the pushes per box
    are at least its Manhattan distance to the target it ends on, and the
    minimum over bijections is below that. The walk term is admissible
    because reaching a push needs at least Manhattan(player, box) - 1 moves
    to stand beside the box.

    Summing them is admissible PROVIDED the solution's first push acts on a
    box that is not yet on a target - always true when no box starts on a
    target. If a solution must first shove an already-solved box aside, the
    walk term can overestimate, so h3 is NOT guaranteed admissible there.
    h1 always is. h2 is NOT (the x2 term overcharges: a box one push from
    its target is charged 2 + 1 = 3 while it costs 1) - tests.py proves this
    on a real board rather than asserting it.
    """
    boxes = list(state.boxes)
    targets = list(state.targets)
    if not boxes or not targets:
        return 0

    pushes = _match_cost(boxes, targets)

    misplaced = [b for b in boxes if b not in state.targets]
    if misplaced:
        pr, pc = state.player
        walk = min(abs(pr - b[0]) + abs(pc - b[1]) for b in misplaced)
        walk = max(0, walk - 1)
    else:
        walk = 0

    return pushes + walk


# =========================
# 4. A* SEARCH
# =========================
DEFAULT_NODE_LIMIT = 400000     # expansions before giving up
DEFAULT_TIMEOUT = 15.0          # seconds before giving up


class SearchResult(tuple):
    """What astar() returns: an honest (goal_node, expanded_count) pair.

    It unpacks exactly like bfs(), so existing call styles keep working:

        goal, expanded = astar(state, h2)

    and it carries the extra measurements the assignment asks for as
    attributes:  .generated   .seconds   .timed_out
    """

    def __new__(cls, goal_node, expanded, generated=0, seconds=0.0,
                timed_out=False):
        obj = super().__new__(cls, (goal_node, expanded))
        obj.generated = generated
        obj.seconds = seconds
        obj.timed_out = timed_out
        return obj

    @property
    def goal(self):
        return self[0]

    @property
    def cost(self):
        """Cost of the solution, or None when there is no solution."""
        return self[0].g if self[0] is not None else None


def astar(initial_state, heuristic=h1, node_limit=DEFAULT_NODE_LIMIT,
          timeout=DEFAULT_TIMEOUT):
    """A* search with a pluggable heuristic.

    Returns a SearchResult, unpackable as (goal_node, expanded_count) exactly
    like bfs(), plus .generated, .seconds and .timed_out.

    Stopping is always reported honestly:
      * goal found          -> goal_node set,  timed_out = False
      * node_limit reached  -> goal_node None, timed_out = True
      * timeout reached     -> goal_node None, timed_out = True
      * frontier exhausted  -> goal_node None, timed_out = False (no solution)
    """
    started = time.perf_counter()

    root = Node(initial_state)
    root.setF(heuristic)                    # f = g + h, g is 0 for the root

    frontier = []                           # (f, tie_breaker, node)
    tie_breaker = count()
    heappush(frontier, (root.f, next(tie_breaker), root))

    root_key = root.state.stateKey()
    best_g = {root_key: 0}                  # cheapest g seen per state

    expanded = 0
    generated = 1                           # the root counts as generated

    while frontier:
        # --- limits -------------------------------------------------------
        # node limit: a cheap integer compare, so it is checked on EVERY
        # expansion and small limits are honoured exactly.
        if node_limit is not None and expanded >= node_limit:
            return SearchResult(None, expanded, generated,
                                time.perf_counter() - started, True)
        # wall clock: perf_counter() is costlier, so poll it every 64
        # expansions - still far more often than a run can stall.
        if (timeout is not None and expanded % 64 == 0
                and time.perf_counter() - started > timeout):
            return SearchResult(None, expanded, generated,
                                time.perf_counter() - started, True)

        _, _, node = heappop(frontier)

        key = node.state.stateKey()
        if node.g != best_g.get(key):       # stale, more expensive entry
            continue

        expanded += 1

        if node.state.isGoal():
            return SearchResult(node, expanded, generated,
                                time.perf_counter() - started, False)

        for action, child_state in node.state.successorFunction():
            child_g = node.g + 1
            child_key = child_state.stateKey()

            if child_g < best_g.get(child_key, float("inf")):
                best_g[child_key] = child_g

                child = Node(child_state, node, action, child_g)
                child.setF(heuristic)       # f = g + h through Node.setF
                generated += 1

                heappush(frontier, (child.f, next(tie_breaker), child))

    return SearchResult(None, expanded, generated,
                        time.perf_counter() - started, False)
