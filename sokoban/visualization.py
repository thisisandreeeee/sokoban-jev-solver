"""Interactive display for RGB frames produced by the Sokoban engine."""

from __future__ import annotations

import numpy as np
import pygame
from numpy.typing import NDArray


class WindowClosed(Exception):
    """Raised when the user closes the visualization window."""


class PygameRenderer:
    """Display environment RGB frames at a watchable rate."""

    _CONTROLS_HEIGHT = 48

    def __init__(self, *, scale: int = 4, fps: float = 8) -> None:
        if scale <= 0 or fps <= 0:
            raise ValueError("scale and fps must be positive")
        self._scale = scale
        self._fps = fps
        self._screen: pygame.Surface | None = None
        self._clock = pygame.time.Clock()
        self._frames: list[NDArray[np.uint8]] = []
        self._board_size = (0, 0)
        self._slider_rect = pygame.Rect(0, 0, 0, 0)
        self._selected_step = 0
        self._follow_latest = True
        self._dragging = False
        self._font: pygame.font.Font | None = None

    @property
    def selected_step(self) -> int:
        """Return the zero-based step currently displayed."""

        return self._selected_step

    @property
    def total_steps(self) -> int:
        """Return the latest available step number."""

        return max(0, len(self._frames) - 1)

    def __call__(self, frame: NDArray[np.uint8]) -> None:
        height, width = frame.shape[:2]
        self._board_size = (width * self._scale, height * self._scale)
        if self._screen is None:
            pygame.display.init()
            pygame.font.init()
            pygame.display.set_caption("Sokoban Solver")
            window_size = (
                self._board_size[0],
                self._board_size[1] + self._CONTROLS_HEIGHT,
            )
            self._screen = pygame.display.set_mode(window_size)
            self._font = pygame.font.Font(None, 20)
            self._slider_rect = pygame.Rect(
                12, self._board_size[1] + 6, self._board_size[0] - 24, 18
            )

        self._frames.append(frame.copy())
        if self._follow_latest:
            self._selected_step = self.total_steps
        for event in pygame.event.get():
            if not self._handle_event(event):
                raise WindowClosed

        self._draw()
        self._clock.tick(self._fps)

    def _handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._slider_rect.collidepoint(event.pos):
                self._dragging = True
                self._select_step(event.pos[0])
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._select_step(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._select_step(event.pos[0])
                self._dragging = False
        return True

    def _select_step(self, mouse_x: int) -> None:
        ratio = (mouse_x - self._slider_rect.left) / self._slider_rect.width
        ratio = min(1.0, max(0.0, ratio))
        self._selected_step = round(ratio * self.total_steps)
        self._follow_latest = self._selected_step == self.total_steps

    def _draw(self) -> None:
        assert self._screen is not None and self._font is not None
        frame = self._frames[self._selected_step]
        surface = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
        self._screen.blit(pygame.transform.scale(surface, self._board_size), (0, 0))

        controls = pygame.Rect(
            0, self._board_size[1], self._board_size[0], self._CONTROLS_HEIGHT
        )
        self._screen.fill("#20242b", controls)
        track_y = self._slider_rect.centery
        pygame.draw.line(
            self._screen,
            "#7c8491",
            (self._slider_rect.left, track_y),
            (self._slider_rect.right, track_y),
            3,
        )
        handle_x = self._slider_rect.left
        if self.total_steps:
            handle_x += round(
                self._slider_rect.width * self._selected_step / self.total_steps
            )
        pygame.draw.circle(self._screen, "#f2f4f8", (handle_x, track_y), 7)

        label = self._font.render(
            f"Step {self._selected_step} / {self.total_steps}", True, "#f2f4f8"
        )
        self._screen.blit(
            label,
            ((self._board_size[0] - label.get_width()) // 2, controls.top + 26),
        )
        pygame.display.flip()

    def wait_until_closed(self) -> None:
        """Keep the replay controls active until the user closes the window."""

        while self._handle_event(pygame.event.wait()):
            self._draw()

    def close(self) -> None:
        pygame.quit()
