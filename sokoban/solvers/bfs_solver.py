"""State-space Sokoban solver."""

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

from sokoban.search import Heuristic, MoveHeuristic, SearchResult, search
from sokoban.solver import BoardState, SokobanAction
from sokoban.transition import apply_action


class BFSSolver:
    """Plan a minimum-push solution, then replay its player actions."""

    def __init__(
        self,
        *,
        heuristic: Heuristic | None = None,
        jev: bool = False,
        client: TypeSafeClient | None = None,
        max_expansions: int | None = None,
    ) -> None:
        if jev and client is None:
            load_dotenv()
            client = TypeSafeClient()
        self._heuristic = heuristic
        self._jev_heuristic: MoveHeuristic | None = (
            self._score_move if client is not None else None
        )
        self._client = client
        self._max_expansions = max_expansions
        self._plan: tuple[int, ...] = ()
        self._next_action = 0
        self._expected_state: BoardState | None = None
        self.result: SearchResult | None = None
        self.api_calls = 0

    def reset(self, state: BoardState) -> None:
        """Search for a complete plan from ``state``."""

        self.api_calls = 0
        self.result = search(
            state,
            heuristic=self._heuristic,
            heuristic_weight=float(self._heuristic is not None),
            move_heuristic=self._jev_heuristic,
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

    def _score_move(
        self, state: BoardState, history: tuple[int, ...], action: int
    ) -> float:
        """Return Jev's bad-move probability for one search edge."""

        assert self._client is not None
        move = SokobanAction(action).name[0]
        self.api_calls += 1
        response = self._client.system_one(
            state={
                "board": {
                    "height": state.height,
                    "width": state.width,
                    "walls": sorted(state.walls),
                    "goals": sorted(state.goals),
                    "boxes": sorted(state.boxes),
                    "player": state.player,
                },
                "history": [SokobanAction(item).name[0] for item in history],
            },
            questions={
                "move": Noul(instructions=f"is this a good move: {move}"),
            },
        )
        return 1.0 - response.nouls["move"].noul
