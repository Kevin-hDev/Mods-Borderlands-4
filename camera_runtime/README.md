# Camera runtime

The camera shared by [Apex Movement](../apex_movement/), [Omni Sprint](../omni_sprint/) and
[Third Person & FOV](../third_person_fov/). It is not a mod of its own: each of the three mods carries a copy inside
its `.sdkmod`, under its own package (`apex_movement/apex_camera_runtime/`, and so on). When several of them are
installed, one runtime serves them all and follows one mod's settings: Apex Movement's first.

Tested in single player on game version **1.10.2-4845623**. Windows only.

## What it does

- **Third person** on foot: the game's own ThirdPerson camera mode, shifted over the shoulder. A saved Aim View
  setting selects third-person aim (default) with native weapon zoom and a visible reticle, or first-person aim.
  Sniper rifles stay in first person; heavy and unsupported weapons retain native aim. Crouch and shoulder switching
  remain available while aiming; sliding, leaving a vehicle, landing a ground slam and being downed keep the
  selected camera. The shoulder shift is suspended while it would put the camera through a wall.
- **Shoulder**: the camera sits over the right shoulder or the left one.
- **Orbit camera**: the game's own Orbit mode, a camera that turns freely around the character. Two commands move it
  closer or farther away, 25 units a press, from 75 to 600 (300 at first); the distance is kept per mod.
- **Custom FOV**: while it is enabled, the runtime writes the player's field of view; switched off, it gives the
  game's own value back, as long as the field of view is still the one it wrote.
- **Loot reach**: ground items and loot containers can be picked up from farther away, 2× by default, from 1× to 3×.
  Vendors, characters and vehicles keep the game's own reach. At 1×, or switched off, the game's reach is back.
- **Interaction aim**: in third person, the item under the crosshair is the one you pick up.
- **Commands**: five actions (third person, switch shoulder, orbit camera, zoom in, zoom out), each with a keyboard
  or mouse key and a controller button. Keyboard defaults are P, 6 and 7, and none for the zoom; no controller button
  is set by default. The same key cannot serve two camera actions on one device. The keyboard side refuses controller
  buttons, the left mouse button, the console key and Escape; the controller side takes controller buttons only.

## How it is put together

- `shared.py` creates one runtime even when several installed mods carry this package, and tells a mod's menu whose
  settings apply without creating it. `bootstrap.py` connects the runtime to the game's SDK once. `arbitration.py`
  decides which mod's settings it follows, the same way on every launch.
- `runtime.py` follows the chosen mod's settings. `third_person.py`, `foot_mode.py`, `transitions.py`, `aiming.py`,
  `shoulder.py`, `orbit_zoom.py` and `collision.py` handle the camera; each change of camera mode is one confirmed
  transaction that is rolled back if the game refuses it (`foot_mode_rollback.py`, `foot_preemption.py`). `fov.py`
  owns the field of view, and `lifetime.py`, `cleanup.py` and `cleanup_retry.py` let go of everything when the player
  or the mod goes away.
- `loot_runtime.py`, `loot_unit.py` and `loot_fields.py` apply the loot reach; `loot_constants.py` holds its bounds.
- `camera_commands.py` holds the five actions, their defaults and the duplicate rule; `key_option.py` keeps a saved
  key valid, turning a refused one into no key instead of letting it reach the game.
- `option_texts.py` holds the English names and descriptions every owner gives its camera settings.
- `native_bridge.py`, `interaction_bridge.py` and `loot_bridge.py` load the native libraries through checked `ctypes`
  boundaries, each after comparing its SHA-256 with the `.sha256` file beside it.

## Native libraries

In `apex_camera_runtime/assets/`, built from the sources in `native_camera/` with Visual Studio's C++ build tools
(x64). Each build script compiles and runs its native test first, then writes the DLL and its SHA-256:

- `apex_camera_view_v6.dll` (`build.ps1`) applies the over-the-shoulder offset and guarded native ADS presentation
  to the camera's final view, within fixed bounds.
- `apex_camera_interaction_v2.dll` (`build_interaction.ps1`) aims the interaction ray from the rendered camera.
- `apex_camera_loot_v1.dll` (`build_loot.ps1`) extends the pickup range of loot.

## Tests

```
cd camera_runtime
python test_camera_runtime.py
```

The Python tests replace the game's SDK with stand-ins (`camera_test_fixtures.py`) and need nothing installed. Run each
test script separately; a failing test exits with a non-zero code. The native tests run as part of the build scripts.
