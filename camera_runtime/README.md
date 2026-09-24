# Camera runtime

The third-person camera and custom field of view shared by [Apex Movement](../apex_movement/) and
[Omni Sprint](../omni_sprint/). It is not a mod of its own: each of the two mods carries a copy inside its `.sdkmod`,
under its own package (`apex_movement/apex_camera_runtime/`, `omni_sprint/apex_camera_runtime/`). When both mods are
installed, one runtime serves them both and Apex Movement's camera settings are the ones used.

Tested in single player on game version **1.10.2-4845623**. Windows only.

## What it does

- Third person on foot: the local player's on-foot camera uses the game's own ThirdPerson camera mode, shifted over
  the shoulder. Aiming hands the view back to the game's own first-person aim, and the shoulder shift is suspended
  while it would put the camera through a wall.
- A key turns third person on and off. It takes keyboard keys and mouse buttons, but never a controller button, the
  left mouse button, the console key or Escape.
- Custom FOV: while it is enabled, the runtime writes the player's field of view; switched off, it gives the game's own
  value back, as long as the field of view is still the one it wrote.

## How it is put together

- `shared.py` creates one runtime even when two installed mods carry this package, and `bootstrap.py` connects it to
  the game's SDK once. `arbitration.py` decides which mod's settings it follows, the same way on every launch.
- `runtime.py` follows the chosen mod's settings. `third_person.py`, `transitions.py`, `aiming.py` and `collision.py`
  handle the camera, `fov.py` the field of view, and `lifetime.py` and `cleanup.py` let go of everything when the
  player or the mod goes away.
- `native_bridge.py` loads the native library through a checked `ctypes` boundary, after comparing its SHA-256 with
  `assets/apex_camera_view_v4.sha256`.
- `key_option.py` keeps a saved key valid: a key it refuses becomes unbound instead of reaching the game.

## Native library

`apex_camera_runtime/assets/apex_camera_view_v4.dll` hooks the camera's view update to apply the over-the-shoulder
offset to the final view, within fixed bounds. Its source is in `native_camera/`. `native_camera/build.ps1` builds it
with Visual Studio's C++ build tools (x64): it compiles and runs the native test first, then writes the DLL and its
SHA-256 into `apex_camera_runtime/assets/`.

## Tests

```
cd camera_runtime
python test_camera_runtime.py
```

The Python tests replace the game's SDK with stand-ins (`camera_test_fixtures.py`) and need nothing installed. Run each
test script separately; a failing test exits with a non-zero code. The native test runs as part of `build.ps1`.
