"""Persistent player progress with safe defaults."""

import json
from pathlib import Path
from typing import Any


DEFAULT_PROGRESS = {"highest_level_unlocked": 1, "total_coins": 0}


class ProgressStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, int]:
        try:
            raw: Any = json.loads(self.path.read_text(encoding="utf-8"))
            highest = max(1, min(4, int(raw.get("highest_level_unlocked", 1))))
            coins = max(0, int(raw.get("total_coins", 0)))
            return {"highest_level_unlocked": highest, "total_coins": coins}
        except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
            return DEFAULT_PROGRESS.copy()

    def save(self, progress: dict[str, int]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        safe = {
            "highest_level_unlocked": max(1, min(4, int(progress["highest_level_unlocked"]))),
            "total_coins": max(0, int(progress["total_coins"])),
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(safe, indent=2), encoding="utf-8")
        temporary.replace(self.path)
