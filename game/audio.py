"""Tiny synthesized sound bank; no copyrighted audio files required."""

from array import array
import math
import pygame
from game.assets import AssetManager


class AudioManager:
    def __init__(self, assets: AssetManager | None = None) -> None:
        self.available = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music: dict[str, pygame.mixer.Sound] = {}
        self.music_channel: pygame.mixer.Channel | None = None
        self.current_music: str | None = None
        self.music_paths: dict[str, str] = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.available = True
            notes = {
                "jump": (520, 0.10), "coin": (880, 0.09), "hurt": (150, 0.18),
                "stomp": (240, 0.10), "powerup": (660, 0.25), "death": (100, 0.35),
                "complete": (990, 0.35), "checkpoint": (740, 0.16),
            }
            self.sounds = {name: self._tone(*spec) for name, spec in notes.items()}
            if assets:
                for name in notes:
                    external = assets.find_audio(f"sounds/{name}")
                    if external:
                        try:
                            self.sounds[name] = pygame.mixer.Sound(external)
                        except pygame.error:
                            pass
            self.music = {
                "menu": self._tone(196, 1.8, 900),
                "level": self._tone(247, 1.35, 700),
            }
            self.music_channel = pygame.mixer.Channel(0)
            if assets:
                for name in ("menu", "level"):
                    external = assets.find_audio(f"music/{name}")
                    if external:
                        self.music_paths[name] = str(external)
        except pygame.error:
            self.available = False

    @staticmethod
    def _tone(frequency: float, duration: float, amplitude: int = 7000) -> pygame.mixer.Sound:
        sample_rate = 22050
        count = int(sample_rate * duration)
        samples = array("h")
        for index in range(count):
            envelope = 1.0 - index / count
            # A quiet overtone makes the placeholder less sterile while remaining original.
            wave = math.sin(2 * math.pi * frequency * index / sample_rate)
            wave += 0.22 * math.sin(4 * math.pi * frequency * index / sample_rate)
            value = int(amplitude * envelope * wave)
            samples.append(value)
        return pygame.mixer.Sound(buffer=samples)

    def play(self, name: str) -> None:
        if self.available and name in self.sounds:
            self.sounds[name].play()

    def play_music(self, name: str) -> None:
        if not self.available or self.music_channel is None or name == self.current_music:
            return
        external = self.music_paths.get(name)
        if external:
            try:
                pygame.mixer.music.fadeout(250)
                pygame.mixer.music.load(external)
                pygame.mixer.music.play(loops=-1, fade_ms=350)
                self.music_channel.stop()
                self.current_music = name
                return
            except pygame.error:
                pass
        pygame.mixer.music.fadeout(250)
        self.music_channel.fadeout(250)
        self.music_channel.play(self.music[name], loops=-1, fade_ms=350)
        self.current_music = name
