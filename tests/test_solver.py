from sokoban.solver import BoardState, SokobanAction, SokobanSolver
from sokoban.solvers import RandomSolver

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
