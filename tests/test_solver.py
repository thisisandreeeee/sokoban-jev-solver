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
