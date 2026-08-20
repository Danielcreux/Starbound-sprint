"""Transparent arcade-style in-game HUD."""

import pygame
from game import settings


class HUD:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 25)
        self.value_font = pygame.font.Font(None, 25)
        self.small = pygame.font.Font(None, 20)

    @staticmethod
    def _blit_text(
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int] = settings.WHITE,
    ) -> None:
        """Draw crisp text with a small readability shadow and no backdrop."""
        shadow = font.render(text, False, (25, 35, 58))
        image = font.render(text, False, color)
        surface.blit(shadow, (position[0] + 2, position[1] + 2))
        surface.blit(image, position)

    def _group(self, surface: pygame.Surface, x: int, label: str, value: str) -> None:
        self._blit_text(surface, self.font, label, (x, 7))
        self._blit_text(surface, self.value_font, value, (x, 28))

    def draw(
        self,
        surface: pygame.Surface,
        lives: int,
        coins: int,
        level: int,
        power: str | None,
        power_time: float,
        fps: float,
    ) -> None:
        # No opaque panel: the level remains visible behind the white labels.
        self._group(surface, 24, "VIDAS", f"  {lives}")

        pygame.draw.ellipse(surface, settings.GOLD, pygame.Rect(205, 28, 13, 18))
        pygame.draw.ellipse(surface, (255, 244, 164), pygame.Rect(205, 28, 13, 18), 2)
        self._blit_text(surface, self.font, f"x{coins:02d}", (225, 28))

        self._group(surface, 350, "MUNDO", f"  1-{level}")
        self._group(surface, 520, "PUNTOS", f"{coins * 100:06d}")

        if power:
            name = "VELOCIDAD" if power == "speed" else "GRAN SALTO"
            self._group(surface, 750, "PODER", f"{name} {power_time:0.1f}")

        self._blit_text(surface, self.small, f"{fps:0.0f} FPS", (surface.get_width() - 75, 9))
