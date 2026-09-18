from sokoban.env import GymSokobanEnv
from sokoban.levels import load_bundled_levels, parse_levels, select_level


def test_loads_and_selects_all_bundled_levels() -> None:
    levels = load_bundled_levels()

    assert len(levels) == 155
    assert select_level(levels, 3).name == "Microban 3"
    assert select_level(levels, 155).name == "Microban 155"

    for level in levels:
        env = GymSokobanEnv(level.board)
        env.reset()
        env.close()


def test_parses_unnamed_single_level() -> None:
    levels = parse_levels("#####\n#@$.#\n#####\n")

    assert levels[0].name == "Level 1"
    assert levels[0].board == "#####\n#@$.#\n#####"
