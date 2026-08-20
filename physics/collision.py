"""Axis-separated collision resolution."""

from collections.abc import Iterable
import pygame


def nearby_rects(rect: pygame.Rect, solids: Iterable[pygame.Rect]) -> list[pygame.Rect]:
    return [solid for solid in solids if rect.colliderect(solid)]


def move_and_collide(
    rect: pygame.Rect,
    position: pygame.Vector2,
    velocity: pygame.Vector2,
    dt: float,
    solids: Iterable[pygame.Rect],
) -> tuple[bool, bool, bool]:
    """Move one body, returning grounded, hit-ceiling and hit-wall flags.

    Movement is sub-stepped so fast bodies cannot tunnel through a tile.
    """
    grounded = hit_ceiling = hit_wall = False
    max_motion = max(abs(velocity.x * dt), abs(velocity.y * dt))
    steps = max(1, int(max_motion / max(1, min(rect.width, rect.height) * 0.45)) + 1)
    step_dt = dt / steps
    solid_list = list(solids)

    for _ in range(steps):
        position.x += velocity.x * step_dt
        rect.x = round(position.x)
        for solid in nearby_rects(rect, solid_list):
            if velocity.x > 0:
                rect.right = solid.left
            elif velocity.x < 0:
                rect.left = solid.right
            position.x = float(rect.x)
            velocity.x = 0.0
            hit_wall = True

        position.y += velocity.y * step_dt
        rect.y = round(position.y)
        for solid in nearby_rects(rect, solid_list):
            if velocity.y > 0:
                rect.bottom = solid.top
                grounded = True
            elif velocity.y < 0:
                rect.top = solid.bottom
                hit_ceiling = True
            position.y = float(rect.y)
            velocity.y = 0.0

    return grounded, hit_ceiling, hit_wall
