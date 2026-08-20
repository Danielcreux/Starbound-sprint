# Integración de assets

Esta carpeta está preparada exclusivamente para recursos suministrados por el usuario. El juego no descarga ni genera imágenes o audio.

## Convención automática

```text
sprites/player/idle.png, idle_0.png, walk_0.png, walk_1.png...
sprites/enemies/walker/walk_0.png...
sprites/enemies/patrol/walk_0.png...
sprites/enemies/jumper/jump_0.png...
sprites/items/coin.png
sprites/items/speed.png
sprites/items/jump.png
tiles/ground.png (o primera imagen dentro de tiles/ground/)
tiles/blocks.png
tiles/platforms.png
tiles/hazards.png
tiles/backgrounds/level_1.png ... level_4.png
sounds/jump.wav, coin.wav, hurt.wav, stomp.wav, powerup.wav...
music/menu.ogg y music/level.ogg
```

Se aceptan PNG, BMP, GIF, JPG y WEBP. Para audio se aceptan WAV, OGG, MP3 y FLAC según el soporte de SDL_mixer instalado.

Las secuencias se ordenan naturalmente (`walk_2` antes de `walk_10`). El escalado usa vecino más cercano y nunca suavizado.

## Sprite sheets y ajustes

Edita `manifest.json` para cambiar escala, velocidad o recortar una hoja. Las coordenadas son celdas, no píxeles:

```json
{
  "pixel_scale": 3,
  "player": {
    "directory": "sprites/player",
    "scale": 3,
    "fps": {"idle": 4, "walk": 10, "run": 14},
    "hitbox": [34, 44],
    "draw_offset": [0, 0],
    "spritesheet": "sprites/player/spritesheet.png",
    "frame_size": [16, 16],
    "animations": {
      "idle": [[0, 0]],
      "walk": [[1, 0], [2, 0], [3, 0]],
      "jump": [[4, 0]]
    }
  }
}
```

Si una animación o imagen falta, se muestra un aviso en consola y se conserva temporalmente el placeholder geométrico.
