"""Uniform random baseline solver."""

from random import Random

from sokoban.solver import BoardState, SokobanAction


class RandomSolver:
    """Choose uniformly from the four canonical actions."""

    def __init__(self, seed: int | None = None) -> None:
        self._seed = seed
        self._random = Random(seed)

    def reset(self, state: BoardState) -> None:
        """Restart the configured random sequence for a new episode."""

        self._random.seed(self._seed)

    def act(self, state: BoardState) -> int:
        """Return a random engine-neutral action."""

        return self._random.randrange(len(SokobanAction))
