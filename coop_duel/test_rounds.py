"""rounds.py: a round goes on while two teams or more have a player standing; a single one wins it; none, a draw."""

import sys

import sdk_stubs

sdk_stubs.install()

from coop_duel import rounds  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("two teams standing: the round goes on", rounds.outcome({1: 1, 2: 1}) == rounds.GOING)
check("three teams, two standing: it goes on", rounds.outcome({1: 1, 2: 0, 3: 2}) == rounds.GOING)
check("a single team standing wins", rounds.outcome({1: 0, 2: 2, 3: 0}) == 2)
check("one against one, the host down: the other team wins", rounds.outcome({1: 0, 2: 1}) == 2)
check("nobody standing: a draw", rounds.outcome({1: 0, 2: 0}) == rounds.DRAW)

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
