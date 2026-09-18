from unittest.mock import patch

from main import main
from sokoban.search import manhattan_distance
from sokoban.solvers import RandomSolver


def test_solver_runs_end_to_end_without_rendering(capsys) -> None:
    assert (
        main(["--no-render", "--solver", "bfs", "--max-steps", "100", "--level", "1"])
        == 0
    )
    output = capsys.readouterr().out
    assert "Microban 1: solved=True, steps=33, time=" in output
    assert ", expanded=39, peak_queue=15" in output


def test_manhattan_heuristic_runs_end_to_end(capsys) -> None:
    assert main(["--no-render", "--heuristic", "manhattan", "--level", "1"]) == 0
    assert "Microban 1: solved=True, steps=33, time=" in capsys.readouterr().out


def test_jev_heuristic_flag_is_additive(capsys) -> None:
    with patch("main.BFSSolver", return_value=RandomSolver(seed=1)) as bfs:
        assert main(["--no-render", "--jev", "--max-steps", "1"]) == 0

    bfs.assert_called_once_with(heuristic=manhattan_distance, jev=True)
    assert "api_calls=0" in capsys.readouterr().out
