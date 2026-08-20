"""Delta-time animation primitives independent of the game frame rate."""

from dataclasses import dataclass
import pygame


@dataclass(frozen=True)
class AnimationClip:
    frames: tuple[pygame.Surface, ...]
    fps: float = 8.0
    loop: bool = True


class Animator:
    """Selects frames using elapsed seconds rather than rendered frames."""

    def __init__(self, clips: dict[str, AnimationClip]) -> None:
        self.clips = clips
        self.state = next(iter(clips), "")
        self.elapsed = 0.0
        self.finished = False

    def set_state(self, state: str) -> None:
        if state == self.state or state not in self.clips:
            return
        self.state = state
        self.elapsed = 0.0
        self.finished = False

    def update(self, dt: float) -> None:
        clip = self.clips.get(self.state)
        if not clip or len(clip.frames) <= 1:
            return
        self.elapsed += max(0.0, dt)
        duration = len(clip.frames) / max(0.01, clip.fps)
        if clip.loop:
            self.elapsed %= duration
        elif self.elapsed >= duration:
            self.elapsed = duration
            self.finished = True

    @property
    def frame(self) -> pygame.Surface | None:
        clip = self.clips.get(self.state)
        if not clip or not clip.frames:
            return None
        index = min(len(clip.frames) - 1, int(self.elapsed * clip.fps))
        return clip.frames[index]
