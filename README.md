# Mods Borderlands 4

Movement mods for Borderlands 4, written in Python on the Borderlands 4 SDK.

| Mod | What it does | Version |
|---|---|---|
| [Apex Movement](apex_movement/) | Apex Legends style movement: auto sprint, momentum slides, air strafe, heavier falls, wall climbing | 1.0.0 |

## Installing a mod

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest). No mod here loads without it.
2. Put the mod's `.sdkmod` file into `...\Borderlands 4\sdk_mods\`
3. Launch the game, open the console with `~`, type `mods`.

Ready-made `.sdkmod` files are on Nexus Mods. A `.sdkmod` is a zip archive of the mod's package folder with its extension changed, so you can also build one yourself from the sources here.

## Reporting a problem

Open an issue, and say what you were doing when it happened, where you were, and which version of the game and of the mod you are on. A movement bug that only happens on one surface is almost impossible to find without those.

## Running the tests

Each module has its test file next to it. They need nothing installed: they replace the game's SDK with stand-in objects.

```
cd apex_movement
python test_wall_climb.py
```

Every test file prints a `RESULTAT:` line and exits with a non-zero code when something fails.

## Permissions

- Translations: allowed, tell me and I will link to yours.
- Patches or mods built on these: allowed, as long as you make the original a requirement instead of copying its code into yours, and credit it with a link.
- Reuploading these mods as they are, anywhere else: not allowed.

## Credits

- The [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager) team, without whom none of this would exist.
- Respawn, for the Apex Legends movement these mods are built after.
