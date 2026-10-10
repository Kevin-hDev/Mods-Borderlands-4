# Apex Movement

Version **1.2.16**. Open Apex Movement in the SDK mods menu for its English/French settings window. It works at the title screen, in a game and while the game is paused. The window remembers the last section you opened. The gear at the top of the window opens the Options page: the camera, its commands and the menu language.

Third-person view and aiming support the tested Steam and Epic Games builds. Extended loot reach is not supported on Epic Games yet. The custom climbing body animation is also not supported on Epic Games yet. If you have several of our camera mods installed, update Apex Movement, Omni Sprint and Third Person & FOV together.

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
| Slow walk | On the Movement page. Hold Caps Lock to walk slowly, even mid-sprint, with or without auto sprint, from 150 to 540, 300 by default. As a toggle, off by default, one press walks and another stops; the sprint key or going down also ends it. Full pack only | yes |
| Auto sprint | Sprint as soon as the move stick is fully pushed, up to the game's own 60 degree limit | yes |
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

- **Third person**: an over-the-shoulder camera on foot, off by default. Aim View defaults to third person,
  with native weapon zoom and a visible reticle; choose first person in Camera settings if preferred.
  Crouch and switch shoulders while aiming. When downed, and when a ground slam lands, the view stays in third
  person.
- **Optics**: Every weapon type has its optic on the AIMING page: BDL4 keeps the game's first-person aim, the zooms
  you tick aim over the shoulder (pistols x1 to x3, SMGs and assault rifles x1 to x4, shotguns and heavy
  weapons x1 and x2, sniper rifles x2 to x8). With several zooms ticked, a key switches from one to the next.
  Unsupported weapons keep the native view.
- **Omni direction**: in third person, the character turns toward where it runs, all the way round (360°) or up
  to the sides (180°), sprints in every direction and stays turned when it stops.
- **Sensitivity**: the camera's speed in third person, without aiming and while aiming, with mouse and
  controller. Optional aim speeds per weapon type and per optic zoom, each with its own switch.
- **Shoulder**: the camera sits over the right shoulder by default, or the left one.
- **Automatic shoulder switch**: when a wall blocks the view ahead, the camera moves to the other shoulder, then
  comes back once the view is clear. On by default, never while aiming; its switch and both delays sit next to the
  shoulder, on the SHOULDER VIEW tab.
- **Orbit camera**: the camera turns freely around the character. The shoulder and the orbit camera only work in
  third person, and are greyed while it is off.
- **Camera distance**: in third person, the 8 key moves the camera from close to normal to far, with a glide;
  aiming keeps the usual aiming distance. Normal is the game's camera; close (1.80 m) and far (3.60 m) are set
  to the centimetre on the CAMERA VIEW tab.
- **Custom FOV**: a field of view from 70 to 150, off by default. Switched off, the game's own FOV is used.
- **Extended loot reach**: pick up loot and open containers from farther away, from 1× to 3×, 2× by default. Vendors,
  characters and vehicles keep the game's own reach.
- **Dynamic camera**, on by default: the view widens while sprinting or sliding, the camera moves back while
  running, in the air or driving fast and closer when crouched, and it follows your changes of speed softly. Each
  effect has its own switch and strength. With Vehicle Driving, its chosen view stays and the driving framing adds to it.
- **Free Look**: hold the key right of Tab (A on AZERTY, Q on QWERTY) or L3 to turn the camera while the character
  or the vehicle keeps going. On foot you keep your speed, left or right turns the run, and letting go stops you
  unless you hold a movement key; first person switches to third person while held. A vehicle keeps its speed and
  goes straight until you brake. Aiming ends it. Hold or press-to-toggle and the hold time (0.20 s) are set on the CAMERA VIEW tab.

The **Commands** page sets each camera key twice, once for keyboard and mouse and once for controller: third person
(P by default), switch shoulder (6), orbit camera (7), orbit camera zoom in and out (no key by default), Free
Look (the key right of Tab, L3) and camera distance (8). Free Look is the only camera action with a controller button by default. The page shows PlayStation or Xbox icons, and DEFAULT KEYS puts the camera keys
back. The left mouse button is refused: it fires and clicks through menus.

The camera is the shared [camera runtime](../camera_runtime/), which Omni Sprint and Third Person & FOV carry too.
When Apex Movement is installed with one of them, its camera settings are the ones used. The separate one-move files
do not carry the camera.

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

Console `~`, command `mods`, Apex Movement: its settings window opens, with one page per move holding that move's switch and its settings. Every setting gives the game's own value where there is one.

Settings are stored in `...\Borderlands 4\sdk_mods\settings\apex_movement.json`, and each separate file in its own,
named after it: `apex_dash.json`, `apex_wall_climb.json`, and so on.

## How it is put together

- `frame.py` runs every move once per frame, in a fixed order; each move is a module with `update`, `stop` and `reset`.
- `movements.py` states which modules and menu lines make up each move, with the reason for every exception; `test_movement_rules.py` holds the code to it: every move turns off on its own, and none reads another's settings or imports its modules.
- `pack.py` says which moves a file carries; `family.py` keeps one move from running in two installed files at once.
- `ground_speed.py` holds the walk and sprint speeds, apart from `sprint.py`, which only asks the game to sprint. The speed floor it writes can only raise the game's speed, so the slow walk also lowers the character's own speed scale while standing, and puts the game's back as soon as it ends.
- `walk_key.py` holds the slow walk key, its switch, its hold or toggle mode and its speed; the ground speed applies that speed. `slow_walk.py` makes the slow walk win over every sprint, the game's own included, by ending the sprint through the auto sprint, the one writer of the sprint request. `shortcut_key.py` gives every file, the separate ones included, the key option of the camera runtime.
- `game.py` finds the player and the move assets, and answers what several moves ask: on the ground, in the air, sliding, whether one of the game's own moves is running. It asks the game that last one (`IsPerformingControlledMove`) rather than reading the move's network copy, which keeps a ground slam after landing until the next slide. A field only one move touches is read in that move's module.
- `dash_lookup.py` finds the dash of the character being played: the first four share `Move_Dash`, while C4SH and Loveless each have their own. No field of the character points at it, so it is found by name. `dash.py` puts the extra speed in the dash's speed curve rather than in its speed, since Loveless's dash reads the first and not the second.
- `ownership.py` remembers every game value a move overwrites, and puts it back when the move stops. Nothing is written to the save file.
- `settings.py` holds every setting with its default and its bounds, and carries the reason each default was chosen.
- `speed_order.py` keeps walk, sprint, slide and top slide speeds in order whatever the sliders say; a file without the movement speeds orders against the game's own.
- The wall climb is split by responsibility: `wall_sense` measures the wall, `wall_choice` picks the surface among what the rays met, `climb_aim` does the geometry, `climb_rules` decides whether a climb starts and keeps going, `wall_climb` moves the character, `climb_refusal` writes why a climb was refused, `climb_animation` plays the game's own climbing animation on the first-person arms `arms` finds.
- `camera.py` and `camera_settings.py` connect the full pack to the shared camera runtime; `panel_options.py` draws the Options page, `panel_camera_commands.py` the Commands page, and `panel_shortcut.py` the key field beside the Slow walk switch.
- `jump_report.py` and `move_watch.py` write every jump and every change of the game's own moves to the SDK log, a few hundred lines at most: on a game version not tested here, those lines show what changed.

## Camera framing

Native wall climbing stays in third person, including the pull over the ledge.
Shoulder switching is smooth by default; its animation can be disabled and its
duration adjusted from 0.05 to 1 second in Camera (0.20 seconds by default).
Native climbing has its own smooth recentering, independent of this duration.
Camera controls are grouped into four tabs. These camera features belong to
the full pack, not the separate movement files.

Camera presets and custom sliders adjust aim zoom, shoulder spacing, and height.
Standard adds 15% aim zoom and 10% shoulder spacing; height is unchanged.
Weapon-specific zoom remains active. Near obstacles, collision handling may
temporarily reduce the chosen framing. The reticle remains centered.

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
