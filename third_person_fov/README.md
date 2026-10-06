# Third Person & FOV

Version **1.1.6**.

An over-the-shoulder camera and a wider field of view for Borderlands 4, without the movement changes from Apex
Movement or Omni Sprint.

Tested in single player on game version **1.10.2-4845623**. Windows only.

## What it does

- Keeps the camera behind the character while on foot. Third person is off by default.
- Aim View defaults to third person with native weapon zoom and a visible reticle; select first person in Camera
  settings if preferred. The choice is saved. Crouch and switch shoulders while aiming.
- Sniper rifles remain in first person. Heavy weapons and unsupported weapons keep the game's native view.
- Sliding, leaving a vehicle, landing a ground slam and being downed keep the selected on-foot camera.
- In third person, the camera sits over the right shoulder or the left one, and an orbit camera turns freely around
  the character. Both switches are greyed while third person is off.
- The FOV slider ranges from 70 to 150 and applies while the mod is enabled. Disabling the mod restores the game's
  FOV.
- **Extended loot reach**, on by default: pick up loot and open containers from farther away, from 1× to 3×, 2× by
  default. Vendors, characters and vehicles keep the game's own reach.
- **Dynamic camera**, on by default: the view widens while sprinting or sliding, the camera moves back while
  running, in the air or driving fast and closer when crouched, and it follows your changes of speed softly. Each
  effect has its own switch and strength. With Vehicle Driving, its chosen view stays and the driving framing adds to it.

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
