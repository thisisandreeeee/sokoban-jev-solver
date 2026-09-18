"""Engine-neutral Sokoban state transitions for search algorithms."""

from dataclasses import replace

from sokoban.solver import BoardState, Position, SokobanAction

_DELTAS: dict[SokobanAction, Position] = {
    SokobanAction.UP: (-1, 0),
    SokobanAction.DOWN: (1, 0),
    SokobanAction.LEFT: (0, -1),
    SokobanAction.RIGHT: (0, 1),
}


def apply_action(state: BoardState, action: int) -> BoardState | None:
    """Return the successor state, or ``None`` if the action is illegal."""

    if isinstance(action, bool) or not isinstance(action, int):
        raise ValueError(f"invalid Sokoban action: {action!r}")
    try:
        direction = SokobanAction(action)
    except ValueError:
        raise ValueError(f"invalid Sokoban action: {action!r}") from None

    row_delta, column_delta = _DELTAS[direction]
    row, column = state.player
    destination = (row + row_delta, column + column_delta)

    if not _is_open(state, destination):
        return None
    if destination not in state.boxes:
        return replace(state, player=destination)

    box_destination = (
        destination[0] + row_delta,
        destination[1] + column_delta,
    )
    if not _is_open(state, box_destination) or box_destination in state.boxes:
        return None

    boxes = (state.boxes - {destination}) | {box_destination}
    return replace(state, boxes=frozenset(boxes), player=destination)


def legal_actions(state: BoardState) -> tuple[int, ...]:
    """Return the canonical actions that produce a successor state."""

    return tuple(action for action in SokobanAction if apply_action(state, action))


def _is_open(state: BoardState, position: Position) -> bool:
    row, column = position
    return (
        0 <= row < state.height
        and 0 <= column < state.width
        and position not in state.walls
    )
