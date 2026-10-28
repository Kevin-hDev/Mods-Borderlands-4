"""Tests the horde with fake pieces: the enemies another script holds left out; each enemy drawn, one refusing let go
alone; each second each enemy checked, kept, brought back unless it rides, its speed kept, what it targets read for
the wave, those brought back longest ago first; a lost enemy let go, its health given back unless the game reuses
its body, nothing called on such a body, a killed one counted and waiting to come back, every table about it
forgotten, the camp the mod made for it let go; the recruits drawn with their camps, speed, health and team, a
copy's distance told to the catch-up, a name lost less than LOST_WATCH_S ago not drawn again, the census run even
with the horde full; at the stop every enemy still drawn let go, one read dead counted killed with nothing called on
its body, each way each part was given back counted; whom an enemy targets read only within near_m; a parked enemy's
team set aside; an enemy let go since its pass began left out of its part (decision 107); 10 000 enemies passed
through the horde, no table keeps more than the horde."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import horde as horde_module  # noqa: E402

fails: list[str] = []
calls: list[tuple] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Mover:
    def __init__(self, name: str, x: float, mode: str = "MOVE_NavWalking") -> None:
        self.Name, self.x, self.freed = name, x, False
        self.HealthState = types.SimpleNamespace(bCurrentlyDead=False)
        self.CharacterMovement = types.SimpleNamespace(MovementMode=f"<EMovementMode.{mode}: 1>")

    def K2_GetActorLocation(self) -> object:
        return types.SimpleNamespace(X=self.x, Y=0.0, Z=0.0)


class FakeChaser:
    """A chaser: its check gives back the mover and the loss set on it; keep may raise; release once."""

    ARRIVAL_M = 35.0

    def __init__(self, seen: object, player_ref: object, announce: object) -> None:
        self.name, self.kind, self.mover = seen.name, seen.definition, seen.actor
        self.actor = lambda: self.mover
        self.ended = None
        self.loss: str | None = None
        self.keep_fails = False
        self.refuse = None
        held = seen.name.startswith("held")
        self.patch = types.SimpleNamespace(read=lambda: "other" if held else "none")

    @staticmethod
    def Chaser(seen: object, player_ref: object, announce: object) -> "FakeChaser":
        return FakeChaser(seen, player_ref, announce)

    def draw(self, zone: object, seen: object, goal: object, pc: object, far: bool, now: float) -> str | None:
        calls.append(("draw", self.name, far))
        return self.refuse

    def check(self, zone: object) -> tuple:
        return self.mover, self.loss

    def keep(self, to_player: object, goal: object, pc: object, impose_again: bool, now: float) -> dict:
        calls.append(("keep", self.name, impose_again))
        if self.keep_fails:
            raise RuntimeError("walk refused")
        return {}

    def release(self, zone: object, reason: str, body_reused: bool) -> dict:
        if self.ended is not None:
            return {}
        self.ended = reason
        calls.append(("release", self.name, body_reused))
        return {"order": "x", "restoration": "y", "target": "z"}


FakeChaser.Chaser = staticmethod(lambda seen, ref, announce: FakeChaser(seen, ref, announce))


class Recorder:
    """Any piece: each call it gets recorded with its name and arguments; answers set per method."""

    def __init__(self, label: str, answers: dict | None = None) -> None:
        self.label, self.answers = label, dict(answers or {})

    def __getattr__(self, method: str) -> object:
        def record(*args: object, **named: object) -> object:
            calls.append((f"{self.label}.{method}", *args, *named.values()))
            answer = self.answers.get(method)
            return answer(*args, **named) if callable(answer) else answer
        return record


def seen(name: str, x: float, kind: str = "Char_CatAdult") -> object:
    return types.SimpleNamespace(actor=Mover(name, x), name=name, definition=kind, zone=f"zone_{name}",
                                 at=(x, 0.0, 0.0))


def parts(**answers: dict) -> types.SimpleNamespace:
    camp_of: dict[str, str] = {}
    place = types.SimpleNamespace(of=camp_of, add=lambda enemy, zone: camp_of.setdefault(enemy, f"camp_{enemy}"),
                                  forget_enemy=lambda enemy: (camp_of.pop(enemy, None),
                                                              calls.append(("map.forget_enemy", enemy))))
    return types.SimpleNamespace(
        zone="zone", camp_map=place, chaser=FakeChaser, player_ref=lambda: "hunter", near_m=50.0,
        crowd_max=answers.get("crowd_max", horde_module.CROWD_MAX), manage_far=answers.get("manage_far", True),
        follow=Recorder("follow", {"place_new": lambda here: {"camp": "moved"}, **answers.get("follow", {})}),
        catch=Recorder("catch", {"queue": lambda chasers: list(chasers), **answers.get("catch", {})}),
        ground=Recorder("ground"), speed=Recorder("speed", {"start": lambda joined: [{} for _ in joined]}),
        toughness=Recorder("toughness", {"start": lambda joined: len(joined),
                                         "put_back": lambda name, actor, reused: "left" if reused else "restored"}),
        teams=Recorder("teams", {"join": lambda joined: {"team": "Team_Bandit"},
                                 "give_back": lambda *a, **k: "set_aside" if k.get("away") else "restored"}),
        wave=Recorder("wave", {"ours": lambda camp: camp in answers.get("ours", ()), "killed": lambda *a: "waiting",
                               "left_behind": lambda *a: "rejoins_near",
                               "owes": lambda camp: camp in answers.get("owed", ())}),
        stats=Recorder("stats", {"killed": lambda name: True}),
        recruiter=Recorder("recruiter", answers.get("recruiter", {})))


notes: list[tuple] = []


def note(event: str, **fields: object) -> None:
    notes.append((event, fields))


def of(label: str) -> list[tuple]:
    return [call for call in calls if call[0] == label]


try:
    pieces = parts(ours=("camp_Char_Cat_2",))
    horde = horde_module.Horde(pieces, note, lambda *a, **k: None)
    crowd = [seen("Char_Cat_1", 1000.0), seen("held_Cat", 2000.0), seen("Char_Cat_2", 9000.0)]
    free = horde.free_of(crowd)
    check("an enemy another script imposes a target on is left out", [s.name for s, _ in free]
          == ["Char_Cat_1", "Char_Cat_2"])
    check("their camps noted before they ever follow", horde.note_camps([s for s, _ in free])
          == ["camp_Char_Cat_1", "camp_Char_Cat_2"])
    taken = horde.draw_all(free, "hunter", "pc", (0.0, 0.0, 0.0), 0.0)
    check("each drawn, walked when farther than ARRIVAL_M", [c.name for c in taken] == ["Char_Cat_1", "Char_Cat_2"]
          and of("draw") == [("draw", "Char_Cat_1", False), ("draw", "Char_Cat_2", True)])
    check("decision 66: a copy tells the catch-up how far it joins, the game's enemy does not",
          of("catch.arrived") == [("catch.arrived", "Char_Cat_2", 90.0)])
    check("a copy drawn tells the wave its camp's birth joined, the game's enemy does not",
          of("wave.joined") == [("wave.joined", "camp_Char_Cat_2")])

    calls.clear()
    aimed: list[str] = []
    real_aimed = horde_module.target.aimed
    horde_module.target.aimed = lambda mover, player: (aimed.append(mover.Name), "player")[1]
    lines = horde.sample(horde.parts.catch.queue(horde.drawn()), "hunter", "pc", (0.0, 0.0, 0.0), 1.0)
    horde_module.target.aimed = real_aimed
    check("whom an enemy targets read only within near_m, the wave's count; beyond, None, never asked",
          aimed == ["Char_Cat_1"] and [line["target"] for line in lines] == ["player", None])
    check("each second each enemy kept, the hunter imposed again, considered for the catch-up, its speed kept",
          [call[:2] for call in calls if call[0] in ("keep", "catch.consider", "speed.keep")]
          == [("keep", "Char_Cat_1"), ("catch.consider", "Char_Cat_1"), ("speed.keep", "Char_Cat_1"),
              ("keep", "Char_Cat_2"), ("catch.consider", "Char_Cat_2"), ("speed.keep", "Char_Cat_2")]
          and all(call[2] is True for call in of("keep")))
    check("what each targets and how far, for the wave's count", [line["to_player_m"] for line in lines]
          == [10.0, 90.0] and all("target" in line for line in lines))
    check("the far enemies managed: none let go for its distance", not of("catch.beyond") and not of("release"))

    calls.clear()
    pass_order, kept_chasers = horde.parts.catch.queue(horde.drawn()), list(horde.chasers)
    taken[0].ended, kept_ended = "let_go_meanwhile", taken[0].ended
    lines = horde.sample(pass_order, "hunter", "pc", (0.0, 0.0, 0.0), 1.5)
    taken[0].ended, horde.chasers = kept_ended, kept_chasers
    check("decision 107: an enemy let go since its pass began is left out of its part, nothing read or called",
          len(lines) == 1 and [call[1] for call in of("keep")] == ["Char_Cat_2"])

    calls.clear()
    taken[0].mover.CharacterMovement.MovementMode = "<EMovementMode.MOVE_None: 0>"
    horde.sample(horde.parts.catch.queue(horde.drawn()), "hunter", "pc", (0.0, 0.0, 0.0), 2.0)
    check("a rider is never brought back", [call[1] for call in of("catch.consider")] == ["Char_Cat_2"])

    calls.clear()
    taken[1].loss = horde_module.KILLED
    horde.sample(horde.parts.catch.queue(horde.drawn()), "hunter", "pc", (0.0, 0.0, 0.0), 3.0)
    check("a killed one is counted, waits to come back, is let go with nothing called on its body",
          of("stats.killed") == [("stats.killed", "Char_Cat_2")]
          and of("wave.killed") == [("wave.killed", "Char_Cat_2", "Char_CatAdult")]
          and of("release") == [("release", "Char_Cat_2", True)]
          and [call[:2] for call in calls if call[0] in ("teams.give_back", "speed.put_back")]
          == [("teams.give_back", "Char_Cat_2"), ("speed.put_back", "Char_Cat_2")])
    check("its health only remembered, its body being the game's again",
          [(call[1], call[3]) for call in of("toughness.put_back")] == [("Char_Cat_2", True)]
          and notes[-1][1]["health"] == "left")
    check("every table about it forgotten, the camp the mod made for it let go",
          ("catch.forget", "Char_Cat_2") in calls and ("ground.forget", "Char_Cat_2") in calls
          and ("map.forget_enemy", "Char_Cat_2") in calls and ("follow.release", "camp_Char_Cat_2") in calls
          and "Char_Cat_2" not in pieces.camp_map.of)
    check("the loss written down", notes[-1][0] == "lost" and notes[-1][1]["on"] == "Char_Cat_2"
          and notes[-1][1]["reason"] == horde_module.KILLED and notes[-1][1]["respawn"] == "waiting"
          and notes[-1][1]["copy"] is True)
    check("a lost enemy leaves the horde at once", [c.name for c in horde.drawn()] == ["Char_Cat_1"]
          and [c.name for c in horde.chasers] == ["Char_Cat_1"])

    calls.clear()
    taken[0].mover.CharacterMovement.MovementMode = "<EMovementMode.MOVE_NavWalking: 1>"
    taken[0].loss = "zone_changed_by_game"
    horde.sample(horde.parts.catch.queue(horde.drawn()), "hunter", "pc", (0.0, 0.0, 0.0), 4.0)
    check("an enemy the game gave another zone is let go, calls allowed on its body, not counted killed",
          of("release") == [("release", "Char_Cat_1", False)] and not of("stats.killed") and not of("wave.killed")
          and not of("follow.release"))
    check("its health given back, its body still its own",
          [(call[1], call[3]) for call in of("toughness.put_back")] == [("Char_Cat_1", False)]
          and notes[-1][1]["health"] == "restored")

    pieces = parts(recruiter={"choose": lambda player, here, taken, room, known, keep: (
        [seen("Char_Cat_1", 500.0), seen("Char_Cat_9", 700.0)], {"read": 3, "kept": 2, "skipped": {},
                                                                 "stopped": "complete", "took_ms": 1.0},
        types.SimpleNamespace(alive=frozenset({"Char_Cat_9"}), dead=frozenset()))})
    horde = horde_module.Horde(pieces, note, lambda *a, **k: None)
    horde.lost_at["Char_Cat_1"] = 10.0
    calls.clear()
    horde.recruit("hunter", "pc", (0.0, 0.0, 0.0), 15.0)
    choose = of("recruiter.choose")[0]
    check("the census is asked for as many as the horde has room for, the names lost lately taken",
          choose[3] == {"Char_Cat_1"} and choose[4] == horde_module.CROWD_MAX)
    check("and told the horde's own, read alive and no further", choose[5] == set())
    check("the recruits drawn, their camps placed, their speed, their health and their team given",
          of("follow.place_new") and of("speed.start") and of("teams.join")
          and [[c.name for c in call[1]] for call in of("toughness.start")] == [["Char_Cat_1", "Char_Cat_9"]]
          and notes[-1][0] == "recruit" and notes[-1][1]["toughened"] == 2
          and [c.name for c in horde.drawn()] == ["Char_Cat_1", "Char_Cat_9"])
    check("the copies among the drawn counted by the camp each came from, the others the game's own",
          horde.copies(lambda camp: camp == "camp_Char_Cat_9") == 1 and horde.copies(lambda camp: False) == 0
          and horde.copies(lambda camp: camp is not None) == 2)
    calls.clear()
    horde.recruit("hunter", "pc", (0.0, 0.0, 0.0), 20.0)
    check("a name lost LOST_WATCH_S ago or more is forgotten: it may be drawn again",
          of("recruiter.choose")[0][3] == {"Char_Cat_1", "Char_Cat_9"} and horde.lost_at == {})
    check("the horde's own handed to the census", of("recruiter.choose")[0][5] == {"Char_Cat_1", "Char_Cat_9"})

    full = parts(recruiter={"choose": lambda player, here, taken, room, known, keep: (
        [], {"read": 0, "kept": 0, "skipped": {}, "stopped": "complete", "took_ms": 0.0},
        types.SimpleNamespace(alive=frozenset(), dead=frozenset({"x"})))})
    crowded = horde_module.Horde(full, note, lambda *a, **k: None)
    crowded.chasers = [types.SimpleNamespace(name=f"Char_{n}", ended=None) for n in range(horde_module.CROWD_MAX)]
    calls.clear()
    sighting = crowded.recruit("hunter", "pc", (0.0, 0.0, 0.0), 1.0)
    check("with the horde full the census runs all the same, for the kills it reads, with no room",
          of("recruiter.choose")[0][4] == 0 and sighting.dead == frozenset({"x"}) and not of("follow.place_new"))

    beyond = {"beyond": lambda name, metres: metres is not None and metres > 60.0}
    far = parts(manage_far=False, catch=beyond)
    horde = horde_module.Horde(far, note, lambda *a, **k: None)
    horde.draw_all(horde.free_of([seen("Char_Near", 3000.0), seen("Char_Far", 9000.0)]), "hunter", "pc",
                   (0.0, 0.0, 0.0), 0.0)
    calls.clear()
    lines = horde.sample(horde.parts.catch.queue(horde.drawn()), "hunter", "pc", (0.0, 0.0, 0.0), 1.0)
    check("decision 97: the far enemies not managed, one the catch-up would bring back let go instead, everything "
          "given back, neither kept nor considered, and never born again (decision 98)",
          of("release") == [("release", "Char_Far", False)]
          and of("wave.left_behind") == [("wave.left_behind",)]
          and [call[1] for call in of("keep")] == ["Char_Near"]
          and [call[1] for call in of("catch.consider")] == ["Char_Near"]
          and [(call[1], call[3]) for call in of("toughness.put_back")] == [("Char_Far", False)]
          and notes[-1][1]["reason"] == horde_module.LEFT_BEHIND and notes[-1][1]["respawn"] == "rejoins_near"
          and not of("stats.killed") and len(lines) == 1)
    born = types.SimpleNamespace(actor=Mover("Char_Born", 20000.0), name="Char_Born", definition="Char_CatAdult",
                                 zone=types.SimpleNamespace(Outer=types.SimpleNamespace(Name="camp_born")),
                                 at=(20000.0, 0.0, 0.0))
    around = [seen("Char_Close", 2000.0), seen("Char_Away", 9000.0), born]
    sighted = types.SimpleNamespace(alive=frozenset(), dead=frozenset())
    said = {"read": 3, "kept": 3, "skipped": {}, "stopped": "complete", "took_ms": 0.0}
    far = parts(manage_far=False, crowd_max=50, owed=("camp_born",), catch=beyond, recruiter={
        "choose": lambda player, here, taken, room, known, keep: (
            [one for one in around if keep is None or keep(one)], said, sighted)})
    horde = horde_module.Horde(far, note, lambda *a, **k: None)
    calls.clear()
    horde.recruit("hunter", "pc", (0.0, 0.0, 0.0), 1.0)
    check("decision 97: only those within the catch-up's distance join, and the births of the mod's camps wherever "
          "they were born; decision 96: room for the run's most",
          [c.name for c in horde.drawn()] == ["Char_Close", "Char_Born"] and of("recruiter.choose")[0][4] == 50)

    pieces = parts()
    horde = horde_module.Horde(pieces, note, lambda *a, **k: None)
    taken = horde.draw_all(horde.free_of([seen("Char_A", 100.0), seen("Char_B", 200.0)]), "hunter", "pc",
                           (0.0, 0.0, 0.0), 0.0)
    taken[1].keep_fails = True
    calls.clear()
    horde.sample(horde.parts.catch.queue(horde.drawn()), "hunter", "pc", (0.0, 0.0, 0.0), 1.0)
    check("an enemy whose walk cannot be given again is let go alone, the others kept",
          of("release") == [("release", "Char_B", False)] and [c.name for c in horde.drawn()] == ["Char_A"]
          and notes[-1][1]["reason"] == "walk_again_failed:RuntimeError")
    calls.clear()
    check("at the stop every enemy still drawn is let go, each way each part was given back counted",
          horde.let_go_all("stopped") == {"released": 1, "killed": 0, "order": {"x": 1}, "restoration": {"y": 1},
                                          "target": {"z": 1}, "team": {"restored": 1}, "boost": {"None": 1},
                                          "health": {"restored": 1}}
          and of("release") == [("release", "Char_A", False)] and horde.chasers == []
          and [(call[1], call[3]) for call in of("toughness.put_back")] == [("Char_A", False)])
    ending = horde_module.Horde(parts(), note, lambda *a, **k: None)
    alive, dying, vanished = ending.draw_all(ending.free_of([seen("Char_L", 10.0), seen("Char_D", 20.0),
                                                              seen("Char_V", 30.0)]), "hunter", "pc",
                                             (0.0, 0.0, 0.0), 0.0)
    dying.mover.HealthState.bCurrentlyDead = True
    vanished.mover = None
    calls.clear()
    stopped = ending.let_go_all("stopped")
    check("audit: one killed in the stop's last second is let go as a killed one, nothing called on its body, counted",
          stopped["released"] == 3 and stopped["killed"] == 1 and of("stats.killed") == [("stats.killed", "Char_D")]
          and of("release") == [("release", "Char_L", False), ("release", "Char_D", True), ("release", "Char_V", True)]
          and [(call[1], call[3]) for call in of("toughness.put_back")]
          == [("Char_L", False), ("Char_D", True), ("Char_V", True)])
    parked = horde_module.Horde(parts(), note, lambda *a, **k: None)
    [one] = parked.draw_all(parked.free_of([seen("Char_P", 10.0)]), "hunter", "pc", (0.0, 0.0, 0.0), 0.0)
    one.loss = horde_module.PARKED
    calls.clear()
    parked.sample(parked.parts.catch.queue(parked.drawn()), "hunter", "pc", (0.0, 0.0, 0.0), 1.0)
    check("a parked enemy: nothing called on its body, its team set aside should it come again",
          of("release") == [("release", "Char_P", True)] and notes[-1][1]["team"] == "set_aside")
    refusing = horde_module.Horde(parts(), note, lambda *a, **k: None)
    free = refusing.free_of([seen("Char_R", 100.0)])
    free[0][1].refuse = "zone_not_taken"
    calls.clear()
    check("an enemy refusing to be drawn is let go alone", refusing.draw_all(free, "hunter", "pc", (0.0, 0.0, 0.0),
                                                                             0.0) == []
          and of("release") == [("release", "Char_R", False)] and notes[-1][1]["reason"] == "zone_not_taken")

    calls.clear()
    pieces = parts()
    long_run = horde_module.Horde(pieces, note, lambda *a, **k: None)
    for wave_number in range(100):
        group = long_run.draw_all(long_run.free_of([seen(f"Char_{wave_number}_{n}", 100.0) for n in range(100)]),
                                  "hunter", "pc", (0.0, 0.0, 0.0), float(wave_number))
        for chaser in group:
            chaser.loss = horde_module.KILLED
        long_run.sample(long_run.parts.catch.queue(long_run.drawn()), "hunter", "pc", (0.0, 0.0, 0.0),
                        float(wave_number) + 0.5)
        long_run._forget_lost(float(wave_number) + 0.5)
        calls.clear()
    check("10 000 enemies passed through the horde: it keeps none, its lost names only those of the last seconds",
          long_run.chasers == [] and len(long_run.lost_at) <= 100 * (horde_module.LOST_WATCH_S + 1)
          and pieces.camp_map.of == {})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
