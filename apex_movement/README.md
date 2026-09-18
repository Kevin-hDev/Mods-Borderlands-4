# Apex Movement

Apex Legends style movement for Borderlands 4. Eight moves, each with its own switch and its own settings in the mod menu.

Built and tested on game version **1.8.1-4709277**, in the first area of the game, single player, with both a controller and mouse and keyboard.

## The moves

The menu lines are named after the game's own option screen (Sprint, Slide, Dash, Slam), so that a line of the menu
and a line of the Nexus page name the same move.

| Move | What it does | On by default |
|---|---|---|
| Movement | Walk and sprint speeds, raised a little. No switch: they apply whether auto sprint is on or off | — |
| Auto sprint | Sprint as soon as the move stick is fully pushed, up to the game's own 60 degree limit | yes |
| Slides | Follow the way you are going, not the way you are aiming; slowed uphill, carried downhill | yes |
| Axle slide | Axle's slide from Apex: steered with the move stick, and boosted every time | no |
| Dash | Goes further, at the game's own speed: its length changes, not its speed | yes |
| Slam and landing slide | Jump + crouch together to slam, and crouch held in the air to slide the moment you land | yes |
| Air / tap strafe | Change direction in the air almost at once, and start and stop faster on the ground | yes |
| Heavier fall | Come down faster while every jump keeps its height, plus a little extra height | yes |
| Wall climb | Climb up a wall, straight or diagonally, and pull yourself over the top | yes |

Dashing in the air is the game's own move, not one this mod adds: the mod blocks the crouch key to tell a tap from a
hold, which would remove that dash, so it asks the game for it back.

The mod turns itself on the first time the game launches with it installed.

## Settings

Console `~`, command `mods`, Apex Movement. One line per move; each line opens that move's switch and its settings. Every setting gives the game's own value where there is one.

Settings are stored in `...\Borderlands 4\sdk_mods\settings\Apex Movement.json`.

## How it is put together

- `frame.py` runs every move once per frame, in a fixed order; each move is a module with `update`, `stop` and `reset`.
- `ground_speed.py` holds the walk and sprint speeds, apart from `sprint.py`, which only asks the game to sprint.
- `game.py` is the only place that reads the game's own fields, so a field that moves in a game update is renamed in one file.
- `ownership.py` remembers every game value a move overwrites, and puts it back when the move stops. Nothing is written to the save file.
- `settings.py` holds every setting with its default and its bounds, and carries the reason each default was chosen.
- The wall climb is split by responsibility: `wall_sense` measures the wall, `climb_aim` does the geometry, `climb_rules` decides whether a climb starts and keeps going, `wall_climb` moves the character, `climb_refusal` writes why a climb was refused.

## Tests

```
python test_wall_climb.py
```

Twenty-nine test files, one per module, needing nothing installed: they replace the game's SDK with stand-in objects. Each prints a `RESULTAT:` line and exits non-zero on failure.

## Known limits

- Never tried in co-op.
- Tested in the first area of the game only; other places will have surfaces the wall climb reacts to differently.
- Do not run it alongside another movement mod: both write the character's speed every frame, and whichever writes last wins.
