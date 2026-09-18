"""Jev-powered Sokoban solver."""

from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient

from sokoban.solver import BoardState, SokobanAction


class JevSolver:
    """Ask Jev to choose each move from the four canonical directions."""

    def __init__(self, client: TypeSafeClient | None = None) -> None:
        if client is None:
            load_dotenv()
            client = TypeSafeClient()
        self._client = client
        self._past_moves: list[str] = []

    def reset(self, state: BoardState) -> None:
        """Forget moves from the previous episode."""

        self._past_moves.clear()

    def act(self, state: BoardState) -> int:
        """Return Jev's top choice and retain it as context for later moves."""

        response = self._client.system_one(
            state={
                "board": {
                    "height": state.height,
                    "width": state.width,
                    "walls": sorted(state.walls),
                    "goals": sorted(state.goals),
                    "boxes": sorted(state.boxes),
                    "player": state.player,
                },
                "past_moves": self._past_moves.copy(),
            },
            questions={
                "move": Choice(
                    instructions=(
                        "Which move should the player make next to solve the "
                        "Sokoban board?"
                    ),
                    criteria={
                        "left": None,
                        "right": None,
                        "up": None,
                        "down": None,
                    },
                )
            },
        )
        move = response.choices["move"].choice
        self._past_moves.append(move)
        return SokobanAction[move.upper()]
