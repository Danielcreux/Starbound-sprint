"""Player movement, powers and damage behaviour."""

from dataclasses import dataclass
from collections.abc import Iterable
import pygame

from game import settings
from game.animation import AnimationClip, Animator
from physics.collision import move_and_collide
from physics.movement import approach


@dataclass(frozen=True)
class PlayerInput:
    left: bool = False
    right: bool = False
    run: bool = False
    jump_pressed: bool = False
    jump_held: bool = False


class Player:
    ANIMATION_STATES = ("idle", "walk", "run", "jump", "fall", "hurt", "death")

    def __init__(
        self,
        spawn: tuple[int, int],
        clips: dict[str, AnimationClip] | None = None,
        hitbox_size: tuple[int, int] = settings.PLAYER_SIZE,
        draw_offset: tuple[int, int] = (0, 0),
        source_facing: str = "right",
    ) -> None:
        self.hitbox = pygame.Rect(spawn, hitbox_size)
        self.rect = self.hitbox.copy()
        self.position = pygame.Vector2(self.hitbox.topleft)
        self.velocity = pygame.Vector2()
        self.spawn = pygame.Vector2(spawn)
        self.checkpoint = pygame.Vector2(spawn)
        self.on_ground = False
        self.facing = 1
        self.coyote_timer = 0.0
        self.jump_buffer = 0.0
        self.jumps_used = 0
        self.jumped_this_frame = False
        self.invulnerability = 0.0
        self.active_power: str | None = None
        self.power_timer = 0.0
        self.animation = "idle"
        self.hit_ceiling = False
        self.animator = Animator(clips or {})
        self.draw_offset = pygame.Vector2(draw_offset)
        self.source_facing = source_facing

    @property
    def max_speed(self) -> float:
        multiplier = settings.SPEED_POWER_MULTIPLIER if self.active_power == "speed" else 1.0
        return settings.RUN_SPEED * multiplier

    @property
    def jump_speed(self) -> float:
        multiplier = settings.JUMP_POWER_MULTIPLIER if self.active_power == "jump" else 1.0
        return settings.JUMP_SPEED * multiplier

    def update(self, dt: float, controls: PlayerInput, solids: Iterable[pygame.Rect]) -> None:
        self.jumped_this_frame = False
        self.invulnerability = max(0.0, self.invulnerability - dt)
        self.power_timer = max(0.0, self.power_timer - dt)
        if self.power_timer == 0.0:
            self.active_power = None

        direction = int(controls.right) - int(controls.left)
        if direction:
            self.facing = direction
        normal_limit = settings.RUN_SPEED if controls.run else settings.WALK_SPEED
        speed_limit = (
            self.max_speed
            if controls.run
            else normal_limit
            * (settings.SPEED_POWER_MULTIPLIER if self.active_power == "speed" else 1.0)
        )
        acceleration = settings.WALK_ACCELERATION if self.on_ground else settings.AIR_ACCELERATION
        if self.active_power == "speed":
            acceleration *= 1.2
        if direction:
            self.velocity.x = approach(self.velocity.x, direction * speed_limit, acceleration * dt)
        else:
            friction = settings.GROUND_FRICTION if self.on_ground else settings.AIR_FRICTION
            self.velocity.x = approach(self.velocity.x, 0.0, friction * dt)

        if self.on_ground:
            self.jumps_used = 0
        self.coyote_timer = settings.COYOTE_TIME if self.on_ground else max(0.0, self.coyote_timer - dt)
        self.jump_buffer = settings.JUMP_BUFFER_TIME if controls.jump_pressed else max(0.0, self.jump_buffer - dt)
        if self.jump_buffer > 0.0 and self.coyote_timer > 0.0:
            self.velocity.y = -self.jump_speed
            self.jump_buffer = 0.0
            self.coyote_timer = 0.0
            self.on_ground = False
            self.jumps_used = 1
            self.jumped_this_frame = True
        elif controls.jump_pressed and not self.on_ground and self.jumps_used < settings.MAX_JUMPS:
            self.velocity.y = -self.jump_speed
            self.jump_buffer = 0.0
            self.coyote_timer = 0.0
            self.jumps_used += 1
            self.jumped_this_frame = True
        if not controls.jump_held and self.velocity.y < -180.0:
            self.velocity.y *= settings.JUMP_CUT_MULTIPLIER

        self.velocity.y = min(settings.TERMINAL_VELOCITY, self.velocity.y + settings.GRAVITY * dt)
        self.on_ground, self.hit_ceiling, _ = move_and_collide(
            self.hitbox, self.position, self.velocity, dt, solids
        )
        if self.on_ground:
            self.jumps_used = 0
        self._choose_animation(controls.run)
        self.animator.set_state(self.animation)
        self.animator.update(dt)
        self._sync_visual_rect()

    def _sync_visual_rect(self) -> None:
        frame = self.animator.frame
        if frame:
            self.rect = frame.get_rect(
                midbottom=(self.hitbox.centerx + round(self.draw_offset.x), self.hitbox.bottom + round(self.draw_offset.y))
            )
        else:
            self.rect = self.hitbox.copy()

    def _choose_animation(self, running: bool) -> None:
        if self.invulnerability > 0.82:
            self.animation = "hurt"
        elif not self.on_ground:
            self.animation = "jump" if self.velocity.y < 0 else "fall"
        elif abs(self.velocity.x) > settings.WALK_SPEED * 0.8 and running:
            self.animation = "run"
        elif abs(self.velocity.x) > 20:
            self.animation = "walk"
        else:
            self.animation = "idle"

    def activate_power(self, kind: str) -> None:
        self.active_power = kind
        self.power_timer = settings.POWERUP_DURATION

    def take_damage(self) -> bool:
        if self.invulnerability > 0.0:
            return False
        self.invulnerability = settings.INVULNERABILITY_TIME
        self.velocity.y = -360.0
        self.velocity.x = -self.facing * 260.0
        return True

    def respawn(self) -> None:
        self.position.update(self.checkpoint)
        self.hitbox.topleft = round(self.position.x), round(self.position.y)
        self._sync_visual_rect()
        self.velocity.update(0, 0)
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jump_buffer = 0.0
        self.jumps_used = 0
        self.jumped_this_frame = False
        self.invulnerability = settings.INVULNERABILITY_TIME

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int]) -> None:
        if self.invulnerability > 0 and int(self.invulnerability * 12) % 2 == 0:
            return
        frame = self.animator.frame
        if frame:
            should_flip = (
                self.facing > 0 if self.source_facing == "left" else self.facing < 0
            )
            image = pygame.transform.flip(frame, True, False) if should_flip else frame
            draw_rect = image.get_rect(
                midbottom=(
                    self.hitbox.centerx - camera_offset[0] + round(self.draw_offset.x),
                    self.hitbox.bottom - camera_offset[1] + round(self.draw_offset.y),
                )
            )
            if self.active_power:
                aura_color = (55, 235, 222) if self.active_power == "speed" else (255, 128, 205)
                aura = pygame.Surface(draw_rect.inflate(14, 10).size, pygame.SRCALPHA)
                pygame.draw.ellipse(aura, (*aura_color, 95), aura.get_rect(), 3)
                surface.blit(aura, aura.get_rect(center=draw_rect.center))
            surface.blit(image, draw_rect)
            return
        draw_rect = self.hitbox.move(-camera_offset[0], -camera_offset[1])
        color = (64, 93, 196) if self.active_power != "speed" else (45, 210, 205)
        pygame.draw.rect(surface, color, draw_rect, border_radius=8)
        visor = pygame.Rect(draw_rect.x + (19 if self.facing > 0 else 5), draw_rect.y + 8, 10, 9)
        pygame.draw.rect(surface, settings.WHITE, visor, border_radius=3)
        pygame.draw.rect(surface, settings.INK, visor.inflate(-5, -4), border_radius=2)
