# Benefix Ohm Attack

Fire an attack beam from your hand in Borderlands 4, with six elements to choose from and damage that scales with
your level.

Tested in single player on game version **1.10.2-4845623**, with every Vault Hunter, on keyboard and on controller.
Windows only.

[Version française](README.fr.md)

## What it does

Hold the key you chose: your left hand fires an energy beam at what you aim at.

- **The beam** comes out of your left hand, with no range limit, and hits the enemy you aim at five times a second.
  It works in first and third person, weapon out or put away.
- **Six elements**: fire, shock, corrosive, cryo, radiation, or kinetic (no element, a white lightning bolt).
- **Damage that follows your level**, like a weapon's. You set its starting strength.
- **No ammo**: the attack uses its own energy, 100, shown by a new bar under your stamina bar. Empty, the beam stops;
  the energy comes back by itself after a short delay.

Open the console with `~`, type `mods`, and choose **Benefix Ohm Attack**: its menu, in English and French, has two
pages.

| Page | Setting | Values |
|---|---|---|
| BEAM | Element | Fire by default |
| BEAM | Damage per second | From 5 to 2,000, 75 by default: the value at level 1 |
| BEAM | Energy bar | Shown or hidden |
| BEAM | Energy per second | From 0 to 100, 20 by default; at 0, the energy never goes down |
| BEAM | Recharge per second | From 1 to 100, 25 by default |
| BEAM | Delay before recharge | From 0 to 10 seconds, 2 by default |
| CONTROLS | Fire the beam | Keyboard/mouse and controller |

No key is set by default: choose yours on the CONTROLS page before playing.

## Two files

The mod is released as two files on Nexus Mods:

- **Benefix Ohm Attack**, the main file: `benefix_ohm_attack.sdkmod`.
- **Benefix Ohm Attack Paks**, in the optional files: four game files. `000_BenefixOhmAttack_999_P` (`.pak`, `.ucas`,
  `.utoc`) brings the raised left hand; `pakchunk998-windows_998_P.pak` brings the energy bar.

Without the second one, the beam still works, but your left hand does not rise and the energy bar does not show.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copy `benefix_ohm_attack.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. Copy the four files of Benefix Ohm Attack Paks into `...\Borderlands 4\OakGame\Content\Paks\`.
4. Launch the game, open the mod's menu and choose your key on the CONTROLS page.

With Vortex, install both files: each one goes to its own folder by itself.

The four game files are built from the game's own files: they are not in this repository, only in the Benefix Ohm
Attack Paks file on Nexus.

## Tests

Run each test separately from this folder, for example `python test_attack.py`. The tests replace the game's SDK with
stand-ins (`sdk_stubs.py`, `*_fixture.py`). Each test prints a `RESULTAT:` line and exits with a non-zero code on
failure.

## Known limits

- Not tested in co-op, on Linux, or on Steam Deck.
- The energy bar goes through the game file that draws the stamina bar. Another mod that changes that bar may conflict
  with it. After a game update, if your stamina bar looks wrong, remove `pakchunk998-windows_998_P.pak` from the Paks
  folder until the mod is updated.
- A game update may move or rename the effects and animations the mod uses.
