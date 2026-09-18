"""Engine-neutral solver contract and Sokoban domain types."""

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Protocol, runtime_checkable

Position = tuple[int, int]


class SokobanAction(IntEnum):
    """Canonical actions understood by every solver and environment adapter."""

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


@dataclass(frozen=True)
class BoardState:
    """Immutable, hashable Sokoban board snapshot."""

    height: int
    width: int
    walls: frozenset[Position]
    goals: frozenset[Position]
    boxes: frozenset[Position]
    player: Position


@dataclass(frozen=True)
class StepResult:
    """Engine-neutral result of one environment action."""

    state: BoardState
    reward: float
    solved: bool
    terminated: bool
    truncated: bool
    info: dict[str, Any]


@runtime_checkable
class SokobanSolver(Protocol):
    """Contract implemented by all Sokoban solvers."""

    def reset(self, state: BoardState) -> None:
        """Prepare to solve a new episode from ``state``."""

        ...

    def act(self, state: BoardState) -> int:
        """Return the next canonical Sokoban action."""

        ...
