"""State-space Sokoban solver."""

from sokoban.search import Heuristic, SearchResult, search
from sokoban.solver import BoardState
from sokoban.transition import apply_action


class BFSSolver:
    """Plan a minimum-push solution, then replay its player actions."""

    def __init__(
        self,
        *,
        heuristic: Heuristic | None = None,
        max_expansions: int | None = None,
    ) -> None:
        self._heuristic = heuristic
        self._max_expansions = max_expansions
        self._plan: tuple[int, ...] = ()
        self._next_action = 0
        self._expected_state: BoardState | None = None
        self.result: SearchResult | None = None

    def reset(self, state: BoardState) -> None:
        """Search for a complete plan from ``state``."""

        self.result = search(
            state,
            heuristic=self._heuristic,
            heuristic_weight=float(self._heuristic is not None),
            max_expansions=self._max_expansions,
        )
        if self.result.actions is None:
            raise RuntimeError("BFS found no solution")
        self._plan = self.result.actions
        self._next_action = 0
        self._expected_state = state

    def act(self, state: BoardState) -> int:
        """Return the next action in the precomputed plan."""

        if self._expected_state is None:
            raise RuntimeError("solver must be reset before act")
        if state != self._expected_state:
            raise RuntimeError("environment state diverged from BFS plan")
        if self._next_action >= len(self._plan):
            raise RuntimeError("BFS plan is exhausted")

        action = self._plan[self._next_action]
        self._next_action += 1
        successor = apply_action(state, action)
        assert successor is not None
        self._expected_state = successor
        return action
