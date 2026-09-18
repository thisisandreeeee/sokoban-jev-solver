from unittest.mock import patch

from sokoban.env import GymSokobanEnv
from sokoban.solver import BoardState, SokobanAction, SokobanSolver
from sokoban.solvers import BFSSolver, RandomSolver

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


def test_bfs_adds_jev_move_score_to_geometry_heuristic() -> None:
    class FakeClient:
        calls: list[dict[str, object]] = []

        def system_one(self, **kwargs: object) -> object:
            self.calls.append(kwargs)
            answer = type("NoulAnswer", (), {"noul": 1.0})()
            return type("Response", (), {"nouls": {"move": answer}})()

    client = FakeClient()
    geometry_calls: list[BoardState] = []
    state = BoardState(
        height=3,
        width=6,
        walls=frozenset(),
        goals=frozenset({(1, 4)}),
        boxes=frozenset({(1, 3)}),
        player=(1, 1),
    )

    def geometry(state: BoardState) -> float:
        geometry_calls.append(state)
        return 0.0

    solver = BFSSolver(heuristic=geometry, client=client)  # type: ignore[arg-type]
    solver.reset(state)

    assert solver.act(state) == SokobanAction.RIGHT
    assert geometry_calls
    assert solver.api_calls == len(client.calls)
    assert client.calls[0]["state"] == {
        "board": {
            "height": 3,
            "width": 6,
            "walls": [],
            "goals": [(1, 4)],
            "boxes": [(1, 3)],
            "player": (1, 2),
        },
        "history": ["R"],
    }
    question = client.calls[0]["questions"]["move"]  # type: ignore[index]
    assert question.instructions == "is this a good move: R"

def test_bfs_jev_loads_dotenv_before_creating_client() -> None:
    with (
        patch("sokoban.solvers.bfs_solver.load_dotenv") as load_dotenv,
        patch("sokoban.solvers.bfs_solver.TypeSafeClient") as client,
    ):
        BFSSolver(jev=True)

    load_dotenv.assert_called_once_with()
    client.assert_called_once_with()
