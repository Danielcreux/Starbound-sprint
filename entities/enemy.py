"""Enemy family with shared collision and defeat behaviour."""

from collections.abc import Iterable
import pygame

from game import settings
from game.animation import AnimationClip, Animator
from physics.collision import move_and_collide


class Enemy:
    color = (210, 77, 92)
    ANIMATION_STATES = ("walk", "jump", "death")

    def __init__(
        self,
        x: int,
        y: int,
        patrol: tuple[int, int] | None = None,
        clips: dict[str, AnimationClip] | None = None,
    ) -> None:
        self.hitbox = pygame.Rect(x, y, 38, 36)
        self.rect = self.hitbox.copy()
        self.position = pygame.Vector2(self.hitbox.topleft)
        self.velocity = pygame.Vector2(-105, 0)
        self.patrol = patrol
        self.alive = True
        self.on_ground = False
        self.animation = "walk"
        self.animator = Animator(clips or {})
        self.death_timer = 0.0

    def update(self, dt: float, solids: Iterable[pygame.Rect]) -> None:
        if not self.alive:
            self.death_timer = max(0.0, self.death_timer - dt)
            self.animator.update(dt)
            return
        self.velocity.y = min(settings.TERMINAL_VELOCITY, self.velocity.y + settings.GRAVITY * dt)
        self.on_ground, _, hit_wall = move_and_collide(self.hitbox, self.position, self.velocity, dt, solids)
        if hit_wall:
            self.velocity.x *= -1
        if self.patrol:
            left, right = self.patrol
            if self.hitbox.left <= left:
                self.velocity.x = abs(self.velocity.x)
            elif self.hitbox.right >= right:
                self.velocity.x = -abs(self.velocity.x)
        self.animation = "jump" if not self.on_ground else "walk"
        self.animator.set_state(self.animation)
        self.animator.update(dt)
        frame = self.animator.frame
        self.rect = frame.get_rect(midbottom=self.hitbox.midbottom) if frame else self.hitbox.copy()

    def take_damage(self) -> None:
        self.animation = "death"
        self.animator.set_state("death")
        self.death_timer = 0.35
        self.alive = False

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if not self.alive and self.death_timer <= 0:
            return
        frame = self.animator.frame
        if frame:
            image = pygame.transform.flip(frame, self.velocity.x < 0, False)
            rect = image.get_rect(midbottom=(self.hitbox.centerx - offset[0], self.hitbox.bottom - offset[1]))
            surface.blit(image, rect)
            return
        rect = self.hitbox.move(-offset[0], -offset[1])
        pygame.draw.rect(surface, self.color, rect, border_radius=10)
        pygame.draw.circle(surface, settings.WHITE, (rect.x + 11, rect.y + 12), 4)
        pygame.draw.circle(surface, settings.WHITE, (rect.x + 27, rect.y + 12), 4)


class WalkerEnemy(Enemy):
    """Turns around at solid walls."""


class PatrolEnemy(Enemy):
    color = (126, 78, 176)


class JumperEnemy(Enemy):
    color = (238, 126, 54)

    def __init__(
        self,
        x: int,
        y: int,
        patrol: tuple[int, int] | None = None,
        clips: dict[str, AnimationClip] | None = None,
    ) -> None:
        super().__init__(x, y, patrol, clips)
        self.velocity.x = 0
        self.jump_timer = 1.4

    def update(self, dt: float, solids: Iterable[pygame.Rect]) -> None:
        self.jump_timer -= dt
        if self.on_ground and self.jump_timer <= 0:
            self.velocity.y = -570
            self.jump_timer = 1.65
        super().update(dt, solids)


class ShellerEnemy(Enemy):
    """A quicker ground enemy used in later levels."""

    color = (77, 174, 67)

    def __init__(
        self,
        x: int,
        y: int,
        patrol: tuple[int, int] | None = None,
        clips: dict[str, AnimationClip] | None = None,
    ) -> None:
        super().__init__(x, y, patrol, clips)
        self.velocity.x = -145


class PlanterEnemy(Enemy):
    """Stationary obstacle that guards platforms and narrow paths."""

    color = (62, 180, 74)

    def update(self, dt: float, solids: Iterable[pygame.Rect]) -> None:
        self.velocity.x = 0
        super().update(dt, solids)
        self.velocity.x = 0


ENEMY_TYPES = {
    "walker": WalkerEnemy,
    "patrol": PatrolEnemy,
    "jumper": JumperEnemy,
    "sheller": ShellerEnemy,
    "planter": PlanterEnemy,
}
