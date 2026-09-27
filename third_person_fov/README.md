# Third Person & FOV

An over-the-shoulder camera and a wider field of view for Borderlands 4, without the movement changes from Apex
Movement or Omni Sprint.

Tested in single player on game version **1.10.2-4845623**. Windows only.

## What it does

- Keeps the camera behind the character while on foot. Third person is off by default.
- Aiming uses the game's native first-person view, then returns to third person when aim is released.
- Sliding, leaving a vehicle and being downed keep the selected on-foot camera.
- In third person, the camera sits over the right shoulder or the left one, and an orbit camera turns freely around
  the character. Both switches are greyed while third person is off.
- The FOV slider ranges from 70 to 150 and applies while the mod is enabled. Disabling the mod restores the game's
  FOV.
- **Extended loot reach**, on by default: pick up loot and open containers from farther away, from 1× to 3×, 2× by
  default. Vendors, characters and vehicles keep the game's own reach.

Its settings window, in English and French, has a **Camera** page and a **Commands** page. The Commands page sets
every camera key, for keyboard and mouse and for controller, with PlayStation or Xbox icons: third person (P by
default), switch shoulder (6), orbit camera (7), and orbit camera zoom in and out (no key by default). No controller
button is set by default.

With Apex Movement installed, Apex Movement's camera settings are the ones used. With Omni Sprint, this pack's
settings are the ones used.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Put `third_person_fov.sdkmod` in the game's `sdk_mods` folder.
3. Launch the game, open the console with `~`, type `mods`, and open **Third Person & FOV**.

## How it is put together

The mod uses the shared [camera runtime](../camera_runtime/) also carried by Apex Movement and Omni Sprint. The
runtime owns one camera configuration at a time, restores the game's FOV when it stops, and uses small checked
native libraries for the third-person offset, the interaction aim and the loot reach. The settings window is the one
Omni Sprint shows, generated from the same source; while another mod runs the camera, its pages point to that mod's
menu instead of showing settings that would change nothing.

No code from BL4NativeCameraToggle is included.

## Tests

Run each test separately from this folder:

```text
python test_settings.py
python test_camera.py
python test_camera_command_bindings.py
python test_frame.py
python test_mod.py
python test_panel_model.py
python test_panel_ownership.py
python test_panel_view.py
```

Each test prints a `RESULTAT:` line and exits with a non-zero code on failure.

## Known limits

- Not tested in co-op, on Linux, or on Steam Deck.
- A future game update may change the native camera structures and require an update to the bundled bridge.
