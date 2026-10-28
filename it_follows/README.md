# It Follows

Two modes to make Borderlands 4 harder: an overhaul of the enemies in your normal game, more numerous, faster and
tougher, and a Horde mode where an endless horde follows you everywhere. And a team of companions to fight at your
side.

Tested on the game version of 22 October 2026 (build **4906557**) on Windows, in single player on Steam. The normal
mode was also tested in two-player co-op on the game's previous version, the host on Steam and the guest on Epic
Games.

## What it does

Press **F5** during the game, or open the console with `~`, type `mods` and choose **It Follows**: its window, in
English, French, Simplified Chinese and Japanese, has five pages. The game is paused while it is open. You start one mode at
a time.

- **HORDE MODE [BETA].** Press START: every enemy around you comes for you and follows you everywhere. The ones you meet
  on the way join the horde, and the ones you kill come back behind you, more and more of them. The enemies are those
  of the areas you go through. Five levels, an enemy speed bonus, BUFF and BUFF+, a time limit or none, and the most
  enemies hunting you at once, from 30 to 120. An optional starting point: one of seven places on the map, where
  START takes you behind a black screen before the run begins. A bar at the top left of the screen shows your kills, deaths, the
  horde's size, the Hardcore and the time, which stops while the game is paused. The Hardcore is always on in the
  Horde: the enemies grow 1% stronger every 100 enemies killed during the run, from 0% at each run.
- **NORMAL MODE.** Play your game as usual: the enemies you meet are more numerous, faster and tougher, dodge more often
  and faster, strike faster, and chase you farther. At Senior and Predator, armed bandits wait less between two
  melee blows. They stagger and fall less often under your shots, 15% less at Bandit, 25% at Senior and 50% at
  Predator, where the No staggers setting takes their staggers away. Enemies without a shield get one, 40% of their health, which recharges at
  Predator once broken; armed enemies shoot straighter and their bullets fly faster. You get more experience from the
  enemies you kill, and more ammo and money from what you pick up; vending machines and missions are unchanged. Four
  levels, Bandit, Senior, Predator and God; God has as many enemies as Predator, far tougher but a little slower,
  and is made for playing with your companions. Bosses get the level's health, speed, shield and aim. At Senior,
  Predator and God, the Enemy speed setting makes them 15% slower for those who find them too fast.
  It is made first for starting or restarting the game from the beginning, a little like four levels of NG+, and
  still works mid-game. It stays on from one game to the next until you press STOP, and STOP gives the enemies back as
  the game made them.
- **Hardcore**, an option of the normal mode: the enemies grow 1% stronger every 100 enemies you kill, all game long.
  Only your Vault Hunter's kills count, not your companions'.
  You can pause the progress, and it is kept while the option is off.
- **COMPANIONS.** Choose up to 8 companions among 13, the 6 Vault Hunters and 7 allies, then launch the team, from
  the page or with its key, F8 at first: they follow you and fight at your side. The Vault Hunters fight with their
  weapons only, without their skills. Each one's card sets its shield, its speed and, for a Vault Hunter, its own
  outfit or your colors. A dead companion comes back near you 45 seconds later; the team finds you again after a
  fast travel or a change of map, and leaves when you stop it or go back to the main menu. With the
  `It Follows Companions Paks` file, each companion's health shows at the bottom left of the screen, and its bars in
  green when you aim at it, with its name for a Vault Hunter.
- **HISTORY.** Your last 20 Horde runs.
- **OPTIONS.** The in-game bar and its size; the Lost Loot machine up to 400 items; a 16:10 resolution in
  Fullscreen; three color profiles for brighter colors, with a preview to try them in game.

The **ENABLED** button, at the bottom left of the window, turns the whole mod on or off.

## Installing

1. Install the [Borderlands 4 Python SDK](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
2. Copy `it_follows.sdkmod` into `...\Borderlands 4\sdk_mods\`.
3. For the companions' health bars, copy the two `.pak` files of the `It Follows Companions Paks` file, on Nexus,
   into `...\Borderlands 4\OakGame\Content\Paks\`.
4. Launch the game, load your save and press F5.

To uninstall, stop the running mode with STOP and your team, then delete `it_follows.sdkmod` and the two
`it-follows-…_999_P.pak` files. The mod does not touch your save.

## Tests

Run each test separately from this folder, for example `python test_wave.py`. The tests replace the game's SDK with
stand-ins (`sdk_stubs.py`, `*_fixture.py`). The companions' code and its stand-ins live in
[characters](../characters/), which the tests load from beside this folder. Each test prints a `RESULTAT:` line and
exits with a non-zero code on failure.

## Known limits

- The Horde mode asks a lot of your PC. If the game slows down, lower Max enemies, choose a lower level or lower the
  game's graphics.
- Manage far enemies is always on for now: it will be reworked in a later version.
- The Horde mode does not start in co-op or in a vehicle; its starting point only works from the open world.
- In co-op, every player needs the mod for the normal mode to work fully.
- The companions were tested in single player only.
- [Companions](../companions/) gives the same companions without It Follows. With both enabled, It Follows runs the
  team, one team at a time; update both together.
- Another mod that changes the enemies, their number or their health may conflict with this one.
