"""teams.py without the game: the game's team each duel team gets (the host's keeps the players', the others, in their
numbers' order, Team_Hostile, Team_Bandit, Team_Order), refused past those; a team's name read on the handle the game
shows."""

import sys

import sdk_stubs

sdk_stubs.install()

from coop_duel import teams  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


PLAYERS, (HOSTILE, BANDIT, ORDER) = teams.PLAYERS_TEAM, teams.OTHER_TEAMS
check("the other teams, one per collision channel", teams.OTHER_TEAMS == ("Team_Hostile", "Team_Bandit", "Team_Order")
      and HOSTILE == teams.DUEL_TEAM)
check("two teams, whatever their sizes", teams.plan([1, 2], 1) == {1: PLAYERS, 2: HOSTILE})
check("each for themselves at four", teams.plan([1, 2, 3, 4], 1) == {1: PLAYERS, 2: HOSTILE, 3: BANDIT, 4: ORDER})
check("three teams", teams.plan([1, 3, 4], 1) == {1: PLAYERS, 3: HOSTILE, 4: BANDIT})
check("the host in team 2", teams.plan([1, 2], 2) == {1: HOSTILE, 2: PLAYERS})
check("the host in team 3, the others in their numbers' order", teams.plan([4, 1, 3], 3) == {
    1: HOSTILE, 3: PLAYERS, 4: BANDIT})
try:
    teams.plan([1, 2, 3, 4, 5], 1)
    refused = False
except ValueError:
    refused = True
check("more teams than the game's teams refused", refused)
check("a team's name read on its handle", teams.team_name("FGameDataHandle(15, 'Team_Bat', None)") == "Team_Bat")
check("no name read on anything else", teams.team_name(None) is None and teams.team_name("<unreadable>") is None)

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
