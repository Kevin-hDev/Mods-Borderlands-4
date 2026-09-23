# Vehicle Driving

Version **1.0.1**. Open Vehicle Driving in the SDK mods menu for its English/French settings window. It works at the title screen, in a game, at the wheel and while the game is paused. The window remembers the last section you opened.

Livelier vehicles for Borderlands 4: a higher top speed, a quicker pick-up, sharper turns, higher jumps, and a grip
that keeps the vehicle going where it faces instead of sliding on through turns. Every effect has its own setting in
the mod menu.

Created and tested on game versions **1.8.1-4709277** through **1.10.2-4845623**, single player, with a controller,
on three different vehicles. It has not been tested on versions older than 1.8.1-4709277 and may not work there.

## The settings

Console `~`, command `mods`, Vehicle Driving. The window splits them into two pages: Driving (the first four) and
Handling (the grip).

| Setting | What it does | Default | Range |
|---|---|---|---|
| Max speed | Top speed, in percent of the game's, Hover Drive bonus included | 125 % | 100 to 300 % |
| Acceleration | How fast the vehicle picks up speed, after a turn too | 250 % | 100 to 500 % |
| Turn speed | How fast the vehicle turns toward your camera | 250 % | 100 to 500 % |
| Jump height | How high the vehicle jumps | 200 % | 100 to 400 % |
| Grip | The vehicle goes where it faces instead of sliding on in turns | on | — |
| Speed lost in a 90 degree turn | The share of speed the grip lets go in a 90 degree turn | 9 % | 0 to 30 % |

At 100 %, a setting gives the game's own value, so each effect can be turned off on its own. The grip has a switch,
since no percentage turns it off. The game's own braking adds to the speed lost in a turn: at full throttle, a big
turn loses a little more than the setting says.

Every slider is held to its range, even a value typed out of range in the console menu or edited by hand in the
settings file; the SDK log says when one is brought back. Settings are stored in
`...\Borderlands 4\sdk_mods\settings\vehicle_driving.json`.

The mod turns itself on the first time the game launches with it installed. It only changes the vehicle you drive,
while you drive it: getting out, or switching the mod off, gives the game's own values back.

## With Apex Movement

Vehicle Driving installs beside [Apex Movement](../apex_movement/): its own package name, frame hook and settings
file, no key bound, and no game value in common.

## How it is put together

- `frame.py` runs the mod once per frame while you drive; the values and the grip each stop on their own after an
  error, so one broken part does not take the other down.
- `seat.py` finds the vehicle you drive: at the wheel, the controller's pawn is the vehicle.
- `levers.py` says which game values each setting multiplies: the driver's speed and acceleration attributes, the
  vehicle's turning springs and its jump height.
- `tuning.py` keeps the game's own value of everything the mod writes, and puts it back when you get out or switch
  the mod off. A value is always written as the game's own times its setting, never as the value in the game times
  it, so nothing is multiplied twice; a value the game rewrites, such as a new Hover Drive's bonus, is followed.
- `grip.py` turns the vehicle's speed toward where it faces, 360 degrees a second at most, losing the set share of
  speed for each degree turned. It lets the game drive in the air, going fast up or down, during the game's
  powerslide, under 300 of speed, and for a gap under 2 or over 120 degrees.
- `ground.py` checks there is ground under the vehicle, with one trace straight down.
- `panel_*.py` and `control_*.py` draw the settings window and hand the controls back to the console menu when it
  closes; `menu.py` groups the settings into its pages.
- `settings.py` holds every setting with its default and its range; `report.py` writes the mod's lines in the SDK
  log, each failure once.

## Tests

```
python test_grip.py
```

The test files sit next to the modules and need nothing installed: they replace the game's SDK with stand-in objects.
Each prints a `RESULTAT:` line and exits non-zero on failure.

## Known limits

- Never tried in co-op.
- Tested on three vehicles; other vehicles have their own settings and may react differently.
- At a very high Max speed, from about 250 %, the world may not load fast enough on some PCs: textures can stay blurry
  for a moment and objects can appear late. It depends mostly on your graphics card's memory and your in-game
  graphics settings. Lower Max speed if it happens.
- Do not run it alongside another vehicle mod that changes the same values, such as Better Vehicle Jump or Vehicle
  Movement: whichever writes last wins.
