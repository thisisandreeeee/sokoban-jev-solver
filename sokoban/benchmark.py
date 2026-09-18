"""Benchmark a solver across the bundled Microban levels."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from statistics import median
from time import perf_counter
from typing import Literal

from sokoban.env import GymSokobanEnv
from sokoban.levels import Level, load_bundled_levels, select_level
from sokoban.search import Heuristic, SearchStats, manhattan_distance, search
from sokoban.solver import BoardState
from sokoban.transition import apply_action

BenchmarkStatus = Literal["solved", "exhausted", "max_expansions", "error"]


@dataclass(frozen=True)
class BenchmarkResult:
    level: int
    name: str
    status: BenchmarkStatus
    solution_steps: int | None
    solution_valid: bool
    stats: SearchStats | None
    total_seconds: float
    error: str | None = None


def run_benchmark(
    levels: Iterable[tuple[int, Level]],
    *,
    heuristic: Heuristic | None = None,
    max_expansions: int | None = 1_000_000,
) -> tuple[BenchmarkResult, ...]:
    """Search every supplied level and retain its metrics in memory."""

    results: list[BenchmarkResult] = []
    for number, level in levels:
        started = perf_counter()
        env: GymSokobanEnv | None = None
        try:
            env = GymSokobanEnv(level.board)
            initial_state = env.reset()
            result = search(
                initial_state,
                heuristic=heuristic,
                heuristic_weight=float(heuristic is not None),
                max_expansions=max_expansions,
            )
            actions = result.actions
            valid = actions is not None and _valid_solution(initial_state, actions)
            results.append(
                BenchmarkResult(
                    level=number,
                    name=level.name,
                    status=result.status,
                    solution_steps=len(actions) if actions is not None else None,
                    solution_valid=valid,
                    stats=result.stats,
                    total_seconds=perf_counter() - started,
                )
            )
        except Exception as error:
            results.append(
                BenchmarkResult(
                    level=number,
                    name=level.name,
                    status="error",
                    solution_steps=None,
                    solution_valid=False,
                    stats=None,
                    total_seconds=perf_counter() - started,
                    error=f"{type(error).__name__}: {error}",
                )
            )
        finally:
            if env is not None:
                env.close()
    return tuple(results)


def _valid_solution(initial_state: BoardState, actions: tuple[int, ...]) -> bool:
    state = initial_state
    for action in actions:
        successor = apply_action(state, action)
        if successor is None:
            return False
        state = successor
    return state.boxes == state.goals


def _print_result(result: BenchmarkResult) -> None:
    stats = result.stats
    fields = (
        f"{result.name + ':':<14}",
        f"{'status=' + result.status:<22}",
        f"{'solved=' + str(result.status == 'solved'):<13}",
        f"{'steps=' + _value(result.solution_steps):<13}",
        f"{'expanded=' + _value(stats.expanded if stats else None):<18}",
        f"{'peak_queue=' + _value(stats.peak_queue if stats else None):<18}",
        f"search_s={stats.elapsed_seconds if stats else 0:.3f}",
        f"total_s={result.total_seconds:.3f}",
    )
    print(
        "\t".join(fields),
        flush=True,
    )
    if result.error:
        print(f"      {result.error}", flush=True)


def _print_summary(results: tuple[BenchmarkResult, ...]) -> None:

    statuses = Counter(result.status for result in results)
    search_times = [
        result.stats.elapsed_seconds for result in results if result.stats is not None
    ]
    total_seconds = sum(result.total_seconds for result in results)
    print(
        "Summary: "
        f"attempted={len(results)} solved={statuses['solved']} "
        f"exhausted={statuses['exhausted']} "
        f"limited={statuses['max_expansions']} errors={statuses['error']} "
        f"valid={sum(result.solution_valid for result in results)} "
        f"median_search_s={median(search_times) if search_times else 0:.3f} "
        f"total_s={total_seconds:.3f}"
    )


def _value(value: int | None) -> str:
    return "-" if value is None else str(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--level",
        type=int,
        action="append",
        help="Microban level to run; repeat as needed (default: all 155)",
    )
    parser.add_argument("--heuristic", choices=("manhattan",))
    parser.add_argument("--max-expansions", type=int, default=1_000_000)
    args = parser.parse_args(argv)

    levels = load_bundled_levels()
    try:
        selected = (
            tuple((number, select_level(levels, number)) for number in args.level)
            if args.level
            else tuple(enumerate(levels, 1))
        )
    except ValueError as error:
        parser.error(str(error))

    heuristic = manhattan_distance if args.heuristic == "manhattan" else None
    collected: list[BenchmarkResult] = []
    for item in selected:
        result = run_benchmark(
            (item,),
            heuristic=heuristic,
            max_expansions=args.max_expansions,
        )[0]
        collected.append(result)
        _print_result(result)
    results = tuple(collected)
    _print_summary(results)
    return int(any(result.status == "error" for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
