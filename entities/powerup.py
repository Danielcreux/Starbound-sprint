"""Temporary speed and jump upgrades."""

import pygame


class PowerUp:
    def __init__(self, x: int, y: int, kind: str, image: pygame.Surface | None = None) -> None:
        self.kind = kind
        self.rect = pygame.Rect(x + 8, y + 8, 32, 32)
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
        color = (45, 210, 205) if self.kind == "speed" else (244, 121, 188)
        pygame.draw.polygon(surface, color, [rect.midtop, rect.midright, rect.midbottom, rect.midleft])
        pygame.draw.polygon(surface, (255, 255, 255), [rect.midtop, rect.midright, rect.midbottom, rect.midleft], 3)
