# Characters

The game's characters that our mods bring into the world and lead: the companions' team, shared by
[It Follows](../it_follows/) and [Companions](../companions/). It is not a mod of its own: each of the two mods
carries a copy inside its `.sdkmod`, under its own package (`it_follows/characters/`, `companions/characters/`).

When both mods are installed, the two copies share one small state: only one team runs at a time, and It Follows
runs it while it is enabled. Two copies of different versions start no team, and both windows ask to update the two
mods.

## What is in it

- `characters/companions/`: the team, from the first companion born to the last one gone: following, fighting,
  health and shield, coming back after a death, after a fast travel or a change of map, and the health bars' service.
- The pieces the team stands on: reading the game's objects, the log, the game's thread, health and shield pools,
  aim targets, walking.
- `characters/assets/`: the names and the bars' constants both mods read.

## Tests

Run each test separately from this folder, for example `python test_companions_team.py`. The tests replace the game's
SDK with stand-ins (`sdk_stubs.py`, `*_fixture.py`), which It Follows' and Companions' tests load too. Each test prints
a `RESULTAT:` line and exits with a non-zero code on failure.
