# Mods Borderlands 4

Mods for Borderlands 4, on foot and at the wheel, written in Python on the Borderlands 4 SDK.

| Mod | What it does | Version |
|---|---|---|
| [Apex Movement](apex_movement/) | Apex Legends style movement: auto sprint, momentum slides, air strafe, heavier falls, wall climbing | 1.1.3 |
| [Apex Grapple](apex_grapple/) | Aim at a surface, grapple toward it, steer in the air and carry momentum when you let go | 1.0.5 |
| [Vehicle Driving](vehicle_driving/) | Livelier vehicles: higher top speed, quicker acceleration and turns, higher jumps, grip in turns | 1.0.1 |
| [Omni Sprint](omni_sprint/) | Sprint in every direction, with a backward run animation and optional FOV | 1.0.1 |

## Installing a mod

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest). No mod here loads without it.
2. Put the mod's `.sdkmod` file into `...\Borderlands 4\sdk_mods\`
3. Launch the game, open the console with `~`, type `mods`.

See each mod's README for distribution and build instructions. A `.sdkmod` is a zip archive of the mod's package folder with its extension changed, so you can also build one yourself from the sources here.

## Reporting a problem

Open an issue, and say what you were doing when it happened, where you were, and which version of the game and of the mod you are on. A movement bug that only happens on one surface is almost impossible to find without those.

## Running the tests

Tests are provided alongside each mod. Most replace the game's SDK with stand-in objects and run with Python alone. Apex Grapple also has two optional integration tests that read an installed console menu; see its README for setup.

```
cd apex_movement
python test_wall_climb.py
```

Run each test script separately. A failing test exits with a non-zero code; optional integration tests print `SKIP` when their SDK input is not configured.

## License

The original code in this repository is licensed under the [Apache License 2.0](LICENSE). Copyright 2026 Kevin-hDev.

Apex Grapple's bundled Anton and Barlow Condensed fonts retain their SIL Open Font License 1.1; their license files are included in its `assets` directory. Game assets and the Borderlands 4 SDK are not relicensed by this repository.

## Credits

- The [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager) team, without whom none of this would exist.
- Respawn, for the Apex Legends movement Apex Movement is built after.
