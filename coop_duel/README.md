# Co-op Duel

Fight your teammates in a Borderlands 4 co-op game, 2 to 4 players, each for themselves or in teams, anywhere in the
world: endless rounds, then back up on the spot. Only the host needs the mod.

Tested on game version **1.10.2-4845623**, on Windows: the host on the Steam version, the guest on the Epic Games
version, with and without mods on the guest's side. **Tested with two players only**: the duel with 3 or 4 players has
not been tried yet. If it goes wrong for you, report it in the Bugs tab of its Nexus page with the host's log file,
`...\Borderlands 4\OakGame\Binaries\Win64\Plugins\unrealsdk.log`, copied before relaunching the game (it is rewritten
at each launch).

## What it does

- The players in the game can shoot and hurt each other, anywhere in the world: 2 to 4 players, each for themselves or
  in teams.
- The one who falls stays down, unable to be hurt, until the round ends. Their teammates can get them back up.
- The round goes to the last team with a player still standing. 3 seconds later, everyone gets back up on the spot with
  full health and shield. No death, no trip back to the respawn point.
- The duel has no end: it goes on until the host stops it.
- At each round, the score shows for a few seconds at the top of the host's screen, with the players' names.
- A player's companions attack the other team. Enemies nearby attack everyone; from 3 teams on, the bandits or the
  Order's soldiers nearby may fight alongside a team.
- When the duel stops, you are normal teammates again. It stops on its own if a player joins the game, if only one team
  is left, or on fast travel.

Your guests have nothing to install, neither the mod nor the SDK. The score only shows on the host's screen.

## Keys and window

- **F9** opens the mod's window, **N** starts the duel or stops it. Both can be changed on the OPTIONS page.
- The window, in English, French and Simplified Chinese, has three pages: DUEL, to start and stop the duel and see the
  score; TEAMS, where the host puts each player in team 1, 2, 3 or 4 (each for themselves at first, and the EACH FOR
  THEMSELVES button goes back to that); and OPTIONS, the two keys. Teams do not change during a duel. You can also open
  the window from the console: `~`, `mods`, then **Co-op Duel**.
- If the duel cannot start (no other player, everyone in the same team, a player in a vehicle or down), the mod tells
  you why and what to do.

The **ENABLED** button, at the bottom left of the window, turns the whole mod on or off.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest), on the host's
   PC.
2. Copy `coop_duel.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. Launch the game and invite friends into your game. To play in teams, arrange them on the TEAMS page (F9). Stand next
   to each other, then press N.

To uninstall, delete `coop_duel.sdkmod`. The mod does not touch your save.

## Tests

Run each test separately from this folder, for example `python test_duel.py`. The tests replace the game's SDK with
stand-ins (`sdk_stubs.py`, `game_fixture.py`, `panel_fixture.py`). Each test prints a `RESULTAT:` line and exits with a
non-zero code on failure.

## Known limits

- Tested with two players only.
- Every fall counts, even when an enemy knocked the player down.
- A host on the Epic Games version was not tested.
- Another mod that changes the players' teams may conflict with this one.
