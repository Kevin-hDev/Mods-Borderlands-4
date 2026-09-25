# Apex Movement

Version **1.1.5**. Open Apex Movement in the SDK mods menu for its English/French settings window. It works at the title screen, in a game and while the game is paused. The window remembers the last section you opened. The gear at the top of the window opens the Options page: third person, its key, a custom field of view and the menu language.

Apex Legends style movement for Borderlands 4. Every move has its own settings in the mod menu, and its own switch,
except the movement speeds, which are adjusted without one.

Created and tested on game versions **1.8.1-4709277** through **1.10.2-4845623**, in the first area of the game,
single player, with both a controller and mouse and keyboard. It has not been tested on versions older than
1.8.1-4709277 and may not work there.

## The moves

The menu lines are named after the game's own option screen (Sprint, Slide, Dash, Slam), so that a line of the menu
and a line of the Nexus page name the same move.

| Move | What it does | On by default |
|---|---|---|
| Movement | Walk and sprint speeds, raised a little. No switch: they apply whether auto sprint is on or off | — |
| Auto sprint | Sprint as soon as the move stick is fully pushed, up to the game's own 60 degree limit. Hold the walk key (Caps Lock by default) to walk slowly instead, from 150 to 540, 300 by default | yes |
| Slides | Follow the way you are going, not the way you are aiming; slowed uphill, carried downhill | yes |
| Axle slide | Axle's slide from Apex: steered with the move stick, and boosted every time | no |
| Dash | Goes further, at the game's own speed: its length changes, not its speed. Past 300 % it starts faster instead | yes |
| Glide | Hold jump in the air and glide faster, in every direction; the descent is the game's own | yes |
| Ground slam and landing slide | Jump + crouch together to slam, and crouch held in the air to slide the moment you land | yes |
| Air / tap strafe | Change direction in the air almost at once, and start and stop faster on the ground | yes |
| Heavier fall | Come down faster while every jump keeps its height, plus a little extra height | yes |
| Wall climb | Climb up a wall, straight or leaning up to 90 degrees along it, and pull yourself over the top | yes |

The ground slam and the landing slide share one switch on purpose: both need the crouch key blocked in the air, and
that block is what removes the game's own slam on a held crouch. Turned off, the key goes back to the game.

Dashing in the air is the game's own move, not one this mod adds: the mod blocks the crouch key to tell a tap from a
hold, which would remove that dash, so it asks the game for it back.

The mod turns itself on the first time the game launches with it installed.

## Camera

The full pack also carries an optional camera, on the Options page:

- **Third person**: an over-the-shoulder camera on foot, off by default. Aiming switches to the game's own
  first-person view. A key turns it on and off, P by default. It is changed right beside the switch: click CHANGE,
  then press a keyboard key or a mouse button other than the left one, which fires and clicks through menus.
- **Custom FOV**: a field of view from 70 to 150, off by default. Switched off, the game's own FOV is used.

The camera is the shared [camera runtime](../camera_runtime/), which Omni Sprint carries too. When both mods are
installed, Apex Movement's camera settings are the ones used. The separate one-move files do not carry the camera.

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
- `ground_speed.py` holds the walk and sprint speeds, apart from `sprint.py`, which only asks the game to sprint. The speed floor it writes can only raise the game's speed, so the walk key's slower walk also lowers the character's own speed scale while standing, and puts the game's back as soon as the key is released.
- `walk_key.py` holds the walk key, its switch and its speed, and whether it is held: the auto sprint asks the walk, the ground speed applies it. `shortcut_key.py` gives every file, the separate ones included, the key option of the camera runtime.
- `game.py` finds the player and the move assets, and answers what several moves ask: on the ground, in the air, sliding, whether one of the game's own moves is running. It asks the game that last one (`IsPerformingControlledMove`) rather than reading the move's network copy, which keeps a ground slam after landing until the next slide. A field only one move touches is read in that move's module.
- `dash_lookup.py` finds the dash of the character being played: the first four share `Move_Dash`, while C4SH and Loveless each have their own. No field of the character points at it, so it is found by name. `dash.py` puts the extra speed in the dash's speed curve rather than in its speed, since Loveless's dash reads the first and not the second.
- `ownership.py` remembers every game value a move overwrites, and puts it back when the move stops. Nothing is written to the save file.
- `settings.py` holds every setting with its default and its bounds, and carries the reason each default was chosen.
- `speed_order.py` keeps walk, sprint, slide and top slide speeds in order whatever the sliders say; a file without the movement speeds orders against the game's own.
- The wall climb is split by responsibility: `wall_sense` measures the wall, `wall_choice` picks the surface among what the rays met, `climb_aim` does the geometry, `climb_rules` decides whether a climb starts and keeps going, `wall_climb` moves the character, `climb_refusal` writes why a climb was refused, `climb_animation` plays the game's own climbing animation on the first-person arms `arms` finds.
- `camera.py` and `camera_settings.py` connect the full pack to the shared camera runtime; `panel_options.py` draws the Options page and `panel_shortcut.py` the key fields beside the Third Person and Walk key switches.
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
- The dash is found by name (`Move_Dash…`): a character added later under another name would keep the game's dash. When two characters' dashes are loaded at once, as co-op might do, the mod knows yours only after your first dash.
- Tested in the first area of the game only; other places will have surfaces the wall climb reacts to differently.
- Do not run it alongside another movement mod: both write the character's speed every frame, and whichever writes last wins.
