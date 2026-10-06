# Vehicle Driving

Version **1.0.6**. Open Vehicle Driving in the SDK mods menu for its English/French settings window. It works at the title screen, in a game, at the wheel and while the game is paused. The window remembers the last section you opened.

Livelier vehicles for Borderlands 4: a higher top speed, a quicker pick-up, sharper turns, higher jumps, a faster
reverse, and a grip that keeps the vehicle going where it faces instead of sliding on through turns. The boost lasts
longer and keeps pushing in the air; the vehicle is tougher and its weapons hit harder. Every effect has its own
setting in the mod menu.

Created and tested on game versions **1.8.1-4709277** through **1.10.2-4845623**, single player, with a controller,
on three different vehicles. It has not been tested on versions older than 1.8.1-4709277 and may not work there.

## The settings

Console `~`, command `mods`, Vehicle Driving. The window splits them into six pages: Driving (the first five),
Handling (the grip), Boost, Combat, Vehicles and Camera. The Camera page offers six views at the wheel, Far, Default, Close,
Closer, Closest and Custom, with three sliders for the Custom view; change view while driving with a key, L by default,
or a controller button. The chosen view is kept.

| Setting | What it does | Default | Range |
|---|---|---|---|
| Max speed | Top speed, in percent of the game's, Hover Drive bonus included | 125 % | 100 to 300 % |
| Acceleration | How fast the vehicle picks up speed, after a turn too | 250 % | 100 to 500 % |
| Turn speed | How fast the vehicle turns toward your camera | 250 % | 100 to 500 % |
| Jump height | How high the vehicle jumps | 200 % | 100 to 400 % |
| Reverse speed | How fast the vehicle backs up | 200 % | 100 to 300 % |
| Grip | The vehicle goes where it faces instead of sliding on in turns | on | on or off |
| Speed lost in turns | The share of speed the grip lets go in a 90 degree turn | 9 % | 0 to 30 % |
| Boost duration | How long the boost gauge lasts: at 150 %, one and a half times as long | 150 % | 100 to 300 % |
| Unlimited boost | The boost gauge never empties | off | on or off |
| Boost in the air | While you boost in a jump or a fall, a flat push toward the vehicle's nose, in percent of the boost's push on the ground, up to about the boost's top speed on the ground | 100 % | 0 to 300 % |
| Toughness | How much damage the vehicle takes: at 200 %, half | 200 % | 100 to 500 % |
| Weapon damage | The damage of the vehicle's machine gun and rockets | 300 % | 100 to 500 % |

At 100 %, a setting gives the game's own value, so each effect can be turned off on its own; Boost in the air does
at 0 %, since the game's boost already pushes a little in the air. The grip and the unlimited boost have a switch.
The game's own braking adds to the speed lost in a turn: at full throttle, a big turn loses a little more than the
setting says.

Every slider is held to its range, even a value typed out of range in the console menu or edited by hand in the
settings file; the SDK log says when one is brought back. Settings are stored in
`...\Borderlands 4\sdk_mods\settings\vehicle_driving.json`.

The mod turns itself on the first time the game launches with it installed. It only changes the vehicle you drive,
while you drive it: getting out, or switching the mod off, gives the game's own values back.

## Vehicle unlocking

The VEHICLES page provides three separate buttons: unlock the 10 standard vehicles, the 4 promotional vehicles, or Trident and its rewards. Use them on foot in your own game. Unlocking changes the shared profile; back up your saves first. It does not complete missions or change SHiFT currency.

Promotional vehicles stay available through reloads and full restarts while the protection is enabled. After disabling and re-enabling both owners of the shared protection, another unlock click may be needed. Disabling or uninstalling the mod can lock these promotional vehicles again.

Vehicle unlocking was tested on Steam game version 1.10.2-4845623. Cooperation and older game versions have not been tested for these buttons.

## With Apex Movement

Vehicle Driving installs beside [Apex Movement](../apex_movement/): its own package name, frame hook and settings
file, no key bound, and no game value in common.

## How it is put together

- `frame.py` runs the mod once per frame while you drive; the values, the grip and the push in the air each stop on
  their own after an error, so one broken part does not take the others down.
- `seat.py` finds the vehicle you drive: at the wheel, the controller's pawn is the vehicle. A vehicle the game has
  destroyed counts as none, even while it is still the pawn.
- `levers.py` says which game values each setting multiplies: the driver's speed, acceleration, reverse and boost
  gauge attributes, the vehicle's turning springs, its jump height and the damage it takes, and the damage of each of
  its weapons' shots.
- `tuning.py` keeps the game's own value of everything the mod writes, and puts it back when you get out or switch
  the mod off. A value is always written as the game's own times its setting, never as the value in the game times
  it, so nothing is multiplied twice; a value the game rewrites, such as a new Hover Drive's bonus, is followed. The
  driver's values and the weapons' damage are looked for again twice a second while they are not there yet: the first
  vehicle called after loading a game gets its weapons' damage a moment after you climb in.
- `grip.py` turns the vehicle's speed toward where it faces, 360 degrees a second at most, losing the set share of
  speed for each degree turned. It lets the game drive in the air, going fast up or down, during the game's
  powerslide, under 300 of speed, and for a gap under 2 or over 120 degrees. After a pause, or once switched back on,
  it never turns more than one frame's worth at once.
- `air_push.py` pushes the vehicle toward its nose, flat, while the game boosts it with no ground within 100 under
  it. The push is an impulse that adds to the vehicle's speed and leaves the game's gravity alone; it stops at the
  boost's top speed and never brakes. The vehicle's speed can still go a little past that top speed, since an impulse
  takes a few frames to arrive.
- `ground.py` checks there is ground under the vehicle, with one trace straight down.
- `panel_*.py` and `control_*.py` draw the settings window and hand the controls back to the console menu when it
  closes; `menu.py` groups the settings into its pages.
- `settings.py` holds every setting with its default and its range; `report.py` writes the mod's lines in the SDK
  log, each kind of failure once.

## Tests

```
python test_grip.py
```

The test files sit next to the modules and need nothing installed: they replace the game's SDK with stand-in objects.
Each prints a `RESULTAT:` line and exits non-zero on failure.

## Known limits

- Never tried in co-op.
- Tested on three vehicles; other vehicles have their own settings and may react differently. The settings added in
  1.0.3 (reverse, boost, toughness, weapon damage) were tested on one vehicle, on game version 1.10.2-4845623.
- At a very high Max speed, from about 250 %, the world may not load fast enough on some PCs: textures can stay blurry
  for a moment and objects can appear late. It depends mostly on your graphics card's memory and your in-game
  graphics settings. Lower Max speed if it happens.
- Do not run it alongside another vehicle mod that changes the same values, such as Better Vehicle Jump or Vehicle
  Movement: whichever writes last wins.
