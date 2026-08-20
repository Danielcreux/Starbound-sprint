import pygame

from entities.player import Player, PlayerInput
from game import settings


def test_player_velocity_respects_terminal_limit():
    player = Player((0, 0))
    for _ in range(240):
        player.update(1 / 60, PlayerInput(), [])
    assert player.velocity.y == settings.TERMINAL_VELOCITY


def test_player_lands_on_floor():
    player = Player((20, 0))
    floor = pygame.Rect(0, 100, 200, 48)
    for _ in range(120):
        player.update(1 / 60, PlayerInput(), [floor])
    assert player.on_ground
    assert player.rect.bottom == floor.top


def test_required_vertical_step_is_reachable():
    theoretical_height = settings.JUMP_SPEED ** 2 / (2 * settings.GRAVITY)
    required_step = 2 * settings.TILE_SIZE
    assert theoretical_height > required_step


def test_configuration_has_sane_limits():
    assert settings.SCREEN_WIDTH / settings.SCREEN_HEIGHT == pytest.approx(16 / 9)
    assert settings.WALK_SPEED < settings.RUN_SPEED
    assert settings.FPS >= 60


def test_powerups_increase_their_respective_ability():
    player = Player((0, 0))
    base_speed = player.max_speed
    base_jump = player.jump_speed
    player.activate_power("speed")
    assert player.max_speed > base_speed
    player.activate_power("jump")
    assert player.jump_speed > base_jump
    assert player.power_timer == settings.POWERUP_DURATION


def test_jump_power_is_a_true_high_jump():
    powered_height = (settings.JUMP_SPEED * settings.JUMP_POWER_MULTIPLIER) ** 2 / (2 * settings.GRAVITY)
    assert powered_height > 6 * settings.TILE_SIZE


def test_player_can_double_jump_but_not_jump_three_times():
    player = Player((20, 50))
    player.on_ground = True

    player.update(1 / 60, PlayerInput(jump_pressed=True, jump_held=True), [])
    assert player.jumps_used == 1
    first_impulse = player.velocity.y

    player.update(1 / 60, PlayerInput(jump_pressed=True, jump_held=True), [])
    assert player.jumps_used == 2
    assert player.jumped_this_frame
    assert player.velocity.y == pytest.approx(first_impulse)

    velocity_before_third_press = player.velocity.y
    player.update(1 / 60, PlayerInput(jump_pressed=True, jump_held=True), [])
    assert player.jumps_used == 2
    assert not player.jumped_this_frame
    assert player.velocity.y > velocity_before_third_press


import pytest
