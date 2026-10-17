# Co-op Duel

Fight your teammate in a Borderlands 4 co-op game, anywhere in the world: endless rounds, a 3 second KO on the ground,
then back up on the spot. Only the host needs the mod.

Tested on game version **1.10.2-4845623**, on Windows: the host on the Steam version, the guest on the Epic Games
version, with and without mods on the guest's side. Tested with two players only.

## What it does

- The host and their guest can shoot and hurt each other, anywhere in the world.
- The one who falls stays down for 3 seconds, unable to hurt or be hurt, then gets back up on the spot with full health
  and shield. No death, no trip back to the respawn point.
- Each fall gives the round to the other player. The duel has no end: it goes on until the host stops it.
- At each round, the score shows for a few seconds at the top of the host's screen, with both players' names.
- Enemies nearby attack both players: neither one gets allies.
- When the duel stops, you are normal teammates again. It stops on its own if the guest leaves the game, if a third
  player joins, or on fast travel.

Your guest has nothing to install, neither the mod nor the SDK. The score only shows on the host's screen.

## Keys and window

- **F9** opens the mod's window, **N** starts the duel or stops it. Both can be changed on the OPTIONS page.
- The window, in English, French and Simplified Chinese, has two pages: DUEL, to start and stop the duel and see the
  score, and OPTIONS, the two keys. You can also open it from the console: `~`, `mods`, then **Co-op Duel**.
- If the duel cannot start (no guest, a player in a vehicle or down), the mod tells you why and what to do.

The **ENABLED** button, at the bottom left of the window, turns the whole mod on or off.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest), on the host's
   PC.
2. Copy `coop_duel.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. Launch the game, invite a friend into your game, stand next to each other, then press N.

To uninstall, delete `coop_duel.sdkmod`. The mod does not touch your save.

## Tests

Run each test separately from this folder, for example `python test_duel.py`. The tests replace the game's SDK with
stand-ins (`sdk_stubs.py`, `game_fixture.py`, `panel_fixture.py`). Each test prints a `RESULTAT:` line and exits with a
non-zero code on failure.

## Known limits

- Two-player duels only for now.
- Every fall counts, even when an enemy knocked the player down.
- A host on the Epic Games version was not tested.
- Another mod that changes the players' teams may conflict with this one.
