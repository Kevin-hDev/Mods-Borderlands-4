# Omni Sprint

Sprint in every direction in Borderlands 4: sideways, diagonally and backwards, while the camera stays free. It is the
game's own sprint, at the game's own speed: the mod only lifts the angle limit that stops it.

Created and tested on game versions **1.8.1-4709277** through **1.10.2-4845623**, single player, with a controller
and a keyboard, with two characters. It has not been tested on versions older than 1.8.1-4709277 and may not work
there.

## What it does

Borderlands 4 only sprints forward: once the move stick is more than 60 degrees away from where you look, the sprint
stops. Omni Sprint opens that limit to 180 degrees, so the sprint starts and holds in any direction.

- No speed changes: sprinting sideways or backwards goes as fast as sprinting forward.
- No key and no setting: once installed, sprint as usual.
- Switched off in the mod menu, the game's 60 degree limit is back at once.

The mod turns itself on the first time the game launches with it installed.

## With Apex Movement

Omni Sprint installs beside [Apex Movement](../apex_movement/) and [Vehicle Driving](../vehicle_driving/): its own
package name, frame hook and settings file, no key bound, and a single game value that neither of them writes. With
Apex Movement:

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
- `report.py` writes the mod's lines in the SDK log, each failure once.

If a game update changes those values, the mod finds no definition, writes nothing, and says so once in the SDK log:
the game simply sprints as usual.

## Tests

```
python test_limit.py
```

The test files sit next to the modules and need nothing installed: they replace the game's SDK with stand-in objects
and its memory with a fake block. `test_memory.py` runs the real Windows calls on its own process. Each prints a
`RESULTAT:` line and exits non-zero on failure.

## Known limits

- Never tried in co-op.
- Windows only: the memory calls are Windows ones. Not tried on Linux or Steam Deck.
- Tested with two characters, Vex and Harlowe. The other two have the same kind of definition, but were not tried.
