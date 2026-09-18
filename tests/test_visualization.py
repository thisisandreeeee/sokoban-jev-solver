import numpy as np
import pygame
import pytest

from sokoban.visualization import PygameRenderer, WindowClosed


def test_pygame_renderer_accepts_engine_frame(monkeypatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    renderer = PygameRenderer(scale=2, fps=1000)
    frame = np.zeros((16, 24, 3), dtype=np.uint8)
    renderer(frame)
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    with pytest.raises(WindowClosed):
        renderer(frame)
    renderer.close()


def test_pygame_renderer_waits_for_close(monkeypatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    renderer = PygameRenderer(scale=2, fps=1000)
    renderer(np.zeros((16, 24, 3), dtype=np.uint8))
    pygame.event.post(pygame.event.Event(pygame.QUIT))

    renderer.wait_until_closed()
    renderer.close()
