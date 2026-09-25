# Third Person & FOV

An over-the-shoulder camera and a wider field of view for Borderlands 4, without the movement changes from Apex
Movement or Omni Sprint.

Tested in single player on game version **1.10.2-4845623**. Windows only.

## What it does

- Keeps the camera behind the character while on foot. Third person is off by default.
- Aiming uses the game's native first-person view, then returns to third person when aim is released.
- Sliding and leaving a vehicle return to the selected on-foot camera.
- P turns third person on or off by default. The keyboard or mouse key can be changed in the mod menu.
- The FOV slider ranges from 70 to 150 and applies while the mod is enabled. Disabling the mod restores the game's
  FOV.

With Apex Movement installed, Apex Movement's camera settings are the ones used. With Omni Sprint, this pack's
settings are the ones used.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Put `third_person_fov.sdkmod` in the game's `sdk_mods` folder.
3. Launch the game, open the console with `~`, type `mods`, and open **Third Person & FOV**.

## How it is put together

The mod uses the shared [camera runtime](../camera_runtime/) also carried by Apex Movement and Omni Sprint. The
runtime owns one camera configuration at a time, restores the game's FOV when it stops, and uses a small checked
native library for the third-person offset.

No code from BL4NativeCameraToggle is included.

## Tests

Run each test separately from this folder:

```text
python test_settings.py
python test_camera.py
python test_frame.py
python test_mod.py
```

Each test prints a `RESULTAT:` line and exits with a non-zero code on failure.

## Known limits

- Not tested in co-op, on Linux, or on Steam Deck.
- A future game update may change the native camera structures and require an update to the bundled bridge.
