import pygame

from entities.player import Player, PlayerInput
from entities.effect import SpriteEffect
from game.animation import AnimationClip, Animator
from game.assets import AssetManager
from world.tile import CoinBlock


def test_image_loading_uses_integer_nearest_scaling(tmp_path):
    pygame.init()
    source = pygame.Surface((2, 3), pygame.SRCALPHA)
    source.fill((255, 0, 0, 255))
    pygame.image.save(source, tmp_path / "frame.png")
    image = AssetManager(tmp_path).load_image("frame.png", scale=4)
    assert image is not None
    assert image.get_size() == (8, 12)


def test_spritesheet_is_cut_by_grid_coordinates(tmp_path):
    pygame.init()
    sheet = pygame.Surface((32, 16), pygame.SRCALPHA)
    pygame.draw.rect(sheet, "red", (0, 0, 16, 16))
    pygame.draw.rect(sheet, "blue", (16, 0, 16, 16))
    pygame.image.save(sheet, tmp_path / "sheet.png")
    frames = AssetManager(tmp_path).load_spritesheet("sheet.png", (16, 16), [(0, 0), (1, 0)], 2)
    assert len(frames) == 2
    assert frames[0].get_size() == (32, 32)
    assert frames[1].get_at((10, 10))[:3] == pygame.Color("blue")[:3]


def test_animator_uses_elapsed_time():
    frames = tuple(pygame.Surface((4, 4)) for _ in range(3))
    animator = Animator({"walk": AnimationClip(frames, fps=10)})
    animator.update(0.21)
    assert animator.frame is frames[2]


def test_visual_sprite_does_not_change_player_hitbox():
    large_frame = pygame.Surface((96, 96), pygame.SRCALPHA)
    player = Player((10, 10), {"idle": AnimationClip((large_frame,))})
    player.update(0.0, PlayerInput(), [])
    assert player.rect.size == (96, 96)
    assert player.hitbox.size == (34, 44)


def test_coin_block_awards_only_once():
    block = CoinBlock(pygame.Rect(48, 48, 48, 48), None)
    assert block.hit()
    assert block.used
    assert not block.hit()


def test_player_flips_according_to_configured_source_direction():
    frame = pygame.Surface((4, 2), pygame.SRCALPHA)
    frame.fill("red", (0, 0, 2, 2))
    frame.fill("blue", (2, 0, 2, 2))
    player = Player((4, 4), {"idle": AnimationClip((frame,))}, source_facing="left")
    player.hitbox.midbottom = (10, 10)
    player._sync_visual_rect()
    left_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
    right_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
    player.facing = -1
    player.draw(left_surface, (0, 0))
    player.facing = 1
    player.draw(right_surface, (0, 0))
    assert left_surface.get_at((8, 8))[:3] == pygame.Color("red")[:3]
    assert right_surface.get_at((8, 8))[:3] == pygame.Color("blue")[:3]


def test_sprite_effect_expires_using_delta_time():
    effect = SpriteEffect((10, 10), AnimationClip((pygame.Surface((4, 4)),), fps=8), 0.4)
    effect.update(0.25)
    assert effect.alive
    effect.update(0.20)
    assert not effect.alive
