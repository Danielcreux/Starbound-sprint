"""Collectible coin."""

import pygame
from game import settings


class Coin:
    def __init__(self, x: int, y: int, image: pygame.Surface | None = None) -> None:
        self.rect = pygame.Rect(x + 12, y + 10, 24, 28)
        self.collected = False
        self.image = image

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if self.collected:
            return
        if self.image:
            image_rect = self.image.get_rect(center=(self.rect.centerx - offset[0], self.rect.centery - offset[1]))
            surface.blit(self.image, image_rect)
            return
        rect = self.rect.move(-offset[0], -offset[1])
        pygame.draw.ellipse(surface, settings.GOLD, rect)
        pygame.draw.ellipse(surface, (255, 240, 125), rect, 3)
