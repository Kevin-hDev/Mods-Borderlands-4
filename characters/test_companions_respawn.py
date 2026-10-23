"""Tests the companions on their way (companions/respawn.py): called by the team, due at once, or dead, due after
the wait its mod gives that companion (It Follows: 45 s, decision 23; another wait for another companion); then
asked once the hunter may have one born: never while he is dead, not on foot, nor
SETTLE_S after his place jumped; once asked, followed by its spawner with the same health, looked for until FIND_S;
one asked a beat at most; a beat a second at most, but one asked looked for every FIND_EVERY_S in between, and
nothing else done then; refused, lost, unasked or failing: dropped, said, the others going on; MOST waiting at
most; cleared at once."""

import pathlib
import sys
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_respawn_under_test", HERE / "characters" / "companions" / "respawn.py")
module = util.module_from_spec(spec)
spec.loader.exec_module(module)


class World:
    """The hunter, the spawns asked and the follows started; what each answers, set by the test."""

    def __init__(self) -> None:
        self.now = 100.0
        self.place, self.dead, self.mode = (0.0, 0.0, 0.0), False, "MOVE_Walking"
        self.spawned: list = []
        self.started: list = []
        self.recalls_seen: list = []
        self.notes: list = []
        self.spawn_answer: dict = {"done": "asked", "spawner": "OakSpawner_1"}
        self.start_answers: list = []
        # Each companion's wait after a death, as its mod gives it; It Follows' 45 s for any other.
        self.waits: dict = {}

    def note(self, event: str, **fields: object) -> None:
        self.notes.append({"event": event, **fields})

    def look(self) -> tuple:
        return self.place, self.dead, self.mode

    def spawn(self, companion: str) -> dict:
        self.spawned.append((companion, self.now))
        if isinstance(self.spawn_answer, Exception):
            raise self.spawn_answer
        return self.spawn_answer

    def start(self, companion: str, spawner: str, times: object, recalls: int) -> dict:
        self.started.append((companion, spawner, times, self.now))
        self.recalls_seen.append(recalls)
        return self.start_answers.pop(0) if self.start_answers else {"done": "started"}

    def made(self, most: int = 8) -> object:
        return module.Respawns(self.look, self.spawn, self.start, self.note, most, lambda: self.now,
                               lambda companion: self.waits.get(companion, 45.0))

    def at(self, respawns: object, now: float) -> None:
        self.now = now
        respawns.beat()

    def said(self) -> list:
        return list(self.notes)


check("a beat a second; looked for 15 s, every 0.05 s; settled 10 s; It Follows' jump", (
      module.EVERY_S, module.FIND_S, module.FIND_EVERY_S, module.SETTLE_S, module.JUMP_M) == (
      1.0, 15.0, 0.05, 10.0, 200.0))
world = World()
respawns = world.made()
check("none waiting: nothing pending, a beat does nothing", not respawns.pending()
      and (world.at(respawns, 100.0), world.spawned)[1] == [])
respawns.died("Char_NPC_Abomination", 0.5)
check("a death said, waiting", respawns.pending() and world.said()[-1] == {
      "event": "companion_dead", "companion": "Char_NPC_Abomination", "back_in_s": 45.0})
world.at(respawns, 144.0)
world.at(respawns, 144.5)
check("not asked before 45 s, nor between beats", world.spawned == [])
world.at(respawns, 145.0)
check("asked at 45 s, said first", world.spawned == [("Char_NPC_Abomination", 145.0)]
      and {"event": "companion_asked", "companion": "Char_NPC_Abomination", "late_s": 0.0} in world.said()
      and world.started == [])
world.at(respawns, 145.04)
check("not looked for again within FIND_EVERY_S", world.started == [])
world.start_answers = [{"done": "not_found"}]
world.at(respawns, 145.05)
check("looked for between beats, by its spawner, with the same health", world.started == [
      ("Char_NPC_Abomination", "OakSpawner_1", 0.5, 145.05)] and respawns.pending())
world.at(respawns, 145.2)
check("found: followed, no longer waiting, said with the time since the death", not respawns.pending()
      and respawns.back == 1 and world.said()[-1] == {"event": "companion_back", "companion": "Char_NPC_Abomination",
                                                      "spawner": "OakSpawner_1", "after_s": 45.2})
world.at(respawns, 145.3)
check("none asked: nothing between beats", len(world.started) == 2)
world = World()
respawns = world.made()
respawns.died("A", None)
respawns.died("B", None)
world.start_answers = [{"done": "not_found"}] * 5
world.at(respawns, 145.0)
world.at(respawns, 145.05)
world.at(respawns, 145.2)
check("two due: one asked at the beat, the other not between beats though the first is looked for",
      [name for name, _at in world.spawned] == ["A"] and len(world.started) == 2)
world.at(respawns, 146.0)
check("the other asked at the next beat", [name for name, _at in world.spawned] == ["A", "B"])

world = World()
respawns = world.made()
respawns.died("A", None)
world.start_answers = [{"done": "not_found"}] * 40
for second in range(145, 161):
    world.at(respawns, float(second))
check("not found for 15 s: asked again, said, not lost", respawns.pending() and respawns.lost == 0
      and {"event": "companion_asked_again", "companion": "A", "why": "not_found", "asks": 1} in world.said()
      and module.ASKS_MOST == 2)
for second in range(161, 178):
    world.at(respawns, float(second))
check("not found again: lost after ASKS_MOST asks, said", not respawns.pending() and respawns.lost == 1
      and world.said()[-1] == {"event": "companion_lost", "companion": "A", "why": "not_found"}
      and [name for name, _at in world.spawned] == ["A", "A"])
for answer in ("team_full", "followed_already"):
    world = World()
    respawns = world.made()
    respawns.died("A", None)
    world.start_answers = [{"done": answer}]
    world.at(respawns, 145.0)
    world.at(respawns, 146.0)
    check(f"refused by the follow ({answer}): dropped at once, never asked again", not respawns.pending()
          and world.said()[-1] == {"event": "companion_lost", "companion": "A", "why": answer}
          and len(world.spawned) == 1)
for answer in ("no_zone", "no_character"):
    world = World()
    respawns = world.made()
    respawns.died("A", None)
    world.start_answers = [{"done": answer}] * 3
    for second in (145.0, 146.0, 147.0, 148.0, 149.0):
        world.at(respawns, second)
    check(f"{answer} for a moment: looked for again until found, nothing lost (review of 22 October 2026)",
          not respawns.pending() and respawns.lost == 0 and world.said()[-1]["event"] == "companion_back")
world = World()
respawns = world.made()
respawns.died("A", None)
world.at(respawns, 145.0)
real_start, respawns.start = respawns.start, lambda *_args: (_ for _ in ()).throw(RuntimeError("busy"))
world.at(respawns, 146.0)
check("a search that raises once: looked for again, not dropped", respawns.pending() and respawns.lost == 0)
respawns.start = real_start
world.at(respawns, 147.0)
check("then found and followed", not respawns.pending() and world.said()[-1]["event"] == "companion_back")

world = World()
respawns = world.made()
respawns.died("A", None)
world.spawn_answer = {"done": "refused", "at": "PushActorDef"}
world.at(respawns, 145.0)
check("a spawn without a spawner: dropped, said", not respawns.pending()
      and world.said()[-1] == {"event": "companion_lost", "companion": "A", "why": "not_asked"})
world = World()
respawns = world.made()
respawns.died("A", None)
respawns.died("B", None)
world.spawn_answer = RuntimeError("boom")
world.at(respawns, 145.0)
check("a spawn that fails: that one dropped, said, the other still waiting", respawns.pending()
      and world.said()[-1] == {"event": "companion_lost", "companion": "A", "why": "failed:RuntimeError:boom"}
      and len(world.spawned) == 1)
world.spawn_answer = {"done": "asked", "spawner": "OakSpawner_2"}
world.at(respawns, 146.0)
check("the other asked at the next beat", world.spawned[-1] == ("B", 146.0))

world = World()
respawns = world.made()
respawns.died("A", None)
respawns.died("B", None)
world.at(respawns, 145.0)
check("two due together: one asked a beat", [one[0] for one in world.spawned] == ["A"])
world.spawn_answer = {"done": "asked", "spawner": "OakSpawner_2"}
world.at(respawns, 146.0)
check("the second at the next, the first then looked for", [one[0] for one in world.spawned] == ["A", "B"]
      and world.started[0][:2] == ("A", "OakSpawner_1"))

world = World()
respawns = world.made()
respawns.died("A", None)
world.dead = True
world.at(respawns, 145.0)
world.at(respawns, 146.0)
check("the hunter dead: not asked, said once", world.spawned == []
      and [note for note in world.said() if note["event"] == "companion_waits"] == [
          {"event": "companion_waits", "companion": "A", "why": "hunter_dead"}])
world.dead = False
world.mode = "MOVE_Falling"
world.at(respawns, 147.0)
check("in the air: not asked, said", world.spawned == [] and world.said()[-1] == {
      "event": "companion_waits", "companion": "A", "why": "not_on_foot"})
world.mode = "MOVE_None"
world.at(respawns, 148.0)
check("driving: not asked", world.spawned == [])
world.mode, world.place = "MOVE_Walking", (30000.0, 0.0, 0.0)
world.at(respawns, 149.0)
check("his place jumped 300 m in a beat: not asked, said", world.spawned == []
      and world.said()[-1] == {"event": "companion_waits", "companion": "A", "why": "hunter_moved"})
world.at(respawns, 158.0)
check("not before 10 s after the jump", world.spawned == [])
world.at(respawns, 159.0)
check("then asked, said late", world.spawned == [("A", 159.0)]
      and {"event": "companion_asked", "companion": "A", "late_s": 14.0} in world.said())
world.place = None
respawns.died("B", None)
world.at(respawns, 205.0)
check("the hunter unread: not asked", world.spawned == [("A", 159.0)]
      and world.said()[-1] == {"event": "companion_waits", "companion": "B", "why": "no_hunter"})

world = World()
respawns = world.made()
respawns.died("A", None)
world.at(respawns, 145.0)
world.place = (50000.0, 0.0, 0.0)
respawns.died("B", None)
world.at(respawns, 190.0)
check("a long way walked between two asks is no jump", world.spawned[-1] == ("B", 190.0))

world = World()
respawns = world.made(most=2)
for name in ("A", "B", "C"):
    respawns.died(name, None)
check("MOST waiting at most, the next refused, said", len(respawns.waiting) == 2
      and world.said()[-1] == {"event": "companion_refused", "companion": "C", "waiting": 2})
check("cleared: none waiting, counted", respawns.clear() == 2 and not respawns.pending())

world = World()
respawns = world.made()
respawns.call("Char_NPC_Abomination", None)
check("the team's call: waiting, said, no wait", respawns.pending() and world.said()[-1] == {
      "event": "companion_called", "companion": "Char_NPC_Abomination"})
world.at(respawns, 100.0)
check("asked at once, not late", world.spawned == [("Char_NPC_Abomination", 100.0)]
      and {"event": "companion_asked", "companion": "Char_NPC_Abomination", "late_s": 0.0} in world.said())
world.at(respawns, 101.0)
check("found: said with the time since the call", world.said()[-1] == {
      "event": "companion_back", "companion": "Char_NPC_Abomination", "spawner": "OakSpawner_1", "after_s": 1.0})
world = World()
respawns = world.made(most=1)
respawns.died("A", None)
respawns.call("B", None)
check("a call past MOST: refused, said", len(respawns.waiting) == 1 and world.said()[-1] == {
      "event": "companion_refused", "companion": "B", "waiting": 1})
world = World()
world.waits = {"Crankus": 20.0}
respawns = world.made()
respawns.died("Crankus", None)
respawns.died("Abomination", None)
check("each dead one waits what its mod gives it, said", [one["due"] for one in respawns.waiting] == [120.0, 145.0]
      and [note["back_in_s"] for note in world.said()] == [20.0, 45.0])
world.at(respawns, 120.0)
check("the one given 20 s asked at 20 s, the other not yet", world.spawned == [("Crankus", 120.0)])

read = type("Read", (), {"place": staticmethod(lambda actor: (1.0, 2.0, 3.0) if actor == "hunter" else None),
                         "dead": staticmethod(lambda actor: actor != "hunter")})
check("the hunter looked at: his character's place, death and mode", module.looked(
      type("Pc", (), {"OakCharacter": "hunter"})(), read, lambda actor: f"mode of {actor}") == (
      (1.0, 2.0, 3.0), False, "mode of hunter"))
check("no player: nothing read of him", module.looked(None, read, lambda actor: actor) == (None, True, None))

LIVING = object()
fall = module.Fall()
check("trial 186: living, full health, anywhere: no end", fall.end(LIVING, False, 1.0, (500.0, 0.0, 0.0)) is None
      and not fall.downed)
check("read dead: dead", module.Fall().end(LIVING, True, 0.0, (500.0, 0.0, 0.0)) == "character_dead")
check("never downed, taken away: gone", module.Fall().end(None, None, None, None) == "character_gone")
check("never downed, at the origin: no end", module.Fall().end(LIVING, False, 0.5, (0.0, 0.0, 0.0)) is None)
check("health unread is no fall", (lambda one: (one.end(LIVING, None, None, (9.0, 0.0, 0.0)), one.downed))(
      module.Fall()) == (None, False))
fall = module.Fall()
check("downed (health 0, not dead): no end yet, seen downed", fall.end(LIVING, False, 0.0, (500.0, 0.0, 0.0)) is None
      and fall.downed)
check("downed then revived: still no end", fall.end(LIVING, False, 0.4, (520.0, 0.0, 0.0)) is None)
check("downed, then hidden at the origin: dead, its height left out", fall.end(LIVING, False, 0.0, (
      60.0, -70.0, 9000.0)) == "character_dead")
fall = module.Fall()
fall.end(LIVING, False, 0.0, (500.0, 0.0, 0.0))
check("downed, 1 m from the origin: not hidden", fall.end(LIVING, False, 0.0, (100.0, 0.0, 0.0)) is None)
check("downed, then taken away: dead", fall.end(None, None, None, None) == "character_dead")
fall = module.Fall()
fall.end(LIVING, False, 0.0, (500.0, 0.0, 0.0))
fall.end(LIVING, False, 0.4, (500.0, 0.0, 0.0))
world = World()
respawns = world.made()
respawns.call("A", None, 2)
respawns.call("B", None)
check("none asked yet: none to look for after a stop", respawns.asked() == [])
world.at(respawns, 100.0)
check("one asked, not found yet: given with its spawner and when it was asked (strays.py)",
      respawns.asked() == [("A", "OakSpawner_1", 100.0)])
world.at(respawns, 100.05)
check("a companion called back twice: its follow told so, the count going with it (team.py)",
      world.recalls_seen == [2] and not any(one["companion"] == "A" for one in respawns.waiting))
world.at(respawns, 101.0)
world.at(respawns, 101.05)
check("one never called back: told none", world.recalls_seen[-1] == 0)

check("downed, revived, then taken away: still seen downed, dead", fall.downed
      and fall.end(None, None, None, None) == "character_dead")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
