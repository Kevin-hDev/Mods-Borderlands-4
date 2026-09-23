# Omni Sprint

Sprint in every direction in Borderlands 4: sideways, diagonally and backwards, while the camera stays free. Omni
Sprint keeps the game's sprint speed, supplies a backward running animation in third person, and offers an optional
field-of-view setting.

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
- Switched off in the mod menu, the game's 60 degree limit is back at once.

The mod turns itself on the first time the game launches with it installed.

## With Apex Movement

Omni Sprint installs beside [Apex Movement](../apex_movement/) and [Vehicle Driving](../vehicle_driving/). It binds
no key. With Apex Movement:

- Apex's auto sprint runs in every direction too;
- Apex's momentum slide follows your movement, so it goes sideways or backwards.

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
- `fov.py` changes the local player's FOV only while Custom FOV is enabled. Before writing, it saves the player's
  original game FOV in the mod's settings so it can restore that value after a menu transition or game restart.
- `report.py` writes the mod's lines in the SDK log, each failure once.

If a game update changes the movement definition, the mod leaves the sprint limit alone and reports it once in the
SDK log. If a matching backward animation is unavailable, that animation change is skipped.

## Tests

```
python test_fov_persistence.py
```

The test files sit next to the modules and need nothing installed: they replace the game's SDK with stand-in objects
and its memory with a fake block. `test_memory.py` runs the real Windows calls on its own process. Each prints a
`RESULTAT:` line and exits non-zero on failure.

## Known limits

- Never tried in co-op.
- Windows only: the memory calls are Windows ones. Not tried on Linux or Steam Deck.
- The original sprint was tested with Vex and Harlowe. The new backward animation and FOV behavior were verified in
  local play on the current Steam game build; they have not been checked on older builds.
- While Custom FOV is active, the game's FOV menu may show the mod's value. Disabling Custom FOV restored the native
  value in the tested 140-to-110 scenario, both after returning to the main menu and after a full game restart.
  Recovery after a restart with a custom value within the game's own 70–110 range has not been verified in play.
