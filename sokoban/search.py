"""Shared state-space search for Sokoban solvers."""

from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import isfinite
from time import perf_counter
from typing import Callable, Literal

from sokoban.solver import BoardState, Position
from sokoban.transition import apply_action, legal_actions

Heuristic = Callable[[BoardState], float]
MoveHeuristic = Callable[[BoardState, tuple[int, ...], int], float]
SearchStatus = Literal["solved", "exhausted", "max_expansions"]
SearchKey = tuple[frozenset[Position], Position]


def manhattan_distance(state: BoardState) -> float:
    """Estimate remaining pushes from each box to its nearest goal."""

    return float(
        sum(
            min(
                abs(row - goal_row) + abs(column - goal_column)
                for goal_row, goal_column in state.goals
            )
            for row, column in state.boxes
        )
    )


@dataclass(frozen=True)
class SearchStats:
    expanded: int
    peak_queue: int
    elapsed_seconds: float


@dataclass(frozen=True)
class SearchResult:
    status: SearchStatus
    actions: tuple[int, ...] | None
    stats: SearchStats


def search(
    initial_state: BoardState,
    *,
    heuristic: Heuristic | None = None,
    heuristic_weight: float = 0.0,
    move_heuristic: MoveHeuristic | None = None,
    max_expansions: int | None = None,
) -> SearchResult:
    """Find a push-minimal solution using ``pushes + weight * heuristic``."""

    if not isfinite(heuristic_weight) or heuristic_weight < 0:
        raise ValueError("heuristic_weight must be finite and non-negative")
    if max_expansions is not None and max_expansions <= 0:
        raise ValueError("max_expansions must be positive")

    started = perf_counter()
    order = count()
    initial_paths = _reachable_paths(initial_state)
    initial_key = _key(initial_state, initial_paths)
    frontier: list[tuple[float, int, int, SearchKey, BoardState]] = []
    heappush(frontier, (0.0, next(order), 0, initial_key, initial_state))
    best_cost = {initial_key: 0}
    parents: dict[SearchKey, tuple[SearchKey, tuple[int, ...]] | None] = {
        initial_key: None
    }
    histories = {initial_key: ()}
    heuristic_cache: dict[SearchKey, float] = {}
    expanded = 0
    peak_queue = 1
    limit_reached = False

    while frontier:
        _, _, cost, key, state = heappop(frontier)
        if cost != best_cost[key]:
            continue
        if state.boxes == state.goals:
            return _result(
                "solved",
                _reconstruct(key, parents),
                started,
                expanded,
                peak_queue,
            )
        if max_expansions is not None and expanded >= max_expansions:
            limit_reached = True
            break

        expanded += 1
        paths = _reachable_paths(state)
        for successor, actions in _push_successors(state, paths):
            successor_cost = cost + 1
            successor_key = _key(successor)
            previous_cost = best_cost.get(successor_key)
            if previous_cost is not None and successor_cost >= previous_cost:
                continue

            best_cost[successor_key] = successor_cost
            parents[successor_key] = (key, actions)
            histories[successor_key] = (*histories[key], *actions)
            priority = float(successor_cost)
            if heuristic is not None and heuristic_weight:
                if successor_key not in heuristic_cache:
                    value = float(heuristic(successor))
                    if not isfinite(value):
                        raise ValueError("heuristic must return a finite number")
                    heuristic_cache[successor_key] = value
                priority += heuristic_weight * heuristic_cache[successor_key]
            if move_heuristic is not None:
                move_state = state
                for action in actions[:-1]:
                    move_state = apply_action(move_state, action)
                    assert move_state is not None
                value = float(
                    move_heuristic(
                        move_state,
                        (*histories[key], *actions[:-1]),
                        actions[-1],
                    )
                )
                if not isfinite(value):
                    raise ValueError("move heuristic must return a finite number")
                priority += value
            heappush(
                frontier,
                (priority, next(order), successor_cost, successor_key, successor),
            )
        peak_queue = max(peak_queue, len(frontier))

    status: SearchStatus = "max_expansions" if limit_reached else "exhausted"
    return _result(status, None, started, expanded, peak_queue)


def _reconstruct(
    goal: SearchKey,
    parents: dict[SearchKey, tuple[SearchKey, tuple[int, ...]] | None],
) -> tuple[int, ...]:
    actions: list[int] = []
    key = goal
    while parents[key] is not None:
        key, step_actions = parents[key]
        actions.extend(reversed(step_actions))
    actions.reverse()
    return tuple(actions)


def _reachable_paths(state: BoardState) -> dict[Position, tuple[int, ...]]:
    """Return shortest box-free walking paths from the player's position."""

    paths = {state.player: ()}
    queue = deque([state])
    while queue:
        current = queue.popleft()
        path = paths[current.player]
        for action in legal_actions(current):
            successor = apply_action(current, action)
            assert successor is not None
            if successor.boxes != state.boxes or successor.player in paths:
                continue
            paths[successor.player] = (*path, action)
            queue.append(successor)
    return paths


def _push_successors(
    state: BoardState,
    paths: dict[Position, tuple[int, ...]],
) -> tuple[tuple[BoardState, tuple[int, ...]], ...]:
    """Return every reachable push and the player actions needed to perform it."""

    successors: list[tuple[BoardState, tuple[int, ...]]] = []
    for player, path in paths.items():
        walking_state = BoardState(
            height=state.height,
            width=state.width,
            walls=state.walls,
            goals=state.goals,
            boxes=state.boxes,
            player=player,
        )
        for action in legal_actions(walking_state):
            successor = apply_action(walking_state, action)
            assert successor is not None
            if successor.boxes != state.boxes:
                successors.append((successor, (*path, action)))
    return tuple(successors)


def _key(
    state: BoardState,
    paths: dict[Position, tuple[int, ...]] | None = None,
) -> SearchKey:
    reachable = paths if paths is not None else _reachable_paths(state)
    return state.boxes, min(reachable)


def _result(
    status: SearchStatus,
    actions: tuple[int, ...] | None,
    started: float,
    expanded: int,
    peak_queue: int,
) -> SearchResult:
    return SearchResult(
        status=status,
        actions=actions,
        stats=SearchStats(
            expanded=expanded,
            peak_queue=peak_queue,
            elapsed_seconds=perf_counter() - started,
        ),
    )
