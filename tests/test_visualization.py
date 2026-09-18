import numpy as np
import pygame
import pytest

from sokoban.visualization import PygameRenderer, WindowClosed


def test_pygame_renderer_accepts_engine_frame(monkeypatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    renderer = PygameRenderer(scale=2, fps=1000)
    frame = np.zeros((16, 24, 3), dtype=np.uint8)
    renderer(frame)
    assert renderer.selected_step == renderer.total_steps == 0
    renderer(frame)
    assert renderer.selected_step == renderer.total_steps == 1
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


def test_pygame_renderer_slider_selects_recorded_step(monkeypatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    renderer = PygameRenderer(scale=2, fps=1000)
    renderer(np.zeros((16, 24, 3), dtype=np.uint8))
    renderer(np.full((16, 24, 3), 255, dtype=np.uint8))

    slider = renderer._slider_rect
    pygame.event.post(
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=(slider.left, slider.centery)
        )
    )
    pygame.event.post(
        pygame.event.Event(
            pygame.MOUSEBUTTONUP, button=1, pos=(slider.left, slider.centery)
        )
    )
    pygame.event.post(pygame.event.Event(pygame.QUIT))

    renderer.wait_until_closed()

    assert renderer.selected_step == 0
    assert renderer.total_steps == 1
    renderer.close()
