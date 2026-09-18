from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from sokoban.env import BoardState, GymSokobanEnv, SokobanAction

LEVEL = """
#####
#@$.#
#####
"""


def test_reset_returns_immutable_engine_neutral_state() -> None:
    env = GymSokobanEnv(LEVEL)
    state = env.reset()
    env.close()

    assert state == BoardState(
        height=3,
        width=5,
        walls=frozenset(
            {
                (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
                (1, 0), (1, 4),
                (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
            }
        ),
        goals=frozenset({(1, 3)}),
        boxes=frozenset({(1, 2)}),
        player=(1, 1),
    )
    with pytest.raises(FrozenInstanceError):
        state.player = (0, 0)  # type: ignore[misc]


def test_step_maps_direction_and_preserves_old_snapshot() -> None:
    env = GymSokobanEnv(LEVEL)
    initial = env.reset()
    result = env.step(SokobanAction.RIGHT)
    env.close()

    assert initial.player == (1, 1)
    assert initial.boxes == frozenset({(1, 2)})
    assert result.state.player == (1, 2)
    assert result.state.boxes == result.state.goals == frozenset({(1, 3)})
    assert result.info == {"moved_player": True, "moved_box": True}
    assert result.solved
    assert result.terminated
    assert not result.truncated


def test_environment_step_limit_is_truncation() -> None:
    env = GymSokobanEnv(LEVEL, max_steps=1)
    env.reset()
    result = env.step(SokobanAction.UP)
    env.close()

    assert not result.solved
    assert not result.terminated
    assert result.truncated


def test_render_rgb_uses_engine_renderer() -> None:
    env = GymSokobanEnv(LEVEL)
    env.reset()
    frame = env.render_rgb()
    env.close()

    assert frame.shape == (48, 80, 3)
    assert frame.dtype == np.uint8


def test_rejects_invalid_action_and_level() -> None:
    env = GymSokobanEnv(LEVEL)
    env.reset()
    with pytest.raises(ValueError, match="invalid Sokoban action"):
        env.step(4)
    with pytest.raises(ValueError, match="invalid Sokoban action"):
        env.step(1.0)  # type: ignore[arg-type]
    env.close()

    with pytest.raises(ValueError, match="exactly one player"):
        GymSokobanEnv("#####\n# $.#\n#####")


def test_xsb_supports_ragged_boards_and_occupied_goals() -> None:
    env = GymSokobanEnv("  ####\n###  #\n#+*$ #\n######")
    state = env.reset()
    env.close()

    assert state.walls.issuperset({(0, 0), (0, 1)})
    assert state.player == (2, 1)
    assert state.goals == frozenset({(2, 1), (2, 2)})
    assert state.boxes == frozenset({(2, 2), (2, 3)})
