"""Generic Sokoban episode execution."""

from dataclasses import dataclass
from typing import Callable, Protocol

import numpy as np
from numpy.typing import NDArray

from sokoban.solver import BoardState, SokobanSolver, StepResult

FrameCallback = Callable[[NDArray[np.uint8]], None]


class EpisodeEnvironment(Protocol):
    """Small environment surface required by the episode runner."""

    def reset(self) -> BoardState: ...

    def step(self, action: int) -> StepResult: ...

    def render_rgb(self) -> NDArray[np.uint8]: ...


@dataclass(frozen=True)
class TrajectoryStep:
    """One action and its resulting state."""

    number: int
    action: int
    state: BoardState
    reward: float
    solved: bool
    terminated: bool
    truncated: bool


@dataclass(frozen=True)
class EpisodeResult:
    """Structured outcome returned by :func:`run_episode`."""

    solved: bool
    num_steps: int
    trajectory: tuple[TrajectoryStep, ...]
    initial_state: BoardState
    terminated: bool
    truncated: bool
    max_steps_reached: bool


def run_episode(
    env: EpisodeEnvironment,
    solver: SokobanSolver,
    *,
    max_steps: int = 120,
    render: FrameCallback | None = None,
) -> EpisodeResult:
    """Run one solver episode against any compatible Sokoban environment."""

    if max_steps <= 0:
        raise ValueError("max_steps must be positive")

    initial_state = env.reset()
    solver.reset(initial_state)
    if render is not None:
        render(env.render_rgb())

    if initial_state.boxes == initial_state.goals:
        return EpisodeResult(
            solved=True,
            num_steps=0,
            trajectory=(),
            initial_state=initial_state,
            terminated=True,
            truncated=False,
            max_steps_reached=False,
        )

    trajectory: list[TrajectoryStep] = []
    state = initial_state
    terminated = False
    truncated = False

    for number in range(1, max_steps + 1):
        action = solver.act(state)
        step = env.step(action)
        state = step.state
        trajectory.append(
            TrajectoryStep(
                number=number,
                action=int(action),
                state=state,
                reward=step.reward,
                solved=step.solved,
                terminated=step.terminated,
                truncated=step.truncated,
            )
        )
        if render is not None:
            render(env.render_rgb())
        terminated = step.terminated
        truncated = step.truncated
        if step.solved or terminated or truncated:
            break

    solved = trajectory[-1].solved
    max_steps_reached = len(trajectory) == max_steps and not (
        solved or terminated or truncated
    )
    return EpisodeResult(
        solved=solved,
        num_steps=len(trajectory),
        trajectory=tuple(trajectory),
        initial_state=initial_state,
        terminated=terminated,
        truncated=truncated or max_steps_reached,
        max_steps_reached=max_steps_reached,
    )
