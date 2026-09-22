# Apex Grapple

Version **1.0.2** — an Apex Legends inspired grapple for Borderlands 4.

Aim at a surface and pull toward it while steering in the air. Let go to carry your momentum. The mod uses the game's grapple effects and hand animation with its own pulling movement.

The grapple plays the game's launch, connection and pulling sounds. Valid contextual grapple interactions, including carryable objects, retain priority within the game's normal targeting area. Ordinary native grapple points follow the corresponding setting.

## Controls and settings

- By default, use the game's melee input, including R3 on a controller. Nearby enemies retain melee priority by default.
- Press the grapple input again, or press jump, to release. Release behavior and pull duration are configurable.
- Open **Apex Grapple** in the SDK mods menu to access the custom settings window, in the main menu or during a game.
- Adjust shooting, pulling and letting go, or restore the defaults. The window remembers your last tab when reopened, including after a game restart.
- English is the default interface language; French is available in the menu.
- In Controls, capture a keyboard, mouse or controller button directly. Extra mouse buttons are supported when reported by the game. You can also configure two buttons held together; individual buttons retain their normal action when pressed alone.
- Escape and the configured console-opening keys are reserved. PlayStation and Xbox button display styles are available, with PlayStation as the default.

## Installation

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Build the archive below, or use an Apex Grapple `.sdkmod` supplied by the author.
3. With the game closed, place `apex_grapple.sdkmod` in `Borderlands 4/sdk_mods/`.
4. Start the game and select Apex Grapple in the SDK mods menu.

Keep only one installed copy: do not leave both an `apex_grapple` folder and its `.sdkmod` archive in `sdk_mods`. Settings are saved separately by the SDK in `sdk_mods/settings/apex_grapple.json`.

## Build from source

From this directory (the one containing this README), run the following Python code. The archive must contain the inner `apex_grapple/` package, including its assets; tests and development helpers are not part of the installed mod.

```python
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

package = Path("apex_grapple")
files = sorted(package.glob("*.py"))
files += sorted(path for path in (package / "assets").iterdir() if path.is_file())
with ZipFile("apex_grapple.sdkmod", "w", ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.as_posix())
```

## Tests

Run the test scripts in separate Python processes. Most use SDK stand-ins and do not need the game running. Run them from this directory in PowerShell:

```powershell
Get-ChildItem test_*.py | ForEach-Object {
    python $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "Apex Grapple test failed" }
}
```

`test_control_console_menu.py` and `test_panel_entry.py` inspect the real SDK console menu archive. To include them, first set `BL4_SDK_MODS` to your installed `sdk_mods` directory:

```powershell
$env:BL4_SDK_MODS = 'D:\SteamLibrary\steamapps\common\Borderlands 4\sdk_mods'
```

Without that variable, those two tests explicitly skip. An invalid configured directory fails the tests. Automated tests cover settings, bindings, window lifecycle, movement logic and archive imports; visual behavior still requires checking in the game.

## Compatibility and reporting

The mod includes integration with Apex Movement and lifecycle handling for vehicles, death and session changes. Avoid combining it with another mod that replaces the grapple. Multiplayer behavior is not established by the offline tests.

When reporting a problem, include your mod and game versions, other active mods, the input used, and steps to reproduce it. Mention whether it happened after loading a character, changing sessions, entering a vehicle or opening the settings window.

## License and credits

Original code: [Apache License 2.0](../LICENSE), copyright 2026 Kevin-hDev.

- [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager) by the SDK team.
- Grapple movement inspired by Apex Legends, by Respawn.
- Anton and Barlow Condensed retain their bundled [Anton license](apex_grapple/assets/OFL-Anton.txt) and [Barlow Condensed license](apex_grapple/assets/OFL-BarlowCondensed.txt), both SIL OFL 1.1.

See [CHANGELOG.md](CHANGELOG.md) for changes.
