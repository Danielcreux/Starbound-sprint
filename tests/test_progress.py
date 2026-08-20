import json

from game.progress import DEFAULT_PROGRESS, ProgressStore


def test_missing_save_uses_defaults(tmp_path):
    assert ProgressStore(tmp_path / "missing.json").load() == DEFAULT_PROGRESS


def test_progress_round_trip_and_clamping(tmp_path):
    path = tmp_path / "progress.json"
    store = ProgressStore(path)
    store.save({"highest_level_unlocked": 9, "total_coins": 42})
    assert store.load() == {"highest_level_unlocked": 4, "total_coins": 42}
    assert json.loads(path.read_text(encoding="utf-8"))["highest_level_unlocked"] == 4


def test_corrupt_save_is_recovered(tmp_path):
    path = tmp_path / "progress.json"
    path.write_text("not-json", encoding="utf-8")
    assert ProgressStore(path).load() == DEFAULT_PROGRESS
