"""Game state declarations."""

from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    LEVEL_SELECT = auto()
    CONTROLS = auto()
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()
    VICTORY = auto()
