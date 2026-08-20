"""Short-lived visual effects loaded from user-supplied sprite sheets."""

import pygame

from game.animation import AnimationClip, Animator


class SpriteEffect:
    def __init__(
        self,
        position: tuple[int, int],
        clip: AnimationClip,
        duration: float = 0.45,
    ) -> None:
        self.position = position
        self.duration = duration
        self.remaining = duration
        self.animator = Animator({"active": AnimationClip(clip.frames, clip.fps, True)})

    @property
    def alive(self) -> bool:
        return self.remaining > 0

    def update(self, dt: float) -> None:
        self.remaining = max(0.0, self.remaining - dt)
        self.animator.update(dt)

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        frame = self.animator.frame
        if frame is None:
            return
        alpha = min(255, round(255 * self.remaining / min(0.18, self.duration)))
        image = frame.copy()
        image.set_alpha(alpha)
        rect = image.get_rect(
            center=(self.position[0] - offset[0], self.position[1] - offset[1])
        )
        surface.blit(image, rect)
