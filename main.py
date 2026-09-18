"""Run a Sokoban solver against a selected XSB level."""

from __future__ import annotations

import argparse
from time import perf_counter
from typing import Sequence

from sokoban.env import GymSokobanEnv
from sokoban.levels import load_bundled_levels, select_level
from sokoban.runner import run_episode
from sokoban.solvers import BFSSolver, RandomSolver
from sokoban.visualization import PygameRenderer, WindowClosed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--fps", type=float, default=8)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--level", type=int, default=1, help="Microban level (1-5)")
    parser.add_argument("--solver", choices=("bfs", "random"), default="bfs")
    args = parser.parse_args(argv)

    try:
        level = select_level(load_bundled_levels(), args.level)
    except ValueError as error:
        parser.error(str(error))

    env = GymSokobanEnv(level.board, max_steps=args.max_steps)
    renderer = None if args.no_render else PygameRenderer(scale=args.scale, fps=args.fps)
    solver = BFSSolver() if args.solver == "bfs" else RandomSolver(seed=args.seed)

    try:
        started = perf_counter()
        result = run_episode(
            env,
            solver,
            max_steps=args.max_steps,
            render=renderer,
        )
        elapsed = perf_counter() - started
        print(
            f"{level.name}: solved={result.solved}, "
            f"steps={result.num_steps}, time={elapsed:.3f}s"
        )
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
