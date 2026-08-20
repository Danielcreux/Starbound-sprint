"""External asset loading with pixel-perfect scaling and safe fallbacks."""

import json
from pathlib import Path
import re
from typing import Any
import warnings
from collections import deque

import pygame

from game.animation import AnimationClip


IMAGE_EXTENSIONS = (".png", ".bmp", ".gif", ".jpg", ".jpeg", ".webp")
AUDIO_EXTENSIONS = (".wav", ".ogg", ".mp3", ".flac")


def _natural_key(path: Path) -> list[str | int]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


class AssetManager:
    """Loads user-supplied assets without embedding or fetching resources."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.missing: set[str] = set()
        self._reported_missing: set[str] = set()
        self._images: dict[tuple[str, int], pygame.Surface] = {}
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict[str, Any]:
        path = self.root / "manifest.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}

    def resolve(self, relative: str | Path) -> Path:
        return self.root / Path(relative)

    def load_image(self, relative: str | Path, scale: int = 1, required: bool = True) -> pygame.Surface | None:
        """Load one image and resize only with nearest-neighbour scaling."""
        relative_text = Path(relative).as_posix()
        scale = max(1, int(scale))
        cache_key = (relative_text, scale)
        if cache_key in self._images:
            return self._images[cache_key]
        path = self.resolve(relative)
        if not path.is_file():
            if required:
                self.missing.add(relative_text)
            return None
        try:
            image = pygame.image.load(path)
            image = image.convert_alpha() if pygame.display.get_surface() else image.copy()
            if scale != 1:
                image = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))
            self._images[cache_key] = image
            return image
        except pygame.error as exc:
            warnings.warn(f"No se pudo cargar el asset {path}: {exc}", stacklevel=2)
            self.missing.add(relative_text)
            return None

    def load_animation(
        self,
        directory: str | Path,
        state: str,
        scale: int = 1,
        fps: float = 8.0,
        loop: bool = True,
    ) -> AnimationClip | None:
        """Load ``state.png``, ``state_N.png`` or ``state/*.png`` in natural order."""
        folder = self.resolve(directory)
        candidates: list[Path] = []
        exact = folder / f"{state}.png"
        if exact.is_file():
            candidates.append(exact)
        candidates.extend(path for path in folder.glob(f"{state}_*.*") if path.suffix.lower() in IMAGE_EXTENSIONS)
        state_folder = folder / state
        if state_folder.is_dir():
            candidates.extend(path for path in state_folder.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
        candidates = sorted(set(candidates), key=_natural_key)
        frames = tuple(
            image for path in candidates
            if (image := self.load_image(path.relative_to(self.root), scale, required=False)) is not None
        )
        if not frames:
            self.missing.add(f"{Path(directory).as_posix()}/{state}.png o {state}_*.png")
            return None
        return AnimationClip(frames, fps, loop)

    def get_sprite(
        self,
        sheet: pygame.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
        scale: int = 1,
    ) -> pygame.Surface:
        """Cut a frame from a loaded sprite sheet using pixel coordinates."""
        frame = pygame.Surface((width, height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), pygame.Rect(x, y, width, height))
        if scale != 1:
            frame = pygame.transform.scale(frame, (width * scale, height * scale))
        return frame

    @staticmethod
    def _clear_connected_background(
        image: pygame.Surface,
        colors: list[tuple[int, int, int]],
        tolerance: int,
    ) -> pygame.Surface:
        """Remove a solid/checker background reachable from a crop border."""
        result = image.convert_alpha()
        width, height = result.get_size()
        pixels = pygame.PixelArray(result)
        visited: set[tuple[int, int]] = set()
        queue: deque[tuple[int, int]] = deque()
        queue.extend((x, y) for x in range(width) for y in (0, height - 1))
        queue.extend((x, y) for y in range(height) for x in (0, width - 1))

        def is_background(x: int, y: int) -> bool:
            color = result.unmap_rgb(pixels[x, y])
            return any(
                abs(color.r - red) <= tolerance
                and abs(color.g - green) <= tolerance
                and abs(color.b - blue) <= tolerance
                for red, green, blue in colors
            )

        while queue:
            x, y = queue.popleft()
            if (x, y) in visited or not (0 <= x < width and 0 <= y < height):
                continue
            visited.add((x, y))
            if not is_background(x, y):
                continue
            pixels[x, y] = pygame.Color(0, 0, 0, 0)
            queue.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
        del pixels
        return result

    def load_region(
        self,
        relative: str | Path,
        rectangle: tuple[int, int, int, int],
        scale: int = 1,
        background_colors: list[tuple[int, int, int]] | None = None,
        tolerance: int = 8,
        alpha_threshold: int | None = None,
        trim: bool = True,
    ) -> pygame.Surface | None:
        """Crop an arbitrary pixel rectangle and optionally clean its background."""
        sheet = self.load_image(relative, required=True)
        if sheet is None:
            return None
        region = pygame.Rect(rectangle)
        if not sheet.get_rect().contains(region):
            warnings.warn(f"Recorte fuera de límites en {relative}: {rectangle}", stacklevel=2)
            return None
        frame = pygame.Surface(region.size, pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), region)
        if alpha_threshold is not None:
            pixels = pygame.PixelArray(frame)
            for x in range(frame.get_width()):
                for y in range(frame.get_height()):
                    color = frame.unmap_rgb(pixels[x, y])
                    if color.a < alpha_threshold:
                        pixels[x, y] = pygame.Color(0, 0, 0, 0)
            del pixels
        if background_colors:
            frame = self._clear_connected_background(frame, background_colors, tolerance)
        if trim:
            bounds = frame.get_bounding_rect(min_alpha=1)
            if bounds.width and bounds.height:
                frame = frame.subsurface(bounds).copy()
        scale = max(1, int(scale))
        if scale != 1:
            frame = pygame.transform.scale(
                frame,
                (frame.get_width() * scale, frame.get_height() * scale),
            )
        return frame

    def load_spritesheet(
        self,
        relative: str | Path,
        frame_size: tuple[int, int],
        coordinates: list[tuple[int, int]] | None = None,
        scale: int = 1,
    ) -> tuple[pygame.Surface, ...]:
        """Split a sheet by grid coordinates; defaults to every frame row-by-row."""
        sheet = self.load_image(relative, required=True)
        if sheet is None:
            return ()
        width, height = frame_size
        if coordinates is None:
            coordinates = [
                (column, row)
                for row in range(sheet.get_height() // height)
                for column in range(sheet.get_width() // width)
            ]
        return tuple(
            self.get_sprite(sheet, column * width, row * height, width, height, scale)
            for column, row in coordinates
        )

    def load_tileset(
        self,
        relative: str | Path,
        frame_size: tuple[int, int],
        tiles: dict[str, tuple[int, int]],
        scale: int = 1,
    ) -> dict[str, pygame.Surface]:
        """Cut named tiles from one sheet using grid coordinates."""
        sheet = self.load_image(relative, required=True)
        if sheet is None:
            return {}
        width, height = frame_size
        return {
            name: self.get_sprite(sheet, column * width, row * height, width, height, scale)
            for name, (column, row) in tiles.items()
        }

    def load_entity_clips(self, entity_name: str, states: tuple[str, ...]) -> dict[str, AnimationClip]:
        """Load loose frames or configured sprite-sheet regions for an entity."""
        config = self.manifest.get(entity_name, {})
        if not isinstance(config, dict):
            config = {}
        directory = str(config.get("directory", f"sprites/{entity_name}"))
        scale = max(1, int(config.get("scale", self.manifest.get("pixel_scale", 3))))
        fps_config = config.get("fps", {})
        clips: dict[str, AnimationClip] = {}
        region_source = config.get("source")
        regions = config.get("regions", {})
        if region_source and isinstance(regions, dict):
            background_colors = [tuple(int(channel) for channel in color) for color in config.get("background_colors", [])]
            tolerance = int(config.get("background_tolerance", 8))
            alpha_threshold = config.get("alpha_threshold")
            for state in states:
                rectangles = regions.get(state, [])
                frames = tuple(
                    frame
                    for rectangle in rectangles
                    if (frame := self.load_region(
                        str(region_source), tuple(int(value) for value in rectangle), scale,
                        background_colors, tolerance,
                        int(alpha_threshold) if alpha_threshold is not None else None,
                    )) is not None
                )
                if frames:
                    clips[state] = AnimationClip(
                        frames,
                        float(fps_config.get(state, 8)),
                        state != "death",
                    )
        sheet_name = config.get("spritesheet")
        sheet_animations = config.get("animations", {})
        frame_size_raw = config.get("frame_size", [16, 16])
        if sheet_name and isinstance(sheet_animations, dict):
            frame_size = (int(frame_size_raw[0]), int(frame_size_raw[1]))
            for state in states:
                coordinates = sheet_animations.get(state)
                if coordinates:
                    frames = self.load_spritesheet(
                        sheet_name, frame_size,
                        [(int(point[0]), int(point[1])) for point in coordinates], scale,
                    )
                    if frames:
                        clips[state] = AnimationClip(frames, float(fps_config.get(state, 8)), state != "death")
        for state in states:
            if state in clips:
                continue
            clip = self.load_animation(
                directory, state, scale,
                float(fps_config.get(state, 8)), state != "death",
            )
            if clip:
                clips[state] = clip
        if clips and bool(config.get("normalize_frames", True)):
            all_frames = [frame for clip in clips.values() for frame in clip.frames]
            render_size = config.get("render_size")
            global_width = max(frame.get_width() for frame in all_frames)
            global_height = max(frame.get_height() for frame in all_frames)
            normalized: dict[str, AnimationClip] = {}
            for state, clip in clips.items():
                # A fixed render box uses one canvas per animation, so a wide
                # death frame cannot shrink every walking frame.
                canvas_width = (
                    max(frame.get_width() for frame in clip.frames)
                    if render_size else global_width
                )
                canvas_height = (
                    max(frame.get_height() for frame in clip.frames)
                    if render_size else global_height
                )
                frames: list[pygame.Surface] = []
                for frame in clip.frames:
                    canvas = pygame.Surface((canvas_width, canvas_height), pygame.SRCALPHA)
                    canvas.blit(frame, frame.get_rect(midbottom=(canvas_width // 2, canvas_height)))
                    if render_size:
                        ratio = min(
                            int(render_size[0]) / canvas_width,
                            int(render_size[1]) / canvas_height,
                        )
                        canvas = pygame.transform.scale(
                            canvas,
                            (
                                max(1, round(canvas_width * ratio)),
                                max(1, round(canvas_height * ratio)),
                            ),
                        )
                    frames.append(canvas)
                normalized[state] = AnimationClip(tuple(frames), clip.fps, clip.loop)
            clips = normalized
        return clips

    def first_image(self, locations: list[str], scale: int = 1) -> pygame.Surface | None:
        """Return the first direct file or first image inside a candidate directory."""
        for location in locations:
            path = self.resolve(location)
            if path.is_file():
                image = self.load_image(location, scale, required=False)
                if image:
                    return image
            elif path.is_dir():
                files = sorted((item for item in path.iterdir() if item.suffix.lower() in IMAGE_EXTENSIONS), key=_natural_key)
                if files:
                    image = self.load_image(files[0].relative_to(self.root), scale, required=False)
                    if image:
                        return image
        self.missing.add(" | ".join(locations))
        return None

    def load_manifest_image(
        self,
        key: str,
        fallback_locations: list[str],
        default_scale: int = 1,
    ) -> pygame.Surface | None:
        """Load a configured whole image or arbitrary region, then optionally resize."""
        visuals = self.manifest.get("visuals", {})
        config = visuals.get(key, {}) if isinstance(visuals, dict) else {}
        if not isinstance(config, dict) or not config.get("source"):
            return self.first_image(fallback_locations, default_scale)
        source = str(config["source"])
        scale = max(1, int(config.get("scale", default_scale)))
        rectangle = config.get("rect")
        if rectangle:
            image = self.load_region(
                source,
                tuple(int(value) for value in rectangle),
                scale,
                [tuple(int(channel) for channel in color) for color in config.get("background_colors", [])],
                int(config.get("background_tolerance", 8)),
                int(config["alpha_threshold"]) if "alpha_threshold" in config else None,
                bool(config.get("trim", True)),
            )
        else:
            image = self.load_image(source, scale)
        target_size = config.get("target_size")
        if image is not None and target_size:
            image = pygame.transform.scale(image, (int(target_size[0]), int(target_size[1])))
        return image

    def find_audio(self, relative_without_extension: str) -> Path | None:
        for extension in AUDIO_EXTENSIONS:
            path = self.resolve(relative_without_extension + extension)
            if path.is_file():
                return path
        self.missing.add(relative_without_extension + ".[wav|ogg|mp3|flac]")
        return None

    def report_missing(self) -> None:
        new_missing = self.missing - self._reported_missing
        if not new_missing:
            return
        listed = "\n  - ".join(sorted(new_missing))
        warnings.warn(
            "Assets no encontrados; se usarán placeholders temporales:\n  - " + listed,
            stacklevel=2,
        )
        self._reported_missing.update(new_missing)
