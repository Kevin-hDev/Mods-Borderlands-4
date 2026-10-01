# Apex Heirloom

An Apex Legends style heirloom for Borderlands 4, and a key to put your weapon away. Put your weapon away and your
hands bring out your heirloom, the Jakobs knife or the axe, with their own animations.

Tested in single player on game version **1.10.2-4845623**, with three different Vault Hunters, on keyboard and mouse
and on controller. Windows only.

## What it does

Two parts, each with its own switch at the top of its page in the settings window:

- **The heirloom.** With no weapon in hand, your right hand holds your heirloom, the Jakobs knife or the axe, each
  with its own animations: idle, walking, running, crouching, sliding and jumping. When your weapon comes back, your
  hands go down with it. The heirloom hides while you climb (ladder, ledge, wall) and in third person. A key of your
  choice plays its animation: your hand spins the axe, as in Apex Legends. The knife has no animation of its own yet:
  with it, the key does nothing.
- **The holster.** Hold A on keyboard (the key to the right of Tab, Q on an English keyboard) or Square on controller
  to put your weapon away. Hold or press, and the hold time from 0.2 to 1 second, are set separately for keyboard and
  controller. Drawing your weapon again is left to the game.

The HEIRLOOM page chooses the knife or the axe. The axe has eight skins, chosen with two arrows, and its blade glows,
from 1 to 5. Each heirloom keeps its own skin and size, from 50 to 150%. The heirloom has two modes. Apex plays all
the heirloom's animations. Borderlands plays ours at rest, walking and running, and the game's base animations for
the rest. The moment and speed of the draw are adjustable too. A skin or a glow shows at once; the other heirloom
settings apply at the next weapon change after leaving the menu.

Open the console with `~`, type `mods`, and choose **Apex Heirloom**: its settings window, in English and French, has
three pages, HEIRLOOM, HOLSTER and CONTROLS. The CONTROLS page sets the keyboard key and the controller button that
put your weapon away, and those that play your heirloom's animation (none by default).

## Three files

The mod is released as three files on Nexus Mods, built from the same package:

- **Apex Heirloom**: both parts.
- **Tidy Weapons**: the holster alone. Its window shows HOLSTER and CONTROLS.
- **Heirloom**: the heirloom alone. Its window shows HEIRLOOM and CONTROLS.

Only `pack.py` differs between them: it names the file and the parts it runs. Tidy Weapons and Heirloom run side by
side. A file that finds one of its parts already running in another installed file, such as the full mod next to a
separate file, stays off: the SDK log says why, and so does its window when you try to switch it on.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copy the file's `.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. For Apex Heirloom and Heirloom, also copy the twelve files `000_ApexHeirloom_999_P`, `000_HeirloomLists_999_P`,
   `000_ApexHeirloomAxe_999_P` and `000_HeirloomListsAxe_999_P` (`.pak`, `.ucas` and `.utoc`) into
   `...\Borderlands 4\OakGame\Content\Paks\`. Tidy Weapons does not need them.
4. Launch the game. The mod turns itself on the first time.

The twelve files hold the knife's and the axe's models and their animations. They are built from the game's own files,
so they are not in this repository: take them from the Nexus archive.

## Tests

Run each test separately from this folder, for example `python test_heirloom.py`. The tests replace the game's SDK
with stand-ins (`sdk_stubs.py`, `heirloom_stubs.py`, `fake_*.py`, `*_fixture.py`). Seven checks compare the mod with
the knife's definition file, kept in the author's workshop; in this repository they print `SKIP` and every other check
runs. Each test prints a `RESULTAT:` line and exits with a non-zero code on failure.

## Known limits

- Not tested in co-op, on Linux, or on Steam Deck.
- Switching from one installed file to another while the heirloom is in hand shows two heirlooms until the next
  weapon change.
- While the heirloom shows, the mod turns the game's depth of field off. A graphics setting changed at that moment may
  not reach the depth of field until the game restarts.
- A game update may move or rename the animations and materials the mod uses.
