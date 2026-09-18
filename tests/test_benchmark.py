from sokoban.benchmark import main, run_benchmark
from sokoban.levels import Level


def test_benchmark_collects_metrics_and_continues_after_limit() -> None:
    levels = (
        (1, Level("Easy", "#####\n#@$.#\n#####")),
        (2, Level("Limited", "#######\n#@ $ .#\n#######")),
    )

    results = run_benchmark(levels, max_expansions=1)

    assert results[0].status == "solved"
    assert results[0].solution_steps == 1
    assert results[0].solution_valid
    assert results[1].status == "max_expansions"
    assert results[1].stats is not None


def test_benchmark_cli_prints_level_metrics_and_summary(capsys) -> None:
    assert main(["--level", "1", "--max-expansions", "1000"]) == 0

    output = capsys.readouterr().out
    assert "Running Microban 1 (1/1)..." in output
    assert "Microban 1:" in output
    assert "\tstatus=solved" in output
    assert "\tsolved=True" in output
    assert "\tsteps=33" in output
    assert "\texpanded=51" in output
    assert "Summary: attempted=1 solved=1" in output
