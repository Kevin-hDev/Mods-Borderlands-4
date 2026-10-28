# Mod Settings

A MODS menu added to Borderlands 4's pause menu and main menu, in the style of the game's Options screen, to see and
set every mod of the Borderlands 4 Python SDK.

**ALPHA version**: a first version, not 100% finished. It works as it is, but it has not been tested thoroughly
enough yet, and it may not work with every mod.

Tested on game version **1.11.0-4906557**, Steam version, in single player, with keyboard, mouse and gamepad and 22
to 29 mods installed. Never tried in co-op, nor on the Epic Games version. If it goes wrong for you, first look at
[troubleshooting](TROUBLESHOOTING.md) and the [FAQ](FAQ.md), then open an issue with the log file,
`...\Borderlands 4\OakGame\Binaries\Win64\Plugins\unrealsdk.log`, copied before relaunching the game (it is
rewritten at each launch).

**Unlike the rest of this repository, Mod Settings is under the [Mozilla Public License 2.0](LICENSE).**

## What it does

- A MODS entry in the pause menu and in the main menu opens one page for every SDK mod found, built with the game's
  own Options pieces.
- Each mod has its page: its settings in tabs and sub-tabs, with the description of the chosen setting. A mod can be
  turned on or off when it allows it.
- Switches, sliders, arrow choices, lists, keys and buttons, as in the SDK console's mods menu. To change a key, click
  it, then press the new one; Escape cancels.
- A change is saved at once, except a slider's: it is saved when MODS closes, or at the next change of another
  setting. The SDK itself saves it, in `...\Borderlands 4\sdk_mods\settings\`.
- MODS' own texts follow the game's language: English, French or Simplified Chinese, English for any other language.
  The settings' names and descriptions stay as each mod gives them.

## For mod authors

You have nothing to add to your code: MODS shows the options your mod declares with `mods_base`, as the console's mods
menu does. How each option type is shown, how to lay out your options in tabs, and the limits are in the
[guide for mod authors](MOD_AUTHORS.md), also in [French](MOD_AUTHORS.fr.md), [Chinese](MOD_AUTHORS.zh.md) and
[Japanese](MOD_AUTHORS.ja.md).

## How it is made

What happens when you change a setting, and what Mod Settings touches: see [How it works](HOW_IT_WORKS.md). Two
parts, both from this folder:

- `mod_settings/`, the Python package, shipped as `mod_settings.sdkmod`. It reads the SDK's mods and options, and
  serves them to the page from a local service on `127.0.0.1` that refuses requests from web pages. Every change is
  applied on the game's own thread.
- `page/`, the page's script and stylesheet, shipped inside `mod-settings_999_P.pak` with copies of the game's pause
  menu and main menu that load them. `build_pak.py` builds that pak from the game's newest menus; `install_pak.py`
  installs or removes it with the game closed, and checks it at any time. `build_pak.py` needs two outside tools that
  read and write the game's paks; `install_pak.py` needs `deploy_sdkmods.py`, which gives it the game's folder, and
  only works on Windows. All three are named in `game_tools.py`, where they sit in the author's workshop: point them
  to your own copies. The pak holds
  the game's own files, so it is not in this repository: it ships on Nexus only.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copy `mod_settings.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. Copy `mod-settings_999_P.pak`, from the Nexus file "Mod Settings Paks", into
   `...\Borderlands 4\OakGame\Content\Paks\`. You need both files.
4. Launch the game, open the pause menu or go to the main menu, then choose MODS.

To uninstall, delete both files. The pause menu and the main menu come back as before, and your other mods' settings
do not change.

## Tests

Run each test separately from this folder: `python test_bridge.py`, and `node test_logic.js` and `node test_layout.js` for the page.
The tests replace the game's SDK with stand-ins (`fixture_sdk.py`, `fixture_world.py`, `fixture_test_mod.py`). Each
prints a `RESULTAT:` line and exits with a non-zero code on failure. The option classes and the settings save are
the SDK's own, read from an installed `mods_base.sdkmod`: set `BL4_SDK_MODS` to your `...\Borderlands 4\sdk_mods`
folder, or the tests that need them print `SKIP`. `test_page_browser.py` runs the page in headless Chrome on the
game's own interface files; without Chrome at its usual Windows place, or without the tool that reads those files
from the game's paks, it prints `SKIP`.

## Known limits

- In the main menu, Escape in MODS also opens the game's "Quit Game" window: click Cancel, or use BACK and CLOSE. In
  the pause menu, Escape works normally.
- A mod with its own settings window only shows in MODS what it declares to the SDK.
- Mod Settings itself cannot be turned off from MODS: use the SDK console (`~`, then `mods`).
- Another mod that replaces the game's pause menu or main menu may conflict. A game update may change those menus: if
  one misbehaves after an update, remove the pak until Mod Settings is updated.

## License

Mod Settings is under the Mozilla Public License 2.0: see [LICENSE](LICENSE), or <https://mozilla.org/MPL/2.0/>. If
you share changed versions of its files, they stay under MPL-2.0 and their source code must stay available. If you
reuse code, keep the notices at the top of each file: the copyright (`Copyright (c) 2026 kevin-hDev`) and the license
notice. The game files inside the pak belong to Gearbox Software and 2K and are not covered by this license.

The idea comes from Mod Settings for Cyberpunk 2077, by jackhumbert.
