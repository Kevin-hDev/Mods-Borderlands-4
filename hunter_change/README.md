# Hunter Change

Become another Vault Hunter in your Borderlands 4 game, keeping its level, backpack and story, each hunter with their
own skill tree. Or only wear another hunter's look.

Tested in single player on game version **1.10.2-4845623**, Steam version, on Windows.

## What it does

Open the console with `~`, type `mods`, and choose **Hunter Change**: its settings window, in English and French, has
two pages.

- **APPEARANCE.** Wear another hunter's look in the game you play. It applies at once and comes back each time you load
  that game. Choose their body and head among the skins you own: BASE, PRISON or PREMIUM. You also take their height:
  your view and crosshair stand at their shoulder, as in their own game. Your hunter, skills, level and gear stay yours,
  and your save is not changed: the choice is kept in the mod's own file.
- **HUNTER.** Become another hunter in this game: same level, same backpack, same story. Each hunter keeps their own
  skill tree in each game. The first time you become a hunter in a game, their skill tree starts over with all your
  points to spend. The next times, the points you spent are still there.

The **ENABLED** button, at the bottom left of the window, turns the chosen look on or off: off, your hunter gets their
own look back and the APPEARANCE page is greyed out. The HUNTER page works either way.

## Changing hunter

**From inside a game.** Open HUNTER and click a hunter: a message says what changes. Click **RETURN TO MAIN MENU**.
The game saves and takes you to the main menu, where the mod changes the save. Wait 5 seconds, click another game,
then yours again: it shows the new hunter. Then Continue.

**At the main menu.** Select the game in the list, open the window and click a hunter: the change is made at once.
Close the window, click another game, then that one again.

The game keeps the selected game in memory, and shows its old hunter until you select it again: that is why you click
another game first.

## Your save

The HUNTER page changes your save file: its hunter, the hunter's name and the skill tree. Before each change, the mod
checks the save, keeps a backup copy of it, then writes it and reads it back. When anything is unclear, such as the
game found in several save files, it changes nothing and says why in the window.

- Backup copies, the last five of each game: `...\Borderlands 4\sdk_mods\settings\hunter_change_backups\`
- The skill trees kept for your other hunters: `...\Borderlands 4\sdk_mods\settings\hunter_change_trees.json`

With several Steam accounts on the PC, only the saves of the account Steam is connected with are used.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copy `hunter_change.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. Launch the game. The mod turns itself on the first time.

To uninstall, delete `hunter_change.sdkmod`. A hunter change stays in your save: change back first if you want your
first hunter again. Keep `hunter_change_trees.json` if you may reinstall the mod, since it holds your other hunters'
skill trees. The look chosen on APPEARANCE goes away with the mod.

## Tests

Run each test separately from this folder, for example `python test_switch.py`. The tests replace the game's SDK with
stand-ins (`sdk_stubs.py`, `fake_game.py`, `*_fixture.py`) and use invented saves in a temporary folder: no real save,
no real Steam ID. Each test prints a `RESULTAT:` line and exits with a non-zero code on failure.

## Known limits

- Tested on the Steam version only. The HUNTER page reads Steam saves; the Epic Games version has not been tried.
- Not tested in co-op, on Linux or on Steam Deck.
- Wait the 5 seconds at the main menu before clicking your game: a game selected too soon may keep its old hunter.
  Change again if it does.
- A game update may change the save format: the mod then refuses to change a save it does not fully understand, and
  says so.
