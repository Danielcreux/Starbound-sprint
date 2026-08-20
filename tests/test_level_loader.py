import json

import pytest

from world.level_loader import LevelFormatError, load_level
from world.level import Level


def test_loads_digit_string_layout(tmp_path):
    path = tmp_path / "level.json"
    path.write_text(json.dumps({"name": "Test", "layout": ["000", "018"]}), encoding="utf-8")
    data = load_level(path)
    assert data.width == 3
    assert data.height == 2
    assert data.layout[1] == (0, 1, 8)


def test_rejects_ragged_layout(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"layout": ["000", "08"]}), encoding="utf-8")
    with pytest.raises(LevelFormatError, match="same width"):
        load_level(path)


def test_all_shipped_levels_are_valid():
    from game.settings import LEVELS_DIR

    levels = [load_level(LEVELS_DIR / f"level_{number}.json") for number in range(1, 5)]
    assert [level.width for level in levels] == [40, 50, 45, 62]
    assert all(8 in (tile for row in level.layout for tile in row) for level in levels)
    assert all(2 in (tile for row in level.layout for tile in row) for level in levels)


def test_enemy_and_power_progression_in_shipped_levels():
    from game.settings import LEVELS_DIR

    levels = [load_level(LEVELS_DIR / f"level_{number}.json") for number in range(1, 5)]
    enemy_counts = [sum(tile == 5 for row in data.layout for tile in row) for data in levels]
    power_counts = [sum(tile == 6 for row in data.layout for tile in row) for data in levels]
    assert enemy_counts == [1, 3, 5, 8]
    assert power_counts == [1, 1, 2, 2]


def test_enemy_reset_restores_defeated_and_moved_enemies():
    from game.settings import LEVELS_DIR

    level = Level(load_level(LEVELS_DIR / "level_2.json"))
    starts = [enemy.hitbox.topleft for enemy in level.enemies]
    level.enemies[0].take_damage()
    level.enemies[1].hitbox.x += 200
    level.reset_enemies()
    assert all(enemy.alive for enemy in level.enemies)
    assert [enemy.hitbox.topleft for enemy in level.enemies] == starts
