"""Tests the host's part for each co-op guest (normal/coop_guests.py) on fake characters: alone, nothing looked for; a
guest found raised once, its damage taken by the level's factor without the Hardcore's and its gains by their
shares; a base the game wrote anew raised again; its place given; kept while its character is a player's even when a
search misses it, given back when it is no longer a player's, a new one raised when the game holds more players, one
whose character is gone forgotten; the end gives every guest back. The Hardcore: a guest asked its percent when
raised, each told the enemies it killed, the others' kills not; its percent heard given to its damage taken on top of
the level's, once, a message of no guest held counted. And presence.others: the other players only, at most
MAX_GUESTS."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import presence  # noqa: E402
from it_follows.characters import reads  # noqa: E402
from it_follows.normal import coop_guests, levels  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Rewards:
    def __init__(self, level, announce) -> None:
        self.added = False

    def start(self, player) -> dict:
        self.added = True
        return {"shares": {"xp": 0.1}}

    def put_back(self, player) -> str:
        self.added = False
        return "gone" if player is None else "taken_back"


def character(name: str, x_m: float, player: bool = True) -> types.SimpleNamespace:
    return types.SimpleNamespace(Name=name, freed=False, at=(x_m * 100.0, 0.0, 0.0),
                                 PlayerState=object() if player else None, DamageState=types.SimpleNamespace(
                                     DamageTakenMultiplier=types.SimpleNamespace(Value=0.8, BaseValue=1.0)))


def taken(actor) -> tuple:
    pair = actor.DamageState.DamageTakenMultiplier
    return round(pair.Value, 3), round(pair.BaseValue, 3)


coop_guests.rewards.Rewards = Rewards
reads.point = lambda actor: actor.at
sys.modules["unrealsdk"].unreal.WeakPointer = lambda target: (lambda: None if target.freed else target)
count = [1]
presence.players = lambda: count[0]
crowd: list = []
looked: list = []
reads.search = lambda class_name, world=None: (looked.append(world) or list(crowd), "actors")

try:
    senior = levels.LEVELS["Senior"]
    host, guest, other = character("Host", 0.0), character("Guest", 50.0), character("Other", 900.0)
    enemy = character("OakCharacter_9", 5.0, player=False)
    crowd[:] = [host, guest, enemy, character("Default__OakCharacter", 0.0)]
    check("presence.others: the other players only", presence.others(host) == [guest] and looked == [host])
    crowd[:] = [host] + [character(f"P{number}", 0.0) for number in range(5)]
    check("presence.others: at most MAX_GUESTS", len(presence.others(host)) == presence.MAX_GUESTS)

    guests = coop_guests.CoopGuests(senior, lambda *a, **k: None)
    looked.clear()
    check("alone: nothing looked for", guests.look(host, 0.0) == {} and looked == [])
    count[0] = 2
    crowd[:] = [host, guest, enemy]
    joined = guests.look(host, 5.0)
    check("a guest found raised: the level's damage, without the Hardcore's, and its gains",
          set(joined["raised"]) == {"Guest"} and taken(guest) == (round(0.8 * senior.taken, 3), senior.taken)
          and guests.held["Guest"].gains.added and taken(host) == taken(enemy) == (0.8, 1.0))
    looked.clear()
    check("not before EVERY_S, then raised once, not looked for with every player held", not guests.due(9.0)
          and guests.due(10.0) and guests.look(host, 10.0).get("raised") == {} and taken(guest)[1] == senior.taken
          and looked == [])
    guest.DamageState.DamageTakenMultiplier.BaseValue, guest.DamageState.DamageTakenMultiplier.Value = 1.5, 1.2
    kept = guests.keep()
    check("a base the game wrote anew raised again", kept["Guest"]["taken"] == "again"
          and taken(guest)[1] == round(1.5 * senior.taken, 3))
    check("its place given", guests.places() == [guest.at])
    crowd[:] = [host, other]
    count[0] = 3
    missed = guests.look(host, 12.0)
    check("kept while a player's though a search misses it; a new one raised when the game holds more players",
          set(missed["raised"]) == {"Other"} and missed["gone"] == {} and set(guests.held) == {"Guest", "Other"})
    guest.PlayerState = None
    lost = guests.look(host, 15.0)
    check("given back when its character is no longer a player's",
          lost["gone"] == {"Guest": {"taken": "restored", "gains": "taken_back"}} and taken(guest) == (1.2, 1.5))
    other.freed = True
    crowd[:] = [host]
    check("one whose character is gone forgotten", guests.look(host, 20.0)["gone"]["Other"]["taken"] == "unavailable"
          and guests.held == {})
    guest.PlayerState = object()
    crowd[:] = [host, guest]
    count[0] = 2
    guests.look(host, 25.0)
    check("the end gives every guest back", guests.end() == {"Guest": {"taken": "restored", "gains": "taken_back"}}
          and taken(guest) == (1.2, 1.5) and guests.held == {})

    told: list = []
    pc = types.SimpleNamespace(ClientMessage=lambda text, kind, life: told.append(text))
    hunter = character("Hunter", 10.0)
    hunter.Controller = pc
    crowd[:] = [host, hunter]
    hard = coop_guests.CoopGuests(senior, lambda *a, **k: None)
    raised = hard.look(host, 0.0)
    check("a guest asked its percent when raised", raised["raised"]["Hunter"]["asked"] == "told"
          and told[0] == "ItFollows:ask")
    told.clear()
    asked = [hard.look(host, 5.0 * step).get("asked_again") for step in range(1, coop_guests.SAID_ASKS + 3)]
    check("asked again every EVERY_S until it answers, said SAID_ASKS times",
          told.count("ItFollows:ask") == coop_guests.SAID_ASKS + 2
          and told.count(f"ItFollows:run {round(senior.speed * 1000)}") == coop_guests.SAID_ASKS + 2
          and asked == [{"Hunter": "told"}] * coop_guests.SAID_ASKS + [None, None])
    check("each told the enemies it killed, the others' kills not",
          hard.kills({"Hunter": 3, "Char_Raider": 2}) == {"Hunter": 3} and told[-1] == "ItFollows:kills 3")
    base = hunter.DamageState.DamageTakenMultiplier.BaseValue
    done = hard.heard([(lambda: pc, 7), (lambda: object(), 2)])
    check("its percent heard given to its damage taken on top of the level's; a message of no guest counted",
          done["Hunter"]["percent"] == 7 and done["unknown"] == 1
          and abs(hunter.DamageState.DamageTakenMultiplier.BaseValue - 1.0 * senior.taken * 1.07) < 1e-6
          and base == senior.taken)
    check("the same percent heard again changes nothing", hard.heard([(lambda: pc, 7)]) == {})
    told.clear()
    check("answered, never asked again; the host's run told every EVERY_S", hard.look(host, 100.0) == {}
          and told == [f"ItFollows:run {round(senior.speed * 1000)}"])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
