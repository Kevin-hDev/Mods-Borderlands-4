# Omni Sprint

Version **1.0.10**.

Sprint in every direction in Borderlands 4: sideways, diagonally and backwards, while the camera stays free. Omni
Sprint keeps the game's sprint speed, supplies a backward running animation in third person, and offers an optional
third-person camera with an orbit camera, a field-of-view setting and a longer loot reach, in an English and French
settings window.

The original sprint was tested on game versions **1.8.1-4709277** through **1.10.2-4845623**. The backward animation
and FOV setting were tested on **1.10.2-4845623**, in single player. Co-op has not been tested.

## What it does

Borderlands 4 only sprints forward: once the move stick is more than 60 degrees away from where you look, the sprint
stops. Omni Sprint opens that limit to 180 degrees, so the sprint starts and holds in any direction.

- No speed changes: sprinting sideways or backwards goes as fast as sprinting forward.
- In third person, backward ground sprint uses the game's backward running clip instead of a frozen or walking body.
  The mod uses a private animation carrier and releases it when the sprint ends or the mod is disabled.
- No extra sprint key: sprint as usual. The optional **Custom FOV** switch is off by default; its slider ranges from
  70 to 150. With the switch off, the game's FOV is used.
- The optional **Third Person** switch, off by default, keeps an over-the-shoulder camera on foot. Aim View defaults
  to third person with native weapon zoom and a visible reticle; choose first person in Camera settings if preferred.
  Crouch and switch shoulders while aiming. Sniper rifles stay in first person; heavy and unsupported weapons keep
  the native view. A downed character and a ground slam landing stay in third person. Its key is P by default.
- In third person, key 6 switches shoulders and key 7 switches to the orbit camera, which turns freely around the
  character; two more keys, none set by default, move it closer or farther away. Both switches are greyed while
  third person is off.
- The **Commands** page sets every camera key, for keyboard and mouse and for controller, with PlayStation or Xbox
  icons. No controller button is set by default.
- **Extended loot reach**, on by default: pick up loot and open containers from farther away, from 1× to 3×, 2× by
  default. Vendors, characters and vehicles keep the game's own reach.
- Switched off in the mod menu, the game's 60 degree limit is back at once.

The mod turns itself on the first time the game launches with it installed.

## With Apex Movement

Omni Sprint installs beside [Apex Movement](../apex_movement/) and [Vehicle Driving](../vehicle_driving/). Its only
keys are the camera ones. With Apex Movement:

- Apex's auto sprint runs in every direction too;
- Apex's momentum slide follows your movement, so it goes sideways or backwards;
- Apex Movement's camera settings are the ones used: both mods carry the same camera, and only one runs it.

Without Apex Movement, the game's own slide always launches toward the camera, even out of a backward sprint.

## How it is put together

The 60 degree limit is `MaxSprintAngle`, in the character's movement definition (`OakCharacterMovementDef`). No field
the SDK can read leads to that definition, and a definition pointer built from its name stays empty, so the mod finds
it in the game's memory instead:

- `definition.py` reads, from the SDK's own type, where `MaxSprintAngle` and 20 other known values sit in the
  definition. It then tries each address held in the first 16 KB of the character's movement component, and keeps the
  one leading to a block where those 20 values are the ones of the game's settings files. No address is fixed: the
  definition moves between launches, and each character has its own.
- `limit.py` writes 180 in that definition, keeps the value it found there, and puts it back when the mod is switched
  off, only if the definition is still recognised.
- `memory.py` reads and writes through `ReadProcessMemory` and `WriteProcessMemory` on the game's own process: a wrong
  address makes the call fail instead of crashing the game.
- `frame.py` checks the played character twice a second: loading a game makes a new character, and the game may set
  the limit back. While a game loads, the character can exist before its definition is ready, so a search that
  misses is tried again, waiting twice as long each time, for about two minutes.
- `animation.py` uses a matching backward running clip from the game for the current third-person character and
  weapon. It leaves the game's original sprint animation resource alone and restores the slot it used.
- `camera.py` hands the camera settings (third person, shoulder, orbit camera, custom FOV, loot reach) to the
  shared [camera runtime](../camera_runtime/), which owns the camera. It changes the FOV only while Custom FOV is enabled, and saves the player's original game
  FOV in the mod's settings so it can restore that value after a menu transition or game restart.
- `panel_*.py` and `control_*.py` draw the settings window.
- `report.py` writes the mod's lines in the SDK log, each failure once.

If a game update changes the movement definition, the mod leaves the sprint limit alone and reports it once in the
SDK log. If a matching backward animation is unavailable, that animation change is skipped.

## Camera framing

Native wall climbing stays in third person, including the pull over the ledge.
Shoulder switching is smooth by default; its animation can be disabled and its
duration adjusted from 0.05 to 1 second in Camera (0.20 seconds by default).
Native climbing has its own smooth recentering, independent of this duration.
Camera controls are grouped into four tabs.

Camera presets and custom sliders adjust aim zoom, shoulder spacing, and height.
Standard adds 15% aim zoom and 10% shoulder spacing; height is unchanged.
Weapon-specific zoom remains active. Near obstacles, collision handling may
temporarily reduce the chosen framing. The reticle remains centered.

## Tests

```
python test_fov_persistence.py
```

The test files sit next to the modules and need nothing installed: they replace the game's SDK with stand-in objects
and its memory with a fake block. `test_memory.py` runs the real Windows calls on its own process. Each prints a
`RESULTAT:` line and exits non-zero on failure.

## Known limits

- Never tried in co-op.
- Omni Sprint's own third-person camera was tried in local play without Apex Movement on September 27, 2026.
- Windows only: the memory calls are Windows ones. Not tried on Linux or Steam Deck.
- The original sprint was tested with Vex and Harlowe. The new backward animation and FOV behavior were verified in
  local play on the current Steam game build; they have not been checked on older builds.
- While Custom FOV is active, the game's FOV menu may show the mod's value. Disabling Custom FOV restored the native
  value in the tested 140-to-110 scenario, both after returning to the main menu and after a full game restart.
  Recovery after a restart with a custom value within the game's own 70–110 range has not been verified in play.
