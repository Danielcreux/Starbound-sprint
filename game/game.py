"""Application controller and state-driven game loop."""

import pygame

from entities.player import Player, PlayerInput
from game import settings
from game.audio import AudioManager
from game.assets import AssetManager
from game.camera import Camera
from game.progress import ProgressStore
from game.state_manager import GameState
from ui.game_over import GAME_OVER_OPTIONS, PAUSE_OPTIONS
from ui.hud import HUD
from ui.menu import Menu, draw_panel
from world.level import Level
from world.level_loader import LevelFormatError, load_level


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.TITLE)
        self.window = pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.RESIZABLE
        )
        self.canvas = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.assets = AssetManager(settings.ASSETS_DIR)
        self.audio = AudioManager(self.assets)
        self.menu_background = self.assets.load_manifest_image(
            "menu_background", ["tiles/backgrounds/menu.png"], 1
        )
        self.pause_background = self.assets.load_manifest_image(
            "pause_background", ["tiles/backgrounds/pausa.jpg"], 1
        )
        self.hud = HUD()
        self.menu = Menu()
        self.camera = Camera(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        self.progress_store = ProgressStore(settings.SAVE_PATH)
        self.progress = self.progress_store.load()
        self.state = GameState.MENU
        self.running = True
        self.current_level_number = 1
        self.level: Level | None = None
        self.player: Player | None = None
        self.lives = settings.STARTING_LIVES
        self.session_coins = 0
        self.banner_timer = 0.0
        self.error_message = ""
        self.audio.play_music("menu")

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(settings.FPS) / 1000.0, 0.05)
            events = pygame.event.get()
            self._handle_events(events)
            if self.state == GameState.PLAYING:
                self._update_playing(dt, events)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    self._menu_key(event.key)
                elif self.state == GameState.LEVEL_SELECT:
                    self._level_select_key(event.key)
                elif self.state == GameState.CONTROLS:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        self.state = GameState.MENU
                        self.audio.play_music("menu")
                elif self.state == GameState.PLAYING and event.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSED
                    self.menu.selected = 0
                elif self.state == GameState.PAUSED:
                    self._pause_key(event.key)
                elif self.state == GameState.GAME_OVER:
                    self._game_over_key(event.key)
                elif self.state in (GameState.LEVEL_COMPLETE, GameState.VICTORY):
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                        self._continue_after_level()

    @staticmethod
    def _navigation(key: int) -> int:
        if key in (pygame.K_UP, pygame.K_w):
            return -1
        if key in (pygame.K_DOWN, pygame.K_s):
            return 1
        return 0

    def _menu_key(self, key: int) -> None:
        options = ("JUGAR", "SELECCIONAR NIVEL", "CONTROLES", "SALIR")
        movement = self._navigation(key)
        if movement:
            self.menu.move(movement, len(options))
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu.selected == 0:
                self._new_game(1)
            elif self.menu.selected == 1:
                self.state = GameState.LEVEL_SELECT
                self.menu.selected = 0
            elif self.menu.selected == 2:
                self.state = GameState.CONTROLS
            else:
                self.running = False

    def _level_select_key(self, key: int) -> None:
        movement = self._navigation(key)
        if movement:
            self.menu.move(movement, 5)
        elif key == pygame.K_ESCAPE:
            self.state = GameState.MENU
            self.menu.selected = 0
            self.audio.play_music("menu")
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu.selected == 4:
                self.state = GameState.MENU
                self.menu.selected = 0
                self.audio.play_music("menu")
            elif self.menu.selected + 1 <= self.progress["highest_level_unlocked"]:
                self._new_game(self.menu.selected + 1)

    def _pause_key(self, key: int) -> None:
        movement = self._navigation(key)
        if movement:
            self.menu.move(movement, len(PAUSE_OPTIONS))
        elif key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu.selected == 0:
                self.state = GameState.PLAYING
            elif self.menu.selected == 1:
                self._load_level(self.current_level_number)
            else:
                self.state = GameState.MENU
                self.menu.selected = 0
                self.audio.play_music("menu")

    def _game_over_key(self, key: int) -> None:
        movement = self._navigation(key)
        if movement:
            self.menu.move(movement, len(GAME_OVER_OPTIONS))
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu.selected == 0:
                self.lives = settings.STARTING_LIVES
                self._load_level(self.current_level_number)
            else:
                self.state = GameState.MENU
                self.menu.selected = 0
                self.audio.play_music("menu")

    def _new_game(self, level_number: int) -> None:
        self.lives = settings.STARTING_LIVES
        self.session_coins = 0
        self._load_level(level_number)

    def _load_level(self, number: int) -> None:
        try:
            data = load_level(settings.LEVELS_DIR / f"level_{number}.json")
            self.level = Level(data, self.assets, number)
            player_config = self.assets.manifest.get("player", {})
            if not isinstance(player_config, dict):
                player_config = {}
            hitbox_raw = player_config.get("hitbox", list(settings.PLAYER_SIZE))
            offset_raw = player_config.get("draw_offset", [0, 0])
            hitbox_size = (int(hitbox_raw[0]), int(hitbox_raw[1]))
            draw_offset = (int(offset_raw[0]), int(offset_raw[1]))
            source_facing = str(player_config.get("source_facing", "right"))
            player_clips = self.assets.load_entity_clips("player", Player.ANIMATION_STATES)
            self.player = Player(
                self.level.spawn,
                player_clips,
                hitbox_size,
                draw_offset,
                source_facing,
            )
            self.current_level_number = number
            self.camera.x = self.camera.y = 0
            self.camera.set_bounds(self.level.width_px, self.level.height_px)
            self.banner_timer = 3.5
            self.error_message = ""
            self.state = GameState.PLAYING
            self.audio.play_music("level")
            self.assets.report_missing()
        except LevelFormatError as exc:
            self.error_message = str(exc)
            self.state = GameState.MENU
            self.audio.play_music("menu")

    def _controls_from_keyboard(self, events: list[pygame.event.Event]) -> PlayerInput:
        keys = pygame.key.get_pressed()
        jump_pressed = any(
            event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
            for event in events
        )
        return PlayerInput(
            left=keys[pygame.K_a] or keys[pygame.K_LEFT],
            right=keys[pygame.K_d] or keys[pygame.K_RIGHT],
            run=keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT],
            jump_pressed=jump_pressed,
            jump_held=keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP],
        )

    def _update_playing(self, dt: float, events: list[pygame.event.Event]) -> None:
        assert self.level is not None and self.player is not None
        controls = self._controls_from_keyboard(events)
        self.player.update(dt, controls, self.level.solids)
        if self.player.jumped_this_frame:
            self.audio.play("jump")
        self.camera.update(self.player.hitbox, dt)
        self.level.update_enemies(dt, self.camera.visible_rect)
        self.level.update_effects(dt)
        if self.player.hit_ceiling and self.level.hit_coin_block(self.player.hitbox):
            self.session_coins += 1
            self.audio.play("coin")
        self.banner_timer = max(0.0, self.banner_timer - dt)
        self._resolve_interactions()

    def _resolve_interactions(self) -> None:
        assert self.level is not None and self.player is not None
        for coin in self.level.coins:
            if not coin.collected and self.player.hitbox.colliderect(coin.rect):
                coin.collected = True
                self.session_coins += 1
                self.audio.play("coin")
                self.level.spawn_effect("sparkle", coin.rect.center)
        for powerup in self.level.powerups:
            if not powerup.collected and self.player.hitbox.colliderect(powerup.rect):
                powerup.collected = True
                self.player.activate_power(powerup.kind)
                self.audio.play("powerup")
                self.level.spawn_effect("power", powerup.rect.center, 0.65)
        for checkpoint in self.level.checkpoints:
            if self.player.hitbox.colliderect(checkpoint):
                new_spawn = pygame.Vector2(checkpoint.x - 6, checkpoint.bottom - self.player.hitbox.height)
                if new_spawn != self.player.checkpoint:
                    self.player.checkpoint = new_spawn
                    self.audio.play("checkpoint")
        for enemy in self.level.enemies:
            if not enemy.alive or not self.player.hitbox.colliderect(enemy.hitbox):
                continue
            stomped = self.player.velocity.y > 80 and self.player.hitbox.bottom - enemy.hitbox.top < 25
            if stomped:
                enemy.take_damage()
                self.player.hitbox.bottom = enemy.hitbox.top
                self.player.position.y = self.player.hitbox.y
                self.player.velocity.y = -470
                self.audio.play("stomp")
                self.level.spawn_effect("smoke", enemy.hitbox.midbottom)
            elif self.player.take_damage():
                self.level.spawn_effect("smoke", self.player.hitbox.center)
                self._lose_life()
                return
        if any(self.player.hitbox.colliderect(rect) for rect in self.level.hazards):
            self._lose_life()
            return
        if self.player.hitbox.top > self.level.height_px + 100:
            self._lose_life()
            return
        if any(self.player.hitbox.colliderect(rect) for rect in self.level.goals):
            self._finish_level()

    def _lose_life(self) -> None:
        assert self.player is not None
        self.lives -= 1
        self.audio.play("death" if self.lives <= 0 else "hurt")
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
            self.menu.selected = 0
        else:
            assert self.level is not None
            self.level.reset_enemies()
            self.player.respawn()
            self.camera.x = max(0.0, self.player.hitbox.centerx - settings.SCREEN_WIDTH * 0.43)

    def _finish_level(self) -> None:
        self.audio.play("complete")
        self.progress["total_coins"] += self.session_coins
        self.session_coins = 0
        if self.current_level_number < 4:
            self.progress["highest_level_unlocked"] = max(
                self.progress["highest_level_unlocked"], self.current_level_number + 1
            )
            self.state = GameState.LEVEL_COMPLETE
        else:
            self.state = GameState.VICTORY
        self.progress_store.save(self.progress)

    def _continue_after_level(self) -> None:
        if self.state == GameState.LEVEL_COMPLETE:
            self._load_level(self.current_level_number + 1)
        else:
            self.state = GameState.MENU
            self.menu.selected = 0
            self.audio.play_music("menu")

    def _draw(self) -> None:
        if self.state in (GameState.PLAYING, GameState.PAUSED):
            self._draw_world()
            if self.state == GameState.PAUSED:
                self.menu.draw(
                    self.canvas,
                    "PAUSA",
                    PAUSE_OPTIONS,
                    background=self.pause_background,
                    background_layout="pause",
                )
        elif self.state == GameState.MENU:
            self.menu.draw(
                self.canvas,
                settings.TITLE.upper(),
                ("JUGAR", "SELECCIONAR NIVEL", "CONTROLES", "SALIR"),
                "Flechas para elegir · ENTER para confirmar",
                self.menu_background,
            )
            if self.error_message:
                error = pygame.font.Font(None, 24).render(self.error_message, True, settings.RED)
                self.canvas.blit(error, error.get_rect(center=(settings.SCREEN_WIDTH // 2, 650)))
        elif self.state == GameState.LEVEL_SELECT:
            unlocked = self.progress["highest_level_unlocked"]
            labels = tuple(f"NIVEL {n}" + ("" if n <= unlocked else "  [BLOQUEADO]") for n in range(1, 5)) + ("VOLVER",)
            self.menu.draw(
                self.canvas,
                "SELECCIONAR NIVEL",
                labels,
                f"Monedas totales: {self.progress['total_coins']}",
                self.pause_background,
                "pause",
            )
        elif self.state == GameState.CONTROLS:
            draw_panel(
                self.canvas,
                "CONTROLES",
                (
                    "A / Flecha izquierda     Mover izquierda",
                    "D / Flecha derecha       Mover derecha",
                    "Espacio / W / Arriba     Saltar / doble salto",
                    "Shift                    Correr",
                    "ESC                      Pausa",
                ),
                "Pulsa ESC o ENTER para volver",
                self.pause_background,
            )
        elif self.state == GameState.GAME_OVER:
            self.menu.draw(
                self.canvas,
                "GAME OVER",
                GAME_OVER_OPTIONS,
                "La expedición aún puede continuar",
                self.menu_background,
                "game_over",
            )
        elif self.state == GameState.LEVEL_COMPLETE:
            draw_panel(
                self.canvas,
                "¡NIVEL COMPLETADO!",
                (f"Has superado el nivel {self.current_level_number}", f"Vidas restantes: {self.lives}"),
                "Pulsa ENTER para continuar",
                self.pause_background,
            )
        elif self.state == GameState.VICTORY:
            draw_panel(
                self.canvas,
                "¡MISIÓN CUMPLIDA!",
                ("Has cruzado los cuatro mundos.", f"Monedas guardadas: {self.progress['total_coins']}"),
                "Pulsa ENTER para volver al menú",
                self.pause_background,
            )
        if self.state in {
            GameState.LEVEL_SELECT,
            GameState.CONTROLS,
            GameState.PAUSED,
            GameState.LEVEL_COMPLETE,
            GameState.VICTORY,
        }:
            active_power = self.player.active_power if self.player else None
            power_time = self.player.power_timer if self.player else 0.0
            displayed_coins = (
                self.progress["total_coins"]
                if self.state == GameState.LEVEL_SELECT
                else self.session_coins
            )
            self.hud.draw(
                self.canvas,
                self.lives,
                displayed_coins,
                self.current_level_number,
                active_power,
                power_time,
                self.clock.get_fps(),
            )
        scaled = pygame.transform.scale(self.canvas, self.window.get_size())
        self.window.blit(scaled, (0, 0))

    def _draw_world(self) -> None:
        assert self.level is not None and self.player is not None
        self.canvas.fill(settings.SKY)
        if self.level.background:
            background = self.level.background
            shift_x = -int(self.camera.x * 0.2) % background.get_width()
            shift_y = -int(self.camera.y * 0.1) % background.get_height()
            for y in range(shift_y - background.get_height(), settings.SCREEN_HEIGHT, background.get_height()):
                for x in range(shift_x - background.get_width(), settings.SCREEN_WIDTH, background.get_width()):
                    self.canvas.blit(background, (x, y))
        else:
            # Original geometric fallback used only while no background asset exists.
            cloud_shift = -int(self.camera.x * 0.18) % 420
            for x in range(cloud_shift - 420, settings.SCREEN_WIDTH + 420, 420):
                pygame.draw.ellipse(self.canvas, (209, 235, 244), (x, 115, 190, 55))
            hill_shift = -int(self.camera.x * 0.35) % 520
            for x in range(hill_shift - 520, settings.SCREEN_WIDTH + 520, 520):
                pygame.draw.polygon(self.canvas, (73, 154, 137), [(x, 620), (x + 250, 310), (x + 520, 620)])
        camera_rect = self.camera.visible_rect
        self.level.draw(self.canvas, camera_rect)
        self.player.draw(self.canvas, camera_rect.topleft)
        self.hud.draw(self.canvas, self.lives, self.session_coins, self.current_level_number, self.player.active_power, self.player.power_timer, self.clock.get_fps())
        if self.banner_timer > 0:
            hint = self.level.data.hint
            panel = pygame.Surface((760, 74), pygame.SRCALPHA)
            panel.fill((21, 29, 50, 195))
            self.canvas.blit(panel, panel.get_rect(center=(settings.SCREEN_WIDTH // 2, 105)))
            text = pygame.font.Font(None, 28).render(hint, True, settings.WHITE)
            self.canvas.blit(text, text.get_rect(center=(settings.SCREEN_WIDTH // 2, 105)))
