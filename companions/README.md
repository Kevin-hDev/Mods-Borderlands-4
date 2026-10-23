# Companions

A team of up to 8 companions, among the game's 6 Vault Hunters and 4 allies, who follow you and fight at your side.
They are [It Follows](../it_follows/)' companions in a mod of their own: you do not need It Follows to have them.

Tested on the game version of 22 October 2026 (build **4906557**) on Windows, in single player on Steam.

## What it does

Open the console with `~`, type `mods` and choose **Companions**, or press the menu key you chose in OPTIONS (none at
first). Its window, in English, French, Simplified Chinese and Japanese, has three pages. The game is paused while it is open,
except in co-op.

- **VAULT HUNTERS and ALLIES.** Choose up to 8 companions among 10, the same one several times if you like, then
  LAUNCH THE TEAM, or press the team key, F8 at first: they follow you and fight at your side. The Vault Hunters
  fight with their weapons only, without their skills. On the card of the Vault Hunter you play, their base outfit or
  your colours. A dead companion comes back near you after the time you set; the team finds you again after a fast
  travel or a change of map, and leaves when you stop it or go back to the main menu.
- **TEAM SETTINGS**, the same for every companion, kept by the team from its launch: health, ×4 your Vault Hunter's
  at first (×1 to ×20); shield, 30% of their health (0% to 100%); shield refill, NEVER at first (5 to 120 s); speed,
  +20% (0 to +50%); back after death, 45 s (10 to 120 s).
- **OPTIONS.** Health bars on the left, the menu key and the team key. With the `Companions Paks` file, each
  companion's health shows at the bottom left of the screen, and its bars in green when you aim at it, with its
  name for a Vault Hunter.

The **ENABLED** button, at the bottom left of the window, turns the whole mod on or off.

## With It Follows

Both mods carry the same companions' code, [characters](../characters/). Only one team runs at a time: while It
Follows is enabled, it runs the team, and Companions' window says so. Disable It Follows in the mods menu to go back
to Companions, without restarting the game. Companions needs It Follows 1.0.11 or later: beside an older one, even
disabled, it starts no team and asks to update it. Both mods use the same two `.pak` files for the bars.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copy `companions.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. For the health bars, copy the two `.pak` files of the `Companions Paks` file, on Nexus, into
   `...\Borderlands 4\OakGame\Content\Paks\`.
4. Launch the game, load your save, open the window and launch your team.

To uninstall, stop your team, then delete `companions.sdkmod`, and the two `it-follows-…_999_P.pak` files unless It
Follows uses them. The mod does not touch your save.

## Tests

Run each test separately from this folder, for example `python test_session.py`. The tests replace the game's SDK
with stand-ins (`sdk_stubs.py`, `*_fixture.py`), and load the companions' code from [characters](../characters/),
beside this folder. `test_mod.py` builds the mod with no file of It Follows anywhere Python looks. Each test prints a
`RESULTAT:` line and exits with a non-zero code on failure.

## Known limits

- The companions were tested in single player only.
