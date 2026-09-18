"""Shared state-space search for Sokoban solvers."""

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import isfinite
from time import perf_counter
from typing import Callable

from sokoban.solver import BoardState
from sokoban.transition import apply_action, legal_actions

Heuristic = Callable[[BoardState], float]


@dataclass(frozen=True)
class SearchStats:
    expanded: int
    generated: int
    max_frontier: int
    elapsed_seconds: float


@dataclass(frozen=True)
class SearchResult:
    actions: tuple[int, ...] | None
    stats: SearchStats


def search(
    initial_state: BoardState,
    *,
    heuristic: Heuristic | None = None,
    heuristic_weight: float = 0.0,
    max_expansions: int | None = None,
) -> SearchResult:
    """Find a solution using ``cost + weight * heuristic`` ordering."""

    if not isfinite(heuristic_weight) or heuristic_weight < 0:
        raise ValueError("heuristic_weight must be finite and non-negative")
    if max_expansions is not None and max_expansions <= 0:
        raise ValueError("max_expansions must be positive")

    started = perf_counter()
    order = count()
    frontier: list[tuple[float, int, int, BoardState]] = []
    heappush(frontier, (0.0, next(order), 0, initial_state))
    best_cost = {initial_state: 0}
    parents: dict[BoardState, tuple[BoardState, int] | None] = {
        initial_state: None
    }
    heuristic_cache: dict[BoardState, float] = {}
    expanded = 0
    generated = 1
    max_frontier = 1

    while frontier:
        _, _, cost, state = heappop(frontier)
        if cost != best_cost[state]:
            continue
        if state.boxes == state.goals:
            return _result(
                _reconstruct(state, parents),
                started,
                expanded,
                generated,
                max_frontier,
            )
        if max_expansions is not None and expanded >= max_expansions:
            break

        expanded += 1
        for action in legal_actions(state):
            successor = apply_action(state, action)
            assert successor is not None
            successor_cost = cost + 1
            previous_cost = best_cost.get(successor)
            if previous_cost is not None and successor_cost >= previous_cost:
                continue

            best_cost[successor] = successor_cost
            parents[successor] = (state, action)
            priority = float(successor_cost)
            if heuristic is not None and heuristic_weight:
                if successor not in heuristic_cache:
                    value = float(heuristic(successor))
                    if not isfinite(value):
                        raise ValueError("heuristic must return a finite number")
                    heuristic_cache[successor] = value
                priority += heuristic_weight * heuristic_cache[successor]
            heappush(
                frontier,
                (priority, next(order), successor_cost, successor),
            )
            generated += 1
        max_frontier = max(max_frontier, len(frontier))

    return _result(None, started, expanded, generated, max_frontier)


def _reconstruct(
    goal: BoardState,
    parents: dict[BoardState, tuple[BoardState, int] | None],
) -> tuple[int, ...]:
    actions: list[int] = []
    state = goal
    while parents[state] is not None:
        state, action = parents[state]
        actions.append(action)
    actions.reverse()
    return tuple(actions)


def _result(
    actions: tuple[int, ...] | None,
    started: float,
    expanded: int,
    generated: int,
    max_frontier: int,
) -> SearchResult:
    return SearchResult(
        actions=actions,
        stats=SearchStats(
            expanded=expanded,
            generated=generated,
            max_frontier=max_frontier,
            elapsed_seconds=perf_counter() - started,
        ),
    )
