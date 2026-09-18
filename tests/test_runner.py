from collections.abc import Iterable

from sokoban.env import GymSokobanEnv, SokobanAction
from sokoban.runner import run_episode
from sokoban.solver import BoardState

LEVEL = """
#####
#@$.#
#####
"""


class ScriptedSolver:
    def __init__(self, actions: Iterable[int]) -> None:
        self._actions = tuple(actions)
        self._index = 0

    def reset(self, state: BoardState) -> None:
        self._index = 0

    def act(self, state: BoardState) -> int:
        action = self._actions[self._index % len(self._actions)]
        self._index += 1
        return action


def test_runner_solves_and_records_trajectory() -> None:
    env = GymSokobanEnv(LEVEL)
    result = run_episode(env, ScriptedSolver([SokobanAction.RIGHT]))
    env.close()

    assert result.solved
    assert result.num_steps == 1
    assert result.terminated
    assert not result.truncated
    assert result.trajectory[0].action == SokobanAction.RIGHT
    assert result.trajectory[0].state.boxes == frozenset({(1, 3)})


def test_runner_enforces_its_own_step_limit() -> None:
    env = GymSokobanEnv(LEVEL, max_steps=10)
    result = run_episode(
        env,
        ScriptedSolver([SokobanAction.UP]),
        max_steps=2,
    )
    env.close()

    assert not result.solved
    assert result.num_steps == 2
    assert result.truncated
    assert result.max_steps_reached


def test_runner_renders_initial_and_resulting_frames() -> None:
    env = GymSokobanEnv(LEVEL)
    frames = []
    result = run_episode(
        env,
        ScriptedSolver([SokobanAction.RIGHT]),
        render=frames.append,
    )
    env.close()

    assert result.num_steps == 1
    assert len(frames) == 2
    assert frames[0].shape == frames[1].shape == (48, 80, 3)
