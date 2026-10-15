"""Tests It Follows' one team (teams): each enemy's team read, announced first; the team most of them already have
shared, the nearest first among equals; handed to the others with the game's own handle, announced first and written
to the log; a refused handing said, that enemy keeping its team, the others still handed theirs; an enemy gone or
unread left alone; enemies drawn later handed the shared team; each enemy handed another team given back its own when
let go, but nothing called on a body the game may reuse nor on one gone, and forgotten either way; one taken away
alive has its own team set aside with the team it was handed, taken back should it come again still holding that one,
in this game or the next whichever team is shared then, given back then; no library, no change; the library held
through a weak pointer and found again once the game freed it."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import teams as teams_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


calls: list[tuple] = []
written: list[bool] = []


class Handle:
    """Stands in for the game's FGameDataHandle, shown as the SDK shows it."""

    def __init__(self, number: int, name: str) -> None:
        self.number, self.name = number, name

    def __str__(self) -> str:
        return f"FGameDataHandle({self.number}, '{self.name}', None)"


BANDIT, ORDER, BEAST = Handle(15, "Team_Bandit"), Handle(16, "Team_Order"), Handle(20, "Team_Beast")


class Library:
    """The team library's default object: reads and sets the team an actor holds; refuses or cannot read some."""

    def __init__(self) -> None:
        self.refuse: set[str] = set()
        self.unreadable: set[str] = set()
        self.used = 0

    def GetTeam(self, actor: object) -> object:
        self.used += 1
        calls.append(("get", actor.Name))
        if actor.Name in self.unreadable:
            raise RuntimeError("no team")
        return actor.team

    def SetTeam(self, actor: object, team: object) -> None:
        self.used += 1
        calls.append(("set", actor.Name, str(team)))
        if actor.Name in self.refuse:
            raise RuntimeError("refused")
        actor.team = team


def install_library() -> Library:
    made = Library()
    state["classes"]["GbxTeamFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=made)
    return made


def chaser(name: str, team: object, alive: bool = True) -> object:
    """A chaser as It Follows holds it: its name, and its enemy through a weak pointer, none once gone."""
    actor = types.SimpleNamespace(Name=name, team=team)
    return types.SimpleNamespace(name=name, actor=sdk_stubs.FakeWeak(actor if alive else None), body=actor)


def announce(call: str, log: bool = True, **fields: object) -> None:
    calls.append(("announce", call, fields.get("on"), fields.get("back", False)))
    written.append(log)


try:
    library = install_library()
    horde = [chaser("psycho", BANDIT), chaser("soldier", ORDER), chaser("beast", BEAST), chaser("raider", BANDIT)]
    teams = teams_module.Teams(announce)
    said = teams.unite(horde)
    check("each enemy's team read, then the team most of them have handed to the others, each call announced first",
          said == {"team": "Team_Bandit", "enemies": [
              {"on": "psycho", "own": "Team_Bandit", "set": "kept"},
              {"on": "soldier", "own": "Team_Order", "set": "handed"},
              {"on": "beast", "own": "Team_Beast", "set": "handed"},
              {"on": "raider", "own": "Team_Bandit", "set": "kept"}]}
          and calls[:8] == [("announce", "GetTeam", "psycho", False), ("get", "psycho"),
                            ("announce", "GetTeam", "soldier", False), ("get", "soldier"),
                            ("announce", "GetTeam", "beast", False), ("get", "beast"),
                            ("announce", "GetTeam", "raider", False), ("get", "raider")]
          and calls[8:] == [("announce", "SetTeam", "soldier", False), ("set", "soldier", str(BANDIT)),
                            ("announce", "SetTeam", "beast", False), ("set", "beast", str(BANDIT))])
    check("with the game's own handle, the very one GetTeam returned",
          horde[1].body.team is BANDIT and horde[2].body.team is BANDIT)
    check("each call to the team library is written to the log before it is made", written and all(written))

    calls.clear()
    check("let go, an enemy handed another team gets its own back, announced first; one never handed needs nothing",
          teams.give_back("soldier", horde[1].body, False) == "restored" and horde[1].body.team is ORDER
          and teams.give_back("psycho", horde[0].body, False) == "not_needed"
          and calls == [("announce", "SetTeam", "soldier", True), ("set", "soldier", str(ORDER))])
    calls.clear()
    check("nothing is called on a body the game may reuse; each given back once",
          teams.give_back("beast", horde[2].body, True) == "not_called" and calls == []
          and horde[2].body.team is BANDIT and teams.give_back("beast", horde[2].body, False) == "not_needed")

    aside = teams_module._aside
    parked = chaser("parked", BEAST)
    shared = teams_module.Teams(announce)
    shared.unite([chaser("a", BANDIT), chaser("b", BANDIT), parked])
    calls.clear()
    check("taken away alive: nothing called, its own team set aside with the team it was handed",
          shared.give_back("parked", parked.body, True, away=True) == "set_aside" and calls == []
          and parked.body.team is BANDIT and aside == {"parked": (BEAST, BANDIT)})
    joined = shared.join([parked])
    check("come again in the shared team: taken back with its own team",
          joined["enemies"] == [{"on": "parked", "own": "Team_Beast", "set": "taken_back"}]
          and shared.own == {"parked": BEAST} and aside == {})
    check("given back its own team when let go", shared.give_back("parked", parked.body, False) == "restored"
          and parked.body.team is BEAST)

    for team, outcome, back in ((BANDIT, "taken_back", "restored"), (ORDER, "handed", "restored"),
                                (BEAST, "handed", "not_needed")):
        first = teams_module.Teams(announce)
        first.unite([chaser("a", BANDIT), chaser("b", BANDIT), parked])
        first.give_back("parked", parked.body, True, away=True)
        later = teams_module.Teams(announce)
        said = later.unite([chaser("c", team), chaser("d", team), parked])
        check(f"review: set aside in one game, come again in the next sharing {team.name}: its own team given back at "
              "the end, whichever team is shared then",
              said["enemies"][-1] == {"on": "parked", "own": "Team_Beast", "set": outcome}
              and later.give_back("parked", parked.body, False) == back and parked.body.team is BEAST and aside == {})
    first = teams_module.Teams(announce)
    first.unite([chaser("a", BANDIT), chaser("b", BANDIT), parked])
    first.give_back("parked", parked.body, True, away=True)
    later = teams_module.Teams(announce)
    library.refuse = {"parked"}
    said = later.unite([chaser("c", ORDER), chaser("d", ORDER), parked])
    library.refuse = set()
    check("a handing refused to one taken back: its own team still given back when let go",
          said["enemies"][-1] == {"on": "parked", "own": "Team_Beast", "set": "call_failed:RuntimeError"}
          and later.give_back("parked", parked.body, False) == "restored" and parked.body.team is BEAST)
    first.unite([chaser("a", BANDIT), chaser("b", BANDIT), parked])
    first.give_back("parked", parked.body, True, away=True)
    parked.body.team = ORDER
    check("one that comes again holding another team than it was handed: that team is its own, the one set aside "
          "forgotten", teams_module.Teams(announce).unite([chaser("c", ORDER), parked])["enemies"][-1]
          == {"on": "parked", "own": "Team_Order", "set": "kept"} and aside == {})
    parked.body.team = BEAST
    killed = chaser("killed", ORDER)
    shared.join([killed])
    shared.give_back("killed", killed.body, True)
    killed.body.team = BANDIT
    check("a killed one's body come again in the shared team is one of the team's own: nothing set aside",
          shared.join([killed])["enemies"] == [{"on": "killed", "own": "Team_Bandit", "set": "kept"}]
          and "killed" not in shared.own)
    reborn = chaser("reborn", ORDER)
    shared.join([reborn])
    shared.give_back("reborn", reborn.body, True, away=True)
    reborn.body.team = BEAST
    shared.join([reborn])
    check("one come again in another team is handed as a new one, its old team forgotten",
          shared.own == {"reborn": BEAST} and "reborn" not in aside)
    for index in range(teams_module.ASIDE_MOST + 3):
        one = chaser(f"away_{index}", ORDER)
        shared.join([one])
        shared.give_back(one.name, one.body, True, away=True)
    check("the teams set aside bounded, the oldest forgotten first",
          len(aside) == teams_module.ASIDE_MOST and "away_0" not in aside)
    aside.clear()

    gone = teams_module.Teams(announce)
    gone.unite([chaser("a", BANDIT), chaser("b", ORDER), chaser("c", BANDIT)])
    calls.clear()
    check("nor on one gone, forgotten all the same", gone.give_back("b", None, False) == "not_called" and calls == []
          and gone.give_back("b", types.SimpleNamespace(Name="b"), False) == "not_needed" and calls == [])

    calls.clear()
    library.refuse = {"soldier"}
    library.unreadable = {"beast"}
    horde = [chaser("cat", BEAST), chaser("soldier", ORDER), chaser("beast", ORDER),
             chaser("gone", ORDER, alive=False), chaser("psycho", BANDIT)]
    teams = teams_module.Teams(announce)
    said = teams.unite(horde)
    check("among equals the nearest team is shared; a refused handing is said and that enemy keeps its team, the "
          "others still handed; an enemy gone or whose team cannot be read is left alone",
          said == {"team": "Team_Beast", "enemies": [
              {"on": "cat", "own": "Team_Beast", "set": "kept"},
              {"on": "soldier", "own": "Team_Order", "set": "call_failed:RuntimeError"},
              {"on": "beast", "own": None, "set": "call_failed:RuntimeError"},
              {"on": "gone", "own": None, "set": "gone"},
              {"on": "psycho", "own": "Team_Bandit", "set": "handed"}]}
          and horde[1].body.team is ORDER and horde[4].body.team is BEAST
          and teams.give_back("soldier", horde[1].body, False) == "not_needed")
    library.refuse, library.unreadable = set(), set()

    calls.clear()
    library.unreadable = {"a", "b"}
    check("no team read at all: nothing handed",
          teams_module.Teams(announce).unite([chaser("a", BANDIT), chaser("b", ORDER)])
          == {"team": None, "enemies": [{"on": "a", "set": "call_failed:RuntimeError"},
                                        {"on": "b", "set": "call_failed:RuntimeError"}]}
          and not [call for call in calls if call[0] == "set"])
    library.unreadable = set()

    calls.clear()
    alone = teams_module.Teams(announce)
    check("trial 6s: joining before any team is shared unites those joining",
          alone.join([chaser("a", ORDER), chaser("b", ORDER), chaser("c", BANDIT)])["team"] == "Team_Order"
          and ("set", "c", str(ORDER)) in calls)
    calls.clear()
    late = chaser("late", BEAST)
    joined = alone.join([late, chaser("same", ORDER)])
    check("then those drawn later are handed the shared team, whatever most of them have, each call announced first",
          joined == {"team": "Team_Order", "enemies": [{"on": "late", "own": "Team_Beast", "set": "handed"},
                                                        {"on": "same", "own": "Team_Order", "set": "kept"}]}
          and late.body.team is ORDER and calls.index(("announce", "SetTeam", "late", False)) < calls.index(
              ("set", "late", str(ORDER))))

    check("the library's default object is held through a weak pointer",
          isinstance(alone.library, sdk_stubs.FakeWeak) and alone.library() is library)
    library.freed = True
    fresh = install_library()
    used = library.used
    calls.clear()
    later = chaser("later", BANDIT)
    check("once the game freed it, it is found again",
          alone.join([later])["enemies"] == [{"on": "later", "own": "Team_Bandit", "set": "handed"}]
          and later.body.team is ORDER and fresh.used == 2 and library.used == used)

    crowd = [chaser(f"enemy_{index}", ORDER if index % 3 == 0 else BANDIT) for index in range(300)]
    many = teams_module.Teams(announce)
    many.unite(crowd)
    handed = len(many.own)
    for index, one in enumerate(crowd):
        many.give_back(one.name, one.body if index % 4 else None, index % 2 == 0)
    check("every enemy let go is forgotten, whatever was done: the table holds no more than the horde",
          handed == 100 and many.own == {})

    del state["classes"]["GbxTeamFunctionLibrary"]
    calls.clear()
    check("without the game's team library nothing is read nor handed, said",
          teams_module.Teams(announce).unite([chaser("a", BANDIT), chaser("b", ORDER)])["team"] is None
          and teams_module.Teams(announce).unite([chaser("a", BANDIT)])["error"].startswith("no_library")
          and calls == [])
    check("the team's name as the SDK shows the handle", teams_module.label(BANDIT) == "Team_Bandit"
          and teams_module.label("something else") == "something else")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
