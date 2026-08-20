import pygame

from physics.collision import move_and_collide


def test_fast_vertical_body_does_not_tunnel_through_floor():
    rect = pygame.Rect(10, 0, 20, 20)
    position = pygame.Vector2(rect.topleft)
    velocity = pygame.Vector2(0, 2000)
    grounded, _, _ = move_and_collide(rect, position, velocity, 0.1, [pygame.Rect(0, 100, 100, 20)])
    assert grounded
    assert rect.bottom == 100
    assert velocity.y == 0


def test_horizontal_collision_resolves_at_wall_edge():
    rect = pygame.Rect(0, 10, 20, 20)
    position = pygame.Vector2(rect.topleft)
    velocity = pygame.Vector2(1000, 0)
    _, _, hit_wall = move_and_collide(rect, position, velocity, 0.1, [pygame.Rect(70, 0, 20, 100)])
    assert hit_wall
    assert rect.right == 70
