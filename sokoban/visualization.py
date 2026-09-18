"""Interactive display for RGB frames produced by the Sokoban engine."""

from __future__ import annotations

import numpy as np
import pygame
from numpy.typing import NDArray


class WindowClosed(Exception):
    """Raised when the user closes the visualization window."""


class PygameRenderer:
    """Display environment RGB frames at a watchable rate."""

    def __init__(self, *, scale: int = 4, fps: float = 8) -> None:
        if scale <= 0 or fps <= 0:
            raise ValueError("scale and fps must be positive")
        self._scale = scale
        self._fps = fps
        self._screen: pygame.Surface | None = None
        self._clock = pygame.time.Clock()

    def __call__(self, frame: NDArray[np.uint8]) -> None:
        height, width = frame.shape[:2]
        size = (width * self._scale, height * self._scale)
        if self._screen is None:
            pygame.display.init()
            pygame.display.set_caption("Sokoban Solver")
            self._screen = pygame.display.set_mode(size)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise WindowClosed

        surface = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
        self._screen.blit(pygame.transform.scale(surface, size), (0, 0))
        pygame.display.flip()
        self._clock.tick(self._fps)

    def wait_until_closed(self) -> None:
        """Keep the final frame visible until the user closes the window."""

        while pygame.event.wait().type != pygame.QUIT:
            pass

    def close(self) -> None:
        pygame.quit()
