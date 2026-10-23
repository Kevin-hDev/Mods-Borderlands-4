"""Tests the team with both mods' copies of this package loaded at once, as in a game with It Follows and Companions
installed (decision 69 of docs/renforts; review of 23 October 2026: the lead was only tested piece by piece). Each
copy under its mod's package, its own hook, one state of owners; each mod's session stood for by an owner that keeps
one team at most and stops it when the team asks. Companions alone: its team starts. It Follows switched on and its
team started: Companions' stopped at once, before It Follows' hook is set, one team's hook left; Companions refused
then. Companions' team running and It Follows switched on without a team: Companions' stopped at its next beat.
It Follows switched off: Companions starts again. Whatever order the two joined in, It Follows leads. No hunter in
the game: the companions wait, only the lead is played."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["pc"] = None

import characters_fixture  # noqa: E402

for mod in ("it_follows", "companions"):
    sys.modules.setdefault(mod, types.ModuleType(mod))
    characters_fixture.mount(mod)

from it_follows.characters.companions import owners as follows_owners, team as follows_team  # noqa: E402
from companions.characters.companions import owners as own_owners, team as own_team  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Clock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


class Owner:
    """A mod's session as far as the team goes."""

    def __init__(self, module: types.ModuleType, clock: Clock) -> None:
        self.module, self.clock, self.team, self.order = module, clock, None, []

    def start(self) -> str:
        team = self.module.Team(self.clock, births=types.SimpleNamespace(ask=lambda *_args: {"done": "refused"}),
                                end=lambda why: self.ended(team, why), menu=lambda: False)
        outcome = team.start(["Crankus"])
        if outcome == "started":
            self.team = team
        return outcome

    def ended(self, team: object, why: str) -> None:
        if self.team is team:
            self.stop(why)

    def stop(self, why: str = "stopped") -> None:
        team, self.team = self.team, None
        if team is not None:
            self.order.append(("stopped", why, sorted(key for key in state["hooks"] if key.endswith(":companions"))))
            team.stop(why)


def hooks() -> list[str]:
    return sorted(key for key in state["hooks"] if key.endswith(":companions"))


check("two copies, two modules, one state of owners", follows_owners is not own_owners
      and follows_owners.STATE == own_owners.STATE and follows_team.IDENTIFIER == "it_follows:companions"
      and own_team.IDENTIFIER == "companions:companions")
clock = Clock()
follows, own = Owner(follows_team, clock), Owner(own_team, clock)
own_owners.switched_on("companions")
check("Companions alone: its team starts", own.start() == "started" and hooks() == ["companions:companions"])
follows_owners.switched_on("it_follows", first=True)
check("It Follows switched on and its team started", follows.start() == "started")
check("Companions' team stopped at once, while It Follows' hook was not set yet; one team's hook left",
      own.team is None and own.order == [("stopped", "elsewhere", ["companions:companions"])]
      and hooks() == ["it_follows:companions"])
check("Companions refused while It Follows leads", own.start() == "elsewhere" and hooks() == ["it_follows:companions"])
follows.stop()
follows_owners.switched_off("it_follows")
check("It Follows switched off: Companions starts again, without a restart", own.start() == "started"
      and hooks() == ["companions:companions"])

follows_owners.switched_on("it_follows", first=True)
clock.now = 200.0
own.team.beat()
check("It Follows switched on without a team: Companions' stopped at its next beat", own.team is None
      and own.order[-1][:2] == ("stopped", "elsewhere") and hooks() == [])
follows_owners.switched_off("it_follows")
own_owners.switched_off("companions")

for first_copy, second_copy, order in ((own_owners, follows_owners, "Companions first"),
                                       (follows_owners, own_owners, "It Follows first")):
    own_owners.reset_for_tests()
    for copy in (first_copy, second_copy):
        copy.switched_on("it_follows" if copy is follows_owners else "companions", first=copy is follows_owners)
    check(f"both on ({order}): It Follows leads, in both copies", follows_owners.leads() == "it_follows"
          and own_owners.leads() == "it_follows" and own.start() == "elsewhere")
own_owners.reset_for_tests()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
