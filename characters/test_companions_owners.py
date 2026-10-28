"""Tests which mod leads the companions' team (companions/owners.py): nobody before any mod joins, and reading
creates nothing; the one mod joined leads; the one joined first=True leads whatever the order; two of a kind, by
name; leaving hands the team to the other; another mod leading is elsewhere, none leading is not; two copies of
the module, one per mod, share one state; a state of another protocol refuses joining and leaves every team
elsewhere; a real copy of another protocol, loaded before or after, raises the clash: no copy says who leads
(review of 23 October 2026: a state named after its protocol let both teams run); a name that is no package
name, and an owner beyond MOST, refused; leaving twice, or before any join, harmless. A team starting claims the
team: another mod's still running stopped at once, a stop failing said; released by its own stop only. A mod
switching on or off: joined or left, said with who leads; a refusal said with this copy's protocol, never
raised."""

import importlib
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from characters.companions import owners  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[Characters] ")) for text in state["info"]
             if text.startswith("[Characters] {")]
    return [{key: value for key, value in line.items() if key != "run"} for line in found
            if line["event"] == event]


def refused(action, copy=None) -> bool:
    """Whether action raised the Refused of that copy of the module (this test's own when none is given)."""
    try:
        action()
    except (owners if copy is None else copy).Refused:
        return True
    return False


def mounted(name: str, folder: pathlib.Path):
    """The characters' package in that folder, mounted as name.characters, its owners module given."""
    sys.modules[name] = types.ModuleType(name)
    spec = importlib.util.spec_from_file_location(f"{name}.characters", folder / "__init__.py",
                                                  submodule_search_locations=[str(folder)])
    sys.modules[f"{name}.characters"] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sys.modules[f"{name}.characters"])
    return importlib.import_module(f"{name}.characters.companions.owners")


check("the state's name carries no protocol: every later version finds it", owners.STATE ==
      "_characters_team_owners")
owners.reset_for_tests()
check("nobody leads before any mod joins", owners.leads() is None and not owners.elsewhere("companions"))
check("reading creates no state", owners.STATE not in sys.modules)
owners.leave("companions")
check("leaving before any join: harmless, still no state", owners.STATE not in sys.modules)

owners.join("companions")
check("the one mod joined leads", owners.leads() == "companions" and not owners.elsewhere("companions"))
owners.join("it_follows", first=True)
check("the one joined first=True leads, though it joined after", owners.leads() == "it_follows")
check("its team is not elsewhere; the other's is", not owners.elsewhere("it_follows")
      and owners.elsewhere("companions"))
owners.leave("it_follows")
check("the leader leaving hands the team to the other", owners.leads() == "companions")
owners.leave("it_follows")
check("leaving twice: harmless", owners.leads() == "companions")

owners.reset_for_tests()
owners.join("zeta")
owners.join("alpha")
check("two of a kind: the first by name, whatever the order", owners.leads() == "alpha")
owners.join("zeta", first=True)
check("joining again with first=True: that one leads", owners.leads() == "zeta")

owners.reset_for_tests()
other = mounted("other_mod", HERE / "characters")
check("the second copy is another module", other is not owners)
other.join("it_follows", first=True)
owners.join("companions")
check("two copies of the module share one state", owners.leads() == "it_follows" and other.leads() == "it_follows"
      and owners.elsewhere("companions"))

owners.reset_for_tests()
foreign = type(sys)("foreign")
foreign.protocol = owners.PROTOCOL + 1
foreign.owners = {}
sys.modules[owners.STATE] = foreign
check("a state of another protocol: joining refused", refused(lambda: owners.join("companions")))
check("beside it, nobody can be known to lead: every team elsewhere", owners.leads() == owners.UNKNOWN
      and owners.elsewhere("companions") and owners.elsewhere("it_follows"))
check("a state whose owners are no dict: refused too", refused(lambda: (setattr(foreign, "protocol",
      owners.PROTOCOL), setattr(foreign, "owners", []), owners.join("companions"))))

later = pathlib.Path(tempfile.mkdtemp(prefix="owners_v2_"))
shutil.copytree(HERE / "characters", later / "characters", ignore=shutil.ignore_patterns("__pycache__"))
source = (later / "characters" / "companions" / "owners.py").read_text(encoding="utf-8")
check("the copy of protocol 2 is made from this one", source.count("PROTOCOL = 1\n") == 1)
(later / "characters" / "companions" / "owners.py").write_text(source.replace("PROTOCOL = 1\n", "PROTOCOL = 2\n"),
                                                            encoding="utf-8")
second = mounted("v2_mod", later / "characters")
for first_copy, then_copy, order in ((owners, second, "1 then 2"), (second, owners, "2 then 1")):
    owners.reset_for_tests()
    first_copy.join("it_follows", first=True)
    check(f"a real copy of protocol 2 ({order}): its join refused", refused(lambda: then_copy.join("companions"),
                                                                            then_copy))
    check(f"then neither copy says who leads ({order}): no team starts in either mod", owners.leads() ==
          owners.UNKNOWN and second.leads() == owners.UNKNOWN and owners.elsewhere("it_follows")
          and second.elsewhere("it_follows") and owners.elsewhere("companions"))
shutil.rmtree(later, ignore_errors=True)

owners.reset_for_tests()
stops: list[str] = []


def companions_stop() -> None:
    stops.append("companions")


def failing() -> None:
    raise RuntimeError("stop broke")


def mine() -> None:
    pass


check("a team starting alone: nothing else stopped", owners.claim("companions", companions_stop) == []
      and stops == [])
check("another mod's team starting: the first stopped at once, before it", owners.claim(
      "it_follows", lambda: stops.append("it_follows")) == ["companions"] and stops == ["companions"])
owners.release("companions", companions_stop)
check("a team stopped already released: the other's claim kept", owners.claim("it_follows", mine) == []
      and stops == ["companions"])
owners.reset_for_tests()
owners.claim("companions", failing)
check("a stop failing: said, the team claimed anyway", owners.claim("it_follows", mine) == ["companions"]
      and notes("team_owner_stop_failed")[-1] == {"event": "team_owner_stop_failed", "owner": "companions",
                                                    "error": "RuntimeError"})
owners.reset_for_tests()
owners.claim("companions", mine)
owners.release("companions", companions_stop)
check("released by another stop than its own: kept (a later team of the same mod)",
      owners.claim("it_follows", mine) == ["companions"])
owners.reset_for_tests()
owners.claim("companions", mine)
owners.release("companions", mine)
check("released by its own stop: forgotten", owners.claim("it_follows", mine) == [])
owners.reset_for_tests()
later_state = types.ModuleType(owners.STATE)
later_state.protocol, later_state.owners, later_state.running = owners.PROTOCOL + 1, {}, {}
sys.modules[owners.STATE] = later_state
check("beside a state of another protocol: no claim, said", owners.claim("companions", mine) == []
      and notes("team_owner_refused")[-1]["owner"] == "companions")
owners.release("companions", mine)

owners.reset_for_tests()
check("a name that is no package name refused", all(refused(lambda name=name: owners.join(name)) for name in (
      "", "It Follows", "../x", None, "x" * 65, 3)))
for index in range(owners.MOST):
    owners.join(f"mod_{index}")
check("an owner beyond MOST refused", refused(lambda: owners.join("one_more")))
owners.join("mod_0", first=True)
check("one already there may join again when full", owners.leads() == "mod_0")
owners.reset_for_tests()

check("a mod switching on: joined, said with who leads", owners.switched_on("companions") is True
      and owners.switched_on("it_follows", first=True) is True and notes("team_owner_joined")[-1] == {
          "event": "team_owner_joined", "owner": "it_follows", "first": True, "leads": "it_follows"})
check("a mod switching off: left, said with who leads", owners.switched_off("it_follows") is True
      and notes("team_owner_left")[-1] == {"event": "team_owner_left", "owner": "it_follows",
                                           "leads": "companions"})
sys.modules[owners.STATE] = foreign
check("a refusal said, never raised, the name given cut short", owners.switched_on("x" * 99) is False
      and notes("team_owner_refused")[-1] == {"event": "team_owner_refused", "owner": "x" * 64,
                                              "why": "team owners state of a shape this protocol never makes",
                                              "protocol": owners.PROTOCOL}
      and owners.switched_off("companions") is False)
owners.reset_for_tests()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
