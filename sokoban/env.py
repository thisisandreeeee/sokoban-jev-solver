"""Stable adapter around the legacy :mod:`gym_sokoban` environment."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from textwrap import dedent

import numpy as np
from numpy.typing import NDArray

from gym_sokoban.envs.sokoban_env import SokobanEnv
from sokoban.solver import BoardState, Position, SokobanAction, StepResult


@dataclass(frozen=True)
class _ParsedLevel:
    room_fixed: NDArray[np.int8]
    room_state: NDArray[np.int8]
    player: Position
    num_boxes: int


class GymSokobanEnv:
    """Expose ``gym-sokoban`` through a small, stable interface."""

    num_actions = len(SokobanAction)

    def __init__(
        self,
        level: str | None = None,
        *,
        room_size: tuple[int, int] = (7, 7),
        num_boxes: int = 2,
        max_steps: int = 120,
    ) -> None:
        if max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if level is None and (min(room_size) <= 2 or num_boxes <= 0):
            raise ValueError("procedural rooms need valid dimensions and boxes")

        self._level = _parse_xsb(level) if level is not None else None
        if self._level is not None:
            room_size = self._level.room_fixed.shape
            num_boxes = self._level.num_boxes

        self._env = SokobanEnv(
            dim_room=room_size,
            num_boxes=num_boxes,
            max_steps=max_steps,
            reset=False,
        )

    def reset(self) -> BoardState:
        """Reset the configured level and return an immutable snapshot."""

        if self._level is None:
            self._env.reset(render_mode="raw")
        else:
            self._env.room_fixed = self._level.room_fixed.copy()
            self._env.room_state = self._level.room_state.copy()
            self._env.player_position = np.array(self._level.player)
            self._env.box_mapping = {}
            self._env.num_env_steps = 0
            self._env.reward_last = 0
            self._env.boxes_on_target = int(
                np.count_nonzero(self._env.room_state == 3)
            )

        return self._snapshot()

    def step(self, action: int) -> StepResult:
        """Apply one canonical direction and normalize the legacy Gym result."""

        if (
            isinstance(action, bool)
            or not isinstance(action, int)
            or action not in range(self.num_actions)
        ):
            raise ValueError(f"invalid Sokoban action: {action!r}")

        _, reward, done, engine_info = self._env.step(
            int(action) + 1,
            observation_mode="raw",
        )
        state = self._snapshot()
        solved = state.boxes == state.goals
        return StepResult(
            state=state,
            reward=float(reward),
            solved=solved,
            terminated=solved,
            truncated=bool(done and not solved),
            info={
                "moved_player": bool(engine_info["action.moved_player"]),
                "moved_box": bool(engine_info["action.moved_box"]),
            },
        )

    def render_rgb(self) -> NDArray[np.uint8]:
        """Return a detached RGB frame produced by ``gym-sokoban``."""

        return np.asarray(self._env.render(mode="rgb_array"), dtype=np.uint8).copy()

    def close(self) -> None:
        self._env.close()

    def _snapshot(self) -> BoardState:
        room_fixed = self._env.room_fixed
        room_state = self._env.room_state
        players = _positions(room_state == 5)
        if len(players) != 1:
            raise RuntimeError("environment state must contain exactly one player")

        return BoardState(
            height=int(room_state.shape[0]),
            width=int(room_state.shape[1]),
            walls=_positions(room_fixed == 0),
            goals=_positions(room_fixed == 2),
            boxes=_positions((room_state == 3) | (room_state == 4)),
            player=next(iter(players)),
        )


def _positions(mask: NDArray[np.bool_]) -> frozenset[Position]:
    return frozenset((int(row), int(column)) for row, column in np.argwhere(mask))


def _parse_xsb(level: str) -> _ParsedLevel:
    lines = dedent(level).strip("\n").splitlines()
    if not lines or not any(line.strip() for line in lines):
        raise ValueError("level must not be empty")

    allowed = {"#", " ", ".", "$", "@", "*", "+"}
    invalid = {character for line in lines for character in line} - allowed
    if invalid:
        raise ValueError(f"level contains invalid characters: {sorted(invalid)!r}")

    width = max(map(len, lines))
    grid = [list(line.ljust(width)) for line in lines]
    outside = _outside_spaces(grid)
    room_fixed = np.zeros((len(lines), width), dtype=np.int8)
    room_state = np.zeros_like(room_fixed)
    players: list[Position] = []
    num_boxes = 0
    num_goals = 0

    for row, line in enumerate(grid):
        for column, character in enumerate(line):
            if character == "#" or (row, column) in outside:
                continue

            room_fixed[row, column] = 2 if character in ".*+" else 1
            room_state[row, column] = {
                " ": 1,
                ".": 2,
                "$": 4,
                "@": 5,
                "*": 3,
                "+": 5,
            }[character]

            if character in "$*":
                num_boxes += 1
            if character in ".*+":
                num_goals += 1
            if character in "@+":
                players.append((row, column))

    if len(players) != 1:
        raise ValueError("level must contain exactly one player")
    if num_boxes == 0 or num_boxes != num_goals:
        raise ValueError("level must contain equal non-zero numbers of boxes and goals")

    return _ParsedLevel(room_fixed, room_state, players[0], num_boxes)


def _outside_spaces(grid: list[list[str]]) -> set[Position]:
    """Find padding outside an enclosed XSB board."""

    height, width = len(grid), len(grid[0])
    pending: deque[Position] = deque()
    outside: set[Position] = set()

    for row in range(height):
        pending.extend(((row, 0), (row, width - 1)))
    for column in range(width):
        pending.extend(((0, column), (height - 1, column)))

    while pending:
        row, column = pending.popleft()
        position = (row, column)
        if position in outside or grid[row][column] != " ":
            continue
        outside.add(position)
        for next_row, next_column in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            if 0 <= next_row < height and 0 <= next_column < width:
                pending.append((next_row, next_column))

    return outside
