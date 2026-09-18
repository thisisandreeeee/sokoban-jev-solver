from sokoban.env import GymSokobanEnv
from sokoban.search import manhattan_distance, search
from sokoban.solver import SokobanAction

SOLVABLE = "#####\n#@$.#\n#####"
UNSOLVABLE = "#####\n#@  #\n#$#.#\n#####"


def state_for(level: str):
    env = GymSokobanEnv(level)
    state = env.reset()
    env.close()
    return state


def test_zero_heuristic_search_finds_shortest_plan() -> None:
    result = search(state_for(SOLVABLE))

    assert result.status == "solved"
    assert result.actions == (SokobanAction.RIGHT,)
    assert result.stats.expanded == 1
    assert result.stats.peak_queue == 1
    assert result.stats.elapsed_seconds >= 0


def test_manhattan_distance_sums_each_box_to_its_nearest_goal() -> None:
    state = state_for("#######\n#@ $ .#\n# $  .#\n#######")

    assert manhattan_distance(state) == 5


def test_search_reports_when_no_solution_exists() -> None:
    result = search(state_for(UNSOLVABLE))

    assert result.status == "exhausted"
    assert result.actions is None


def test_search_reports_expansion_limit() -> None:
    result = search(state_for("######\n#@ $.#\n######"), max_expansions=1)

    assert result.status == "max_expansions"
    assert result.actions is None


def test_zero_weight_does_not_evaluate_heuristic() -> None:
    def unexpected_heuristic(state):
        raise AssertionError("zero-weight BFS must not evaluate its heuristic")

    result = search(
        state_for(SOLVABLE),
        heuristic=unexpected_heuristic,
        heuristic_weight=0,
    )

    assert result.actions == (SokobanAction.RIGHT,)
