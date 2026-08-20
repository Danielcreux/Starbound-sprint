"""Tile definitions and simple original rendering."""

import pygame
import math
from game import settings

EMPTY = 0
GROUND = 1
BLOCK = 2
PLATFORM = 3
COIN = 4
ENEMY = 5
POWERUP = 6
CHECKPOINT = 7
GOAL = 8
HAZARD = 9

SOLID_TYPES = {GROUND, BLOCK, PLATFORM}


class CoinBlock:
    """Solid block that awards one coin when struck from below."""

    def __init__(
        self,
        rect: pygame.Rect,
        active_image: pygame.Surface | None,
        used_image: pygame.Surface | None = None,
    ) -> None:
        self.rect = rect
        self.active_image = active_image
        self.used_image = used_image
        self.used = False
        self.bump_timer = 0.0

    def hit(self) -> bool:
        self.bump_timer = 0.16
        if self.used:
            return False
        self.used = True
        return True

    def update(self, dt: float) -> None:
        self.bump_timer = max(0.0, self.bump_timer - dt)

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        progress = self.bump_timer / 0.16 if self.bump_timer else 0.0
        bump = round(math.sin(progress * math.pi) * 7)
        draw_rect = self.rect.move(-offset[0], -offset[1] - bump)
        image = self.used_image if self.used and self.used_image else self.active_image
        if image:
            surface.blit(image, image.get_rect(center=draw_rect.center))
        else:
            pygame.draw.rect(surface, (218, 146, 43) if not self.used else (115, 104, 92), draw_rect, border_radius=4)
            pygame.draw.rect(surface, (255, 205, 74), draw_rect, 3, border_radius=4)
        if not self.used:
            font = pygame.font.Font(None, 38)
            symbol = font.render("?", True, (255, 244, 178))
            surface.blit(symbol, symbol.get_rect(center=draw_rect.center))
        elif self.used_image is None:
            shade = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
            shade.fill((45, 42, 50, 115))
            surface.blit(shade, draw_rect)


class RisingCoin:
    """Short visual emitted by a coin block."""

    def __init__(self, center: tuple[int, int], image: pygame.Surface | None) -> None:
        self.x = float(center[0])
        self.y = float(center[1])
        self.velocity_y = -280.0
        self.timer = 0.65
        self.image = image

    def update(self, dt: float) -> None:
        self.timer = max(0.0, self.timer - dt)
        self.velocity_y += 720.0 * dt
        self.y += self.velocity_y * dt

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        center = (round(self.x - offset[0]), round(self.y - offset[1]))
        if self.image:
            surface.blit(self.image, self.image.get_rect(center=center))
        else:
            pygame.draw.ellipse(surface, settings.GOLD, pygame.Rect(center[0] - 10, center[1] - 14, 20, 28))


def draw_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    kind: int,
    image: pygame.Surface | None = None,
) -> None:
    if image is not None:
        image_rect = (
            image.get_rect(topleft=rect.topleft)
            if kind == PLATFORM
            else image.get_rect(bottomleft=rect.bottomleft)
        )
        surface.blit(image, image_rect)
        return
    if kind == GROUND:
        pygame.draw.rect(surface, (73, 116, 70), rect)
        pygame.draw.rect(surface, (107, 172, 82), (rect.x, rect.y, rect.w, 9))
        pygame.draw.line(surface, (55, 84, 61), rect.bottomleft, rect.bottomright, 3)
    elif kind == BLOCK:
        pygame.draw.rect(surface, (113, 95, 115), rect, border_radius=4)
        pygame.draw.rect(surface, (156, 134, 155), rect, 3, border_radius=4)
    elif kind == PLATFORM:
        pygame.draw.rect(surface, (240, 173, 83), rect.inflate(0, -22), border_radius=5)
        pygame.draw.line(surface, settings.WHITE, (rect.left + 5, rect.centery - 10), (rect.right - 5, rect.centery - 10), 3)
    elif kind == HAZARD:
        points = [(rect.left, rect.bottom), (rect.centerx, rect.top + 8), (rect.right, rect.bottom)]
        pygame.draw.polygon(surface, (231, 74, 77), points)
        pygame.draw.polygon(surface, (255, 177, 78), points, 3)
