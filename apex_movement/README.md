# Apex Movement

Apex Legends style movement for Borderlands 4. Every move has its own settings in the mod menu, and its own switch,
except the movement speeds, which are adjusted without one.

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
| Ground slam and landing slide | Jump + crouch together to slam, and crouch held in the air to slide the moment you land | yes |
| Air / tap strafe | Change direction in the air almost at once, and start and stop faster on the ground | yes |
| Heavier fall | Come down faster while every jump keeps its height, plus a little extra height | yes |
| Wall climb | Climb up a wall, straight or diagonally, and pull yourself over the top | yes |

The ground slam and the landing slide share one switch on purpose: both need the crouch key blocked in the air, and
that block is what removes the game's own slam on a held crouch. Turned off, the key goes back to the game.

Dashing in the air is the game's own move, not one this mod adds: the mod blocks the crouch key to tell a tap from a
hold, which would remove that dash, so it asks the game for it back.

The mod turns itself on the first time the game launches with it installed.

## One file, or one file per move

The full mod pack ships as `apex_movement.sdkmod`. Every move also ships on its own — `apex_wall_climb.sdkmod`,
`apex_slides.sdkmod`, and so on — built from these same sources. A separate file carries the whole package under its
own name and differs only by its `pack.py`: the moves it runs, and the name it wears in the mod list. Nothing is
generated beyond those two lines, so a separate file runs the code that was tested.

Several separate files can be installed side by side: no two moves write the same game setting they later put back
(`test_movement_rules.py` checks the named ones). A file about to switch on while another switched-on file already
runs one of its moves stays off and says why in the SDK log, rather than fighting over the same field. A file keeps
its own settings: one that does not carry the movement speeds orders its slide speeds against the game's own walk
and sprint.

## Settings

Console `~`, command `mods`, Apex Movement. One line per move; each line opens that move's switch and its settings. Every setting gives the game's own value where there is one.

Settings are stored in `...\Borderlands 4\sdk_mods\settings\apex_movement.json`, and each separate file in its own,
named after it: `apex_dash.json`, `apex_wall_climb.json`, and so on.

## How it is put together

- `frame.py` runs every move once per frame, in a fixed order; each move is a module with `update`, `stop` and `reset`.
- `movements.py` states which modules and menu lines make up each move, with the reason for every exception; `test_movement_rules.py` holds the code to it: every move turns off on its own, and none reads another's settings or imports its modules.
- `pack.py` says which moves a file carries; `family.py` keeps one move from running in two installed files at once.
- `ground_speed.py` holds the walk and sprint speeds, apart from `sprint.py`, which only asks the game to sprint.
- `game.py` finds the player and the move assets, and answers what several moves ask: on the ground, in the air, sliding, whether one of the game's own moves is running. It asks the game that last one (`IsPerformingControlledMove`) rather than reading the move's network copy, which keeps a ground slam after landing until the next slide. A field only one move touches is read in that move's module.
- `ownership.py` remembers every game value a move overwrites, and puts it back when the move stops. Nothing is written to the save file.
- `settings.py` holds every setting with its default and its bounds, and carries the reason each default was chosen.
- `speed_order.py` keeps walk, sprint, slide and top slide speeds in order whatever the sliders say; a file without the movement speeds orders against the game's own.
- The wall climb is split by responsibility: `wall_sense` measures the wall, `wall_choice` picks the surface among what the rays met, `climb_aim` does the geometry, `climb_rules` decides whether a climb starts and keeps going, `wall_climb` moves the character, `climb_refusal` writes why a climb was refused, `climb_animation` plays the game's own climbing animation on the first-person arms `arms` finds.
- `jump_report.py` and `move_watch.py` write every jump and every change of the game's own moves to the SDK log, a few hundred lines at most: on a game version not tested here, those lines show what changed.

## Tests

```
python test_wall_climb.py
```

The test files sit next to the modules and need nothing installed: they replace the game's SDK with stand-in objects
that follow the real one where the mod depends on it, down to a mod being switched on from its settings file while it
is still being built. Each prints a `RESULTAT:` line and exits non-zero on failure.

## Known limits

- Never tried in co-op.
- Tested in the first area of the game only; other places will have surfaces the wall climb reacts to differently.
- Do not run it alongside another movement mod: both write the character's speed every frame, and whichever writes last wins.
