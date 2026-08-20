"""Runtime representation of one tile-based level."""

import pygame

from entities.coin import Coin
from entities.enemy import ENEMY_TYPES, Enemy
from entities.powerup import PowerUp
from entities.effect import SpriteEffect
from game import settings
from game.assets import AssetManager
from world.level_loader import LevelData
from world import tile
from world.tile import CoinBlock, RisingCoin


class Level:
    def __init__(self, data: LevelData, assets: AssetManager | None = None, level_number: int = 1) -> None:
        self.data = data
        self.width_px = data.width * settings.TILE_SIZE
        self.height_px = data.height * settings.TILE_SIZE
        self.solids: list[pygame.Rect] = []
        self.hazards: list[pygame.Rect] = []
        self.checkpoints: list[pygame.Rect] = []
        self.goals: list[pygame.Rect] = []
        self.coins: list[Coin] = []
        self.powerups: list[PowerUp] = []
        self.enemies: list[Enemy] = []
        self.spawn = (data.spawn[0] * settings.TILE_SIZE + 7, data.spawn[1] * settings.TILE_SIZE)
        self._tiles: list[tuple[pygame.Rect, int]] = []
        self.assets = assets
        self.tile_images: dict[int, pygame.Surface | None] = {}
        self.background: pygame.Surface | None = None
        self._entity_clips: dict[str, dict] = {}
        self._enemy_specs: list[tuple[type[Enemy], int, int, tuple[int, int] | None, dict]] = []
        self._item_images: dict[str, pygame.Surface | None] = {}
        self.coin_blocks: list[CoinBlock] = []
        self.rising_coins: list[RisingCoin] = []
        self.used_block_image: pygame.Surface | None = None
        self.goal_castle: pygame.Surface | None = None
        self.effects: list[SpriteEffect] = []
        self.effect_clips: dict = {}
        self._load_visuals(level_number)
        self._build()

    def _load_visuals(self, level_number: int) -> None:
        if self.assets is None:
            return
        scale = max(1, int(self.assets.manifest.get("pixel_scale", 3)))
        self.tile_images = {
            tile.GROUND: self.assets.load_manifest_image("ground", ["tiles/ground.png", "tiles/ground"], scale),
            tile.BLOCK: self.assets.load_manifest_image("block", ["tiles/blocks.png", "tiles/blocks"], scale),
            tile.PLATFORM: self.assets.load_manifest_image("platform", ["tiles/platforms.png", "tiles/platforms"], scale),
            tile.HAZARD: self.assets.load_manifest_image("hazard", ["tiles/hazards.png", "tiles/hazards"], scale),
        }
        background_scale = max(1, int(self.assets.manifest.get("background_scale", 1)))
        self.background = self.assets.load_manifest_image(
            f"background_{level_number}",
            [f"tiles/backgrounds/level_{level_number}.png", "tiles/backgrounds/default.png", "tiles/backgrounds"],
            background_scale,
        )
        animation_states = {
            "walker": ("walk", "death"),
            "patrol": ("walk", "death"),
            "jumper": ("walk", "jump", "death"),
            "sheller": ("walk", "death"),
            "planter": ("walk", "death"),
        }
        self._entity_clips = {
            kind: self.assets.load_entity_clips(kind, animation_states[kind])
            for kind in ENEMY_TYPES
        }
        self.effect_clips = self.assets.load_entity_clips(
            "effects", ("smoke", "sparkle", "power")
        )
        self._item_images = {
            "coin": self.assets.load_manifest_image("coin", ["sprites/items/coin.png"], scale),
            "speed": self.assets.load_manifest_image("speed", ["sprites/items/speed.png"], scale),
            "jump": self.assets.load_manifest_image("jump", ["sprites/items/jump.png"], scale),
        }
        visuals = self.assets.manifest.get("visuals", {})
        if isinstance(visuals, dict) and "used_block" in visuals:
            self.used_block_image = self.assets.load_manifest_image("used_block", [], scale)
        self.goal_castle = self.assets.load_manifest_image(
            "goal_castle", ["sprites/items/castillo.png"], 1
        )

    def _build(self) -> None:
        enemy_index = power_index = 0
        for row_index, row in enumerate(self.data.layout):
            for column_index, kind in enumerate(row):
                x = column_index * settings.TILE_SIZE
                y = row_index * settings.TILE_SIZE
                rect = pygame.Rect(x, y, settings.TILE_SIZE, settings.TILE_SIZE)
                if kind in tile.SOLID_TYPES:
                    collision_rect = rect.copy()
                    if kind == tile.PLATFORM:
                        collision_rect.height = 18
                    self.solids.append(collision_rect)
                    if kind == tile.BLOCK:
                        self.coin_blocks.append(
                            CoinBlock(collision_rect, self.tile_images.get(tile.BLOCK), self.used_block_image)
                        )
                    else:
                        self._tiles.append((rect, kind))
                elif kind == tile.COIN:
                    self.coins.append(Coin(x, y, self._item_images.get("coin")))
                elif kind == tile.ENEMY:
                    enemy_kind = self.data.enemy_types[enemy_index] if enemy_index < len(self.data.enemy_types) else "walker"
                    enemy_index += 1
                    enemy_class = ENEMY_TYPES.get(enemy_kind, ENEMY_TYPES["walker"])
                    patrol = (x - settings.TILE_SIZE * 2, x + settings.TILE_SIZE * 3) if enemy_kind == "patrol" else None
                    clips = self._entity_clips.get(enemy_kind, {})
                    spec = (enemy_class, x + 5, y + 10, patrol, clips)
                    self._enemy_specs.append(spec)
                    self.enemies.append(enemy_class(x + 5, y + 10, patrol, clips))
                elif kind == tile.POWERUP:
                    power_kind = self.data.powerup_types[power_index] if power_index < len(self.data.powerup_types) else "speed"
                    power_index += 1
                    self.powerups.append(PowerUp(x, y, power_kind, self._item_images.get(power_kind)))
                elif kind == tile.CHECKPOINT:
                    self.checkpoints.append(rect.inflate(-24, 0))
                elif kind == tile.GOAL:
                    self.goals.append(rect)
                elif kind == tile.HAZARD:
                    self.hazards.append(rect.inflate(-8, -4))
                    self._tiles.append((rect, kind))

    def update_enemies(self, dt: float, active_area: pygame.Rect) -> None:
        expanded = active_area.inflate(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        for enemy in self.enemies:
            if (enemy.alive or enemy.death_timer > 0) and expanded.colliderect(enemy.hitbox):
                enemy.update(dt, self.solids)

    def update_effects(self, dt: float) -> None:
        for block in self.coin_blocks:
            block.update(dt)
        for coin in self.rising_coins:
            coin.update(dt)
        self.rising_coins = [coin for coin in self.rising_coins if coin.timer > 0]
        for effect in self.effects:
            effect.update(dt)
        self.effects = [effect for effect in self.effects if effect.alive]

    def spawn_effect(self, kind: str, position: tuple[int, int], duration: float = 0.45) -> None:
        clip = self.effect_clips.get(kind)
        if clip:
            self.effects.append(SpriteEffect(position, clip, duration))

    def reset_enemies(self) -> None:
        """Restore every enemy without resetting coins, blocks or checkpoint state."""
        self.enemies = [
            enemy_class(x, y, patrol, clips)
            for enemy_class, x, y, patrol, clips in self._enemy_specs
        ]

    def hit_coin_block(self, player_hitbox: pygame.Rect) -> bool:
        """Activate the block directly above the player's collision box."""
        for block in self.coin_blocks:
            horizontally_aligned = player_hitbox.right > block.rect.left and player_hitbox.left < block.rect.right
            touching_underside = abs(player_hitbox.top - block.rect.bottom) <= 2
            if horizontally_aligned and touching_underside:
                awarded = block.hit()
                if awarded:
                    self.rising_coins.append(
                        RisingCoin((block.rect.centerx, block.rect.top - 8), self._item_images.get("coin"))
                    )
                    self.spawn_effect("sparkle", (block.rect.centerx, block.rect.top - 8))
                return awarded
        return False

    def draw(self, surface: pygame.Surface, camera_rect: pygame.Rect) -> None:
        offset = camera_rect.topleft
        expanded = camera_rect.inflate(settings.TILE_SIZE * 2, settings.TILE_SIZE * 2)
        for rect, kind in self._tiles:
            if expanded.colliderect(rect):
                tile.draw_tile(
                    surface,
                    rect.move(-offset[0], -offset[1]),
                    kind,
                    self.tile_images.get(kind),
                )
        for block in self.coin_blocks:
            if expanded.colliderect(block.rect):
                block.draw(surface, offset)
        for checkpoint in self.checkpoints:
            if expanded.colliderect(checkpoint):
                base = checkpoint.move(-offset[0], -offset[1])
                pygame.draw.line(surface, settings.INK, base.midbottom, base.midtop, 5)
                pygame.draw.polygon(surface, settings.GOLD, [base.midtop, (base.right + 18, base.y + 10), (base.centerx, base.y + 21)])
        for goal in self.goals:
            if expanded.colliderect(goal):
                base = goal.move(-offset[0], -offset[1])
                if self.goal_castle:
                    castle_rect = self.goal_castle.get_rect(midbottom=base.midbottom)
                    surface.blit(self.goal_castle, castle_rect)
                else:
                    pygame.draw.line(surface, settings.WHITE, base.midbottom, base.midtop, 6)
                    pygame.draw.circle(surface, settings.GOLD, base.midtop, 9)
        for coin in self.coins:
            coin.draw(surface, offset)
        for powerup in self.powerups:
            powerup.draw(surface, offset)
        for enemy in self.enemies:
            enemy.draw(surface, offset)
        for coin in self.rising_coins:
            coin.draw(surface, offset)
        for effect in self.effects:
            effect.draw(surface, offset)
