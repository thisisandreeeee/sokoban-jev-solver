"""Load single-level or multi-level XSB files."""

from dataclasses import dataclass
from importlib.resources import files


@dataclass(frozen=True)
class Level:
    """A named Sokoban board ready for the environment adapter."""

    name: str
    board: str


def parse_levels(text: str) -> tuple[Level, ...]:
    """Parse XSB boards separated by blank lines; ``;`` lines name boards."""

    levels: list[Level] = []
    title: str | None = None
    board: list[str] = []

    def finish() -> None:
        nonlocal title, board
        if board:
            levels.append(Level(title or f"Level {len(levels) + 1}", "\n".join(board)))
        title, board = None, []

    for line in text.splitlines():
        if line.startswith(";"):
            if board:
                finish()
            title = line.removeprefix(";").strip() or None
        elif not line.strip():
            finish()
        else:
            board.append(line.rstrip())
    finish()

    if not levels:
        raise ValueError("XSB file contains no levels")
    return tuple(levels)


def load_bundled_levels() -> tuple[Level, ...]:
    """Load the five bundled Microban levels."""

    return parse_levels(files(__package__).joinpath("microban.xsb").read_text())


def select_level(levels: tuple[Level, ...], number: int) -> Level:
    """Select a level by one-based number."""

    if number < 1 or number > len(levels):
        raise ValueError(f"level number must be between 1 and {len(levels)}")
    return levels[number - 1]
