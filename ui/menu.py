"""Keyboard-driven menu rendering."""

from collections.abc import Sequence
import pygame
from game import settings


class Menu:
    def __init__(self) -> None:
        self.selected = 0

    def move(self, amount: int, item_count: int) -> None:
        self.selected = (self.selected + amount) % item_count

    @staticmethod
    def _draw_pixel_background(surface: pygame.Surface, background: pygame.Surface) -> None:
        """Center an image at the largest whole-number scale that fits the screen."""
        if background.get_width() > surface.get_width() or background.get_height() > surface.get_height():
            ratio = min(
                surface.get_width() / background.get_width(),
                surface.get_height() / background.get_height(),
            )
            size = round(background.get_width() * ratio), round(background.get_height() * ratio)
        else:
            scale = max(
                1,
                min(
                    surface.get_width() // background.get_width(),
                    surface.get_height() // background.get_height(),
                ),
            )
            size = background.get_width() * scale, background.get_height() * scale
        scaled = pygame.transform.scale(background, size)
        fill_color = background.get_at((0, 0))[:3]
        surface.fill(fill_color)
        surface.blit(scaled, scaled.get_rect(center=surface.get_rect().center))

    def draw(
        self,
        surface: pygame.Surface,
        title: str,
        items: Sequence[str],
        subtitle: str = "",
        background: pygame.Surface | None = None,
        background_layout: str = "main",
        background_decoration: pygame.Surface | None = None,
    ) -> None:
        if background:
            self._draw_pixel_background(surface, background)
            if background_layout == "pause":
                self._draw_pause_background_menu(surface, title, items, background_decoration)
            elif background_layout == "game_over":
                self._draw_game_over_background_menu(surface, title, items, subtitle)
            else:
                self._draw_background_menu(surface, items, subtitle)
            return
        surface.fill((38, 52, 91))
        font_title = pygame.font.Font(None, 82)
        font_item = pygame.font.Font(None, 42)
        title_image = font_title.render(title, True, settings.GOLD)
        surface.blit(title_image, title_image.get_rect(center=(surface.get_width() // 2, 145)))
        if subtitle:
            small = pygame.font.Font(None, 27).render(subtitle, True, (180, 198, 228))
            surface.blit(small, small.get_rect(center=(surface.get_width() // 2, 205)))
        start_y = 285
        for index, label in enumerate(items):
            active = index == self.selected
            color = settings.WHITE if active else (159, 174, 205)
            image = font_item.render((">  " if active else "   ") + label, True, color)
            surface.blit(image, image.get_rect(center=(surface.get_width() // 2, start_y + index * 65)))

    def _draw_background_menu(
        self,
        surface: pygame.Surface,
        items: Sequence[str],
        subtitle: str,
    ) -> None:
        """Place functional choices over the option area baked into the supplied art."""
        panel = pygame.Surface((560, 250), pygame.SRCALPHA)
        background_color = surface.get_at((surface.get_width() // 2, 365))[:3]
        panel.fill((*background_color, 255))
        pygame.draw.rect(panel, (247, 220, 191), panel.get_rect(), 4)
        surface.blit(panel, panel.get_rect(center=(surface.get_width() // 2, 500)))

        font = pygame.font.Font(None, 34)
        start_y = 410
        for index, label in enumerate(items):
            active = index == self.selected
            color = (255, 242, 209) if active else (247, 247, 247)
            prefix = "> " if active else "  "
            image = font.render(prefix + label, False, color)
            surface.blit(image, image.get_rect(center=(surface.get_width() // 2, start_y + index * 46)))
        if subtitle:
            small = pygame.font.Font(None, 23).render(subtitle, False, (255, 238, 201))
            surface.blit(small, small.get_rect(center=(surface.get_width() // 2, 612)))

    def _draw_pause_background_menu(
        self,
        surface: pygame.Surface,
        title: str,
        items: Sequence[str],
        decoration: pygame.Surface | None,
    ) -> None:
        """Keep the castle visible while presenting the live pause actions."""
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((10, 17, 38, 70))
        surface.blit(shade, (0, 0))
        panel_height = max(250, 150 + len(items) * 48)
        panel = pygame.Surface((760, panel_height), pygame.SRCALPHA)
        panel.fill((16, 27, 55, 218))
        pygame.draw.rect(panel, (255, 224, 176), panel.get_rect(), 4)
        panel_rect = panel.get_rect(center=(500, 155 + panel_height // 2))
        surface.blit(panel, panel_rect)

        if decoration:
            surface.blit(decoration, decoration.get_rect(center=(275, 245)))

        title_image = pygame.font.Font(None, 58).render(title, False, (255, 234, 199))
        surface.blit(title_image, title_image.get_rect(center=(610, 165)))
        font = pygame.font.Font(None, 34)
        for index, label in enumerate(items):
            active = index == self.selected
            color = settings.GOLD if active else settings.WHITE
            image = font.render(("> " if active else "  ") + label, False, color)
            surface.blit(image, image.get_rect(center=(610, 220 + index * 48)))

    def _draw_game_over_background_menu(
        self,
        surface: pygame.Surface,
        title: str,
        items: Sequence[str],
        subtitle: str,
    ) -> None:
        panel = pygame.Surface((600, 270), pygame.SRCALPHA)
        background_color = surface.get_at((surface.get_width() // 2, 365))[:3]
        panel.fill((*background_color, 250))
        pygame.draw.rect(panel, (255, 224, 176), panel.get_rect(), 4)
        surface.blit(panel, panel.get_rect(center=(surface.get_width() // 2, 500)))
        title_image = pygame.font.Font(None, 58).render(title, False, settings.RED)
        surface.blit(title_image, title_image.get_rect(center=(surface.get_width() // 2, 405)))
        font = pygame.font.Font(None, 34)
        for index, label in enumerate(items):
            active = index == self.selected
            color = settings.GOLD if active else settings.WHITE
            image = font.render(("> " if active else "  ") + label, False, color)
            surface.blit(image, image.get_rect(center=(surface.get_width() // 2, 470 + index * 52)))
        if subtitle:
            image = pygame.font.Font(None, 22).render(subtitle, False, (255, 238, 201))
            surface.blit(image, image.get_rect(center=(surface.get_width() // 2, 585)))


def draw_panel(
    surface: pygame.Surface,
    title: str,
    lines: Sequence[str],
    footer: str,
    background: pygame.Surface | None = None,
) -> None:
    if background:
        Menu._draw_pixel_background(surface, background)
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((10, 17, 38, 82))
        surface.blit(shade, (0, 0))
        panel = pygame.Surface((860, 440), pygame.SRCALPHA)
        panel.fill((16, 27, 55, 220))
        pygame.draw.rect(panel, (255, 224, 176), panel.get_rect(), 4)
        surface.blit(panel, panel.get_rect(center=surface.get_rect().center))
    else:
        surface.fill((38, 52, 91))
    title_font = pygame.font.Font(None, 70)
    body_font = pygame.font.Font(None, 34)
    title_image = title_font.render(title, True, settings.GOLD)
    surface.blit(title_image, title_image.get_rect(center=(surface.get_width() // 2, 110)))
    for index, line in enumerate(lines):
        image = body_font.render(line, True, settings.WHITE)
        surface.blit(image, image.get_rect(center=(surface.get_width() // 2, 220 + index * 48)))
    foot = pygame.font.Font(None, 27).render(footer, True, (174, 194, 225))
    surface.blit(foot, foot.get_rect(center=(surface.get_width() // 2, surface.get_height() - 70)))
