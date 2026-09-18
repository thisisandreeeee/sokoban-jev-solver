from unittest.mock import patch

from main import main
from sokoban.solvers import RandomSolver


def test_solver_runs_end_to_end_without_rendering(capsys) -> None:
    assert (
        main(["--no-render", "--solver", "bfs", "--max-steps", "100", "--level", "1"])
        == 0
    )
    output = capsys.readouterr().out
    assert "Microban 1: solved=True, steps=33, time=" in output
    assert output.rstrip().endswith("s")


def test_manhattan_heuristic_runs_end_to_end(capsys) -> None:
    assert main(["--no-render", "--heuristic", "manhattan", "--level", "1"]) == 0
    assert "Microban 1: solved=True, steps=33, time=" in capsys.readouterr().out


def test_jev_solver_flag(capsys) -> None:
    with patch("main.JevSolver", return_value=RandomSolver(seed=1)) as jev:
        assert main(["--no-render", "--solver", "jev", "--max-steps", "1"]) == 0

    jev.assert_called_once_with()
    assert "Microban 1:" in capsys.readouterr().out
