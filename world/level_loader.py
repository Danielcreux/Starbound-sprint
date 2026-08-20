"""Validated JSON level loading."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


class LevelFormatError(ValueError):
    pass


@dataclass(frozen=True)
class LevelData:
    name: str
    hint: str
    layout: tuple[tuple[int, ...], ...]
    enemy_types: tuple[str, ...]
    powerup_types: tuple[str, ...]
    spawn: tuple[int, int]

    @property
    def width(self) -> int:
        return len(self.layout[0])

    @property
    def height(self) -> int:
        return len(self.layout)


def load_level(path: Path) -> LevelData:
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LevelFormatError(f"Level not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LevelFormatError(f"Invalid JSON in {path.name}: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("layout"), list) or not raw["layout"]:
        raise LevelFormatError("A level needs a non-empty 'layout' list")
    layout: list[tuple[int, ...]] = []
    expected_width: int | None = None
    for row_number, row in enumerate(raw["layout"], 1):
        if isinstance(row, str):
            row = list(row)
        if not isinstance(row, list) or not row:
            raise LevelFormatError(f"Row {row_number} must be a non-empty list or digit string")
        try:
            parsed = tuple(int(value) for value in row)
        except (TypeError, ValueError) as exc:
            raise LevelFormatError(f"Row {row_number} contains a non-integer tile") from exc
        if any(tile < 0 or tile > 9 for tile in parsed):
            raise LevelFormatError(f"Row {row_number} contains an unknown tile")
        if expected_width is None:
            expected_width = len(parsed)
        elif len(parsed) != expected_width:
            raise LevelFormatError("All layout rows must have the same width")
        layout.append(parsed)
    flattened = [tile for row in layout for tile in row]
    for required, label in ((8, "goal"),):
        if required not in flattened:
            raise LevelFormatError(f"Level has no {label} tile")
    spawn_raw = raw.get("spawn", [1, 1])
    if not isinstance(spawn_raw, list) or len(spawn_raw) != 2:
        raise LevelFormatError("'spawn' must be [column, row]")
    try:
        spawn = (int(spawn_raw[0]), int(spawn_raw[1]))
    except (TypeError, ValueError) as exc:
        raise LevelFormatError("Spawn coordinates must be integers") from exc
    return LevelData(
        name=str(raw.get("name", path.stem)),
        hint=str(raw.get("hint", "")),
        layout=tuple(layout),
        enemy_types=tuple(str(x) for x in raw.get("enemy_types", [])),
        powerup_types=tuple(str(x) for x in raw.get("powerup_types", [])),
        spawn=spawn,
    )
