"""Smooth, bounded side-scrolling camera."""

import pygame


class Camera:
    def __init__(self, viewport_width: int, viewport_height: int) -> None:
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.x = 0.0
        self.y = 0.0
        self.world_width = viewport_width
        self.world_height = viewport_height

    def set_bounds(self, width: int, height: int) -> None:
        self.world_width = max(width, self.viewport_width)
        self.world_height = max(height, self.viewport_height)

    def update(self, target: pygame.Rect, dt: float) -> None:
        desired_x = target.centerx - self.viewport_width * 0.43
        desired_y = target.centery - self.viewport_height * 0.58
        max_x = max(0, self.world_width - self.viewport_width)
        max_y = max(0, self.world_height - self.viewport_height)
        desired_x = max(0.0, min(float(max_x), desired_x))
        desired_y = max(0.0, min(float(max_y), desired_y))
        blend = min(1.0, 6.5 * dt)
        self.x += (desired_x - self.x) * blend
        self.y += (desired_y - self.y) * blend

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(-round(self.x), -round(self.y))

    @property
    def visible_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.viewport_width, self.viewport_height)
