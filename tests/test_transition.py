import pytest

from sokoban.env import GymSokobanEnv
from sokoban.levels import load_bundled_levels
from sokoban.solver import SokobanAction
from sokoban.transition import apply_action, legal_actions

LEVEL = "#####\n#@$.#\n#####"


def test_moves_pushes_and_rejects_blocked_actions() -> None:
    env = GymSokobanEnv(LEVEL)
    state = env.reset()
    env.close()

    pushed = apply_action(state, SokobanAction.RIGHT)

    assert pushed is not None
    assert pushed.player == (1, 2)
    assert pushed.boxes == frozenset({(1, 3)})
    assert apply_action(state, SokobanAction.LEFT) is None
    assert legal_actions(state) == (SokobanAction.RIGHT,)
    assert state.player == (1, 1)
    assert state.boxes == frozenset({(1, 2)})


def test_rejects_invalid_actions() -> None:
    env = GymSokobanEnv(LEVEL)
    state = env.reset()
    env.close()

    with pytest.raises(ValueError, match="invalid Sokoban action"):
        apply_action(state, 4)
    with pytest.raises(ValueError, match="invalid Sokoban action"):
        apply_action(state, 1.0)  # type: ignore[arg-type]


def test_matches_gym_sokoban_on_all_bundled_levels() -> None:
    for level in load_bundled_levels():
        env = GymSokobanEnv(level.board)
        initial = env.reset()

        for action in SokobanAction:
            env.reset()
            actual = env.step(action).state
            expected = apply_action(initial, action)
            assert actual == (expected if expected is not None else initial), (
                level.name,
                action,
            )

        env.close()
