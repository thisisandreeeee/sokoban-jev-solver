"""Run the random solver against Microban level 1."""

from __future__ import annotations

import argparse
from importlib.resources import files
from typing import Sequence

from sokoban.env import GymSokobanEnv
from sokoban.runner import run_episode
from sokoban.solvers import RandomSolver
from sokoban.visualization import PygameRenderer, WindowClosed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--fps", type=float, default=8)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args(argv)

    level = files("sokoban.levels").joinpath("microban_001.xsb").read_text()
    env = GymSokobanEnv(level, max_steps=args.max_steps)
    renderer = None if args.no_render else PygameRenderer(scale=args.scale, fps=args.fps)

    try:
        result = run_episode(
            env,
            RandomSolver(seed=args.seed),
            max_steps=args.max_steps,
            render=renderer,
        )
        print(f"Microban 1: solved={result.solved}, steps={result.num_steps}")
        if renderer is not None:
            renderer.wait_until_closed()
    except WindowClosed:
        print("Visualization closed before the episode finished.")
        return 0
    finally:
        env.close()
        if renderer is not None:
            renderer.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
