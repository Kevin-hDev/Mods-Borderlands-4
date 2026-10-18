# It Follows

Two modes to make Borderlands 4 harder: an overhaul of the enemies in your normal game, more numerous, faster and
tougher, and a Horde mode where an endless horde follows you everywhere.

Tested on game version **1.10.2-4845623** on Windows: in single player on Steam, and the normal mode in two-player
co-op, the host on Steam and the guest on Epic Games.

## What it does

Press **F5** during the game, or open the console with `~`, type `mods` and choose **It Follows**: its window, in
English, French and Simplified Chinese, has four pages. The game is paused while it is open. You start one mode at
a time.

- **HORDE MODE [BETA].** Press START: every enemy around you comes for you and follows you everywhere. The ones you meet
  on the way join the horde, and the ones you kill come back behind you, more and more of them. The enemies are those
  of the areas you go through. Five levels, an enemy speed bonus, BUFF and BUFF+, a time limit or none, and the most
  enemies hunting you at once, from 30 to 120. A bar at the top left of the screen shows your kills, deaths, the
  horde's size, the Hardcore and the time, which stops while the game is paused. The Hardcore is always on in the
  Horde: the enemies grow 1% stronger every 100 enemies killed during the run, from 0% at each run.
- **NORMAL MODE.** Play your game as usual: the enemies you meet are more numerous, faster and tougher, dodge more often
  and faster, strike faster, and chase you farther. At Senior and Predator, armed bandits wait less between two
  melee blows. Enemies without a shield get one, 40% of their health, which recharges at
  Predator once broken; armed enemies shoot straighter and their bullets fly faster. You get more experience from the
  enemies you kill, and more ammo and money from what you pick up; vending machines and missions are unchanged. Three
  levels, Bandit, Senior and Predator. Bosses get the level's health, speed, shield and aim. At Senior and Predator,
  the Enemy speed setting makes them 15% slower for those who find them too fast.
  It is made first for starting or restarting the game from the beginning, a little like three levels of NG+, and
  still works mid-game. It stays on from one game to the next until you press STOP, and STOP gives the enemies back as
  the game made them.
- **Hardcore**, an option of the normal mode: the enemies grow 1% stronger every 100 enemies you kill, all game long.
  Only your Vault Hunter's kills count, not your companions'.
  You can pause the progress, and it is kept while the option is off.
- **HISTORY.** Your last 20 Horde runs.
- **OPTIONS.** The in-game bar and its size.

The **ENABLED** button, at the bottom left of the window, turns the whole mod on or off.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copy `it_follows.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. Launch the game, load your save and press F5.

To uninstall, stop the running mode with STOP, then delete `it_follows.sdkmod`. The mod does not touch your save.

## Tests

Run each test separately from this folder, for example `python test_wave.py`. The tests replace the game's SDK with
stand-ins (`sdk_stubs.py`, `*_fixture.py`). Each test prints a `RESULTAT:` line and exits with a non-zero code on
failure.

## Known limits

- The Horde mode asks a lot of your PC. If the game slows down, lower Max enemies, choose a lower level or lower the
  game's graphics.
- Manage far enemies is always on for now: it will be reworked in a later version.
- The Horde mode does not start in co-op or in a vehicle.
- In co-op, every player needs the mod for the normal mode to work fully.
- Another mod that changes the enemies, their number or their health may conflict with this one.
