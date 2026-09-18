from main import main


def test_solver_runs_end_to_end_without_rendering(capsys) -> None:
    assert (
        main(["--no-render", "--solver", "bfs", "--max-steps", "100", "--level", "1"])
        == 0
    )
    output = capsys.readouterr().out
    assert "Microban 1: solved=True, steps=33, time=" in output
    assert output.rstrip().endswith("s")
