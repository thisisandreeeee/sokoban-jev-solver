from unittest.mock import patch

from sokoban.env import GymSokobanEnv
from sokoban.solver import BoardState, SokobanAction, SokobanSolver
from sokoban.solvers import BFSSolver, JevSolver, RandomSolver

STATE = BoardState(
    height=3,
    width=5,
    walls=frozenset(),
    goals=frozenset({(1, 3)}),
    boxes=frozenset({(1, 2)}),
    player=(1, 1),
)


def test_random_solver_implements_protocol_and_returns_valid_actions() -> None:
    solver = RandomSolver(seed=42)
    solver.reset(STATE)

    assert isinstance(solver, SokobanSolver)
    assert all(solver.act(STATE) in SokobanAction for _ in range(20))


def test_random_solver_reset_restarts_seeded_sequence() -> None:
    solver = RandomSolver(seed=7)
    solver.reset(STATE)
    first = [solver.act(STATE) for _ in range(10)]

    solver.reset(STATE)
    second = [solver.act(STATE) for _ in range(10)]

    assert first == second


def test_bfs_solver_plans_and_executes_solution() -> None:
    env = GymSokobanEnv("#####\n#@$.#\n#####")
    state = env.reset()
    solver = BFSSolver()

    solver.reset(state)
    result = env.step(solver.act(state))
    env.close()

    assert isinstance(solver, SokobanSolver)
    assert result.solved
    assert solver.result is not None
    assert solver.result.actions == (SokobanAction.RIGHT,)


def test_jev_solver_passes_board_and_move_history_and_uses_top_choice() -> None:
    class FakeClient:
        calls: list[dict[str, object]] = []

        def system_one(self, **kwargs: object) -> object:
            self.calls.append(kwargs)
            choice = type("ChoiceAnswer", (), {"choice": "right"})()
            return type("Response", (), {"choices": {"move": choice}})()

    client = FakeClient()
    solver = JevSolver(client)  # type: ignore[arg-type]
    solver.reset(STATE)

    assert solver.act(STATE) == SokobanAction.RIGHT
    assert client.calls[0]["state"] == {
        "board": {
            "height": 3,
            "width": 5,
            "walls": [],
            "goals": [(1, 3)],
            "boxes": [(1, 2)],
            "player": (1, 1),
        },
        "past_moves": [],
    }

    solver.act(STATE)
    assert client.calls[1]["state"]["past_moves"] == ["right"]  # type: ignore[index]

    solver.reset(STATE)
    solver.act(STATE)
    assert client.calls[2]["state"]["past_moves"] == []  # type: ignore[index]


def test_jev_solver_loads_dotenv_before_creating_client() -> None:
    with (
        patch("sokoban.solvers.jev_solver.load_dotenv") as load_dotenv,
        patch("sokoban.solvers.jev_solver.TypeSafeClient") as client,
    ):
        JevSolver()

    load_dotenv.assert_called_once_with()
    client.assert_called_once_with()
