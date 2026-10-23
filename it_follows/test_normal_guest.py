"""Tests the normal mode's guest part (normal/guest_enemies.py, normal/guest.py) on fake characters. The scan: the
enemies and bosses within NEAR_M kept, nearest first; the hunter, the other players, the dead, the other kinds, the
unknown kinds, the unplaced and the far passed over, each counted by why; a death the game does not say no death.
The play: each new enemy given the level's run, read back; one whose bonus the game wrote again written again; one no
longer found given its own back; their own time never sped (trial 72: gestures sped on the guest jumped); a status
line every 30 s; the end gives every run back in one line. The Hardcore: nothing told before the host asks; asked,
the percent told; each kill the host tells counted, a step said and the new percent told; switched off, 0 told; kept
with each status line and at the end, its door unhooked. The mode: a co-op guest's seat plays the guest's part,
said."""

import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import kinds, presence, report  # noqa: E402
from it_follows.characters import reads  # noqa: E402
from it_follows.normal import coop_messages, enemy_time, guest, guest_enemies, levels, mode, options  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes() -> list[dict]:
    lines = [json.loads(text.split(" ", 2)[2]) for text in state["info"] if text.startswith(report.PREFIX + " {")]
    state["info"].clear()
    return [line for line in lines if line["event"] != "call"]


def character(name: str, x_m: float, kind: str | None = "enemy", dead: bool | None = None,
              player: bool = False) -> types.SimpleNamespace:
    movement = types.SimpleNamespace(MaxGroundSpeedScale=types.SimpleNamespace(Value=1.0))
    return types.SimpleNamespace(Name=name, kind=kind, HealthState=types.SimpleNamespace(bCurrentlyDead=dead),
                                 PlayerState=object() if player else None, CharacterMovement=movement,
                                 at=(x_m * 100.0, 0.0, 0.0), freed=False,
                                 AIDodgeState=types.SimpleNamespace(ActiveDodge=types.SimpleNamespace(Action=None)),
                                 TrickData=types.SimpleNamespace(InstancedScripts=[]),
                                 CustomTimeDilation=types.SimpleNamespace(BaseValue=1.0, Value=1.0))


def bonus(actor: types.SimpleNamespace) -> float:
    return actor.CharacterMovement.MaxGroundSpeedScale.Value


reads.point = lambda actor: actor.at
reads.definition = lambda actor: actor.kind
kinds.kind = lambda name: None if name is None else (name, True)
crowd: list = []
reads.search = lambda class_name, world=None: (list(crowd), "actors")
sys.modules["unrealsdk"].unreal.WeakPointer = lambda target: (lambda: None if target.freed else target)

try:
    hunter = character("OakCharacter_1", 0.0, player=True)
    near, boss, unsaid = character("OakCharacter_2", 20.0), character("OakCharacter_3", 10.0, "boss"), \
        character("OakCharacter_4", 30.0, dead=False)
    crowd[:] = [hunter, near, boss, unsaid, character("OakCharacter_5", 5.0, player=True),
                character("OakCharacter_6", 5.0, dead=True), character("OakCharacter_7", 5.0, "other"),
                character("OakCharacter_8", 5.0, None), character("OakCharacter_9", guest_enemies.NEAR_M + 1.0)]
    unplaced = character("OakCharacter_10", 0.0)
    unplaced.at = None
    crowd.append(unplaced)
    found, left = guest_enemies.scan(hunter, hunter.at)
    check("the enemies and bosses near kept, nearest first, a death not said no death",
          [name for _, name, _ in found] == ["OakCharacter_3", "OakCharacter_2", "OakCharacter_4"])
    check("the others passed over, each counted by why",
          left == {"way": "actors", "self": 1, "player": 1, "dead": 1, "other": 1, "unknown_kind": 1, "far": 1,
                   "unplaced": 1})

    predator = levels.LEVELS["Predator"]
    notes()
    play = guest.GuestPlay(options.Settings(predator, False), hunter, lambda reason: fails.append(reason))
    play.begin(100.0)
    check("each new enemy given the level's run, read back", bonus(near) == bonus(boss) == bonus(unsaid)
          == predator.speed and set(play.held) == {"OakCharacter_2", "OakCharacter_3", "OakCharacter_4"})
    looked = [line for line in notes() if line["event"] == "normal_guest_enemies"]
    check("what was done said", looked and looked[0]["sped"] == 3 and looked[0]["held"] == 3
          and looked[0]["left"]["player"] == 1)
    check("their own time never sped: nothing looks at each image", enemy_time.IDENTIFIER not in state["hooks"]
          and not hasattr(play, "watch"))
    near.CharacterMovement.MaxGroundSpeedScale.Value = 1.0
    crowd.remove(unsaid)
    play.tick(102.0)
    check("nothing before EVERY_S", bonus(near) == 1.0)
    play.tick(105.0)
    looked = [line for line in notes() if line["event"] == "normal_guest_enemies"]
    check("a bonus the game wrote again written again; one no longer found given its own back",
          bonus(near) == predator.speed and bonus(unsaid) == 1.0 and "OakCharacter_4" not in play.held
          and looked[-1]["again"] == 1 and looked[-1]["given_back"] == {"restored": 1})
    play.tick(130.0)
    status = [line for line in notes() if line["event"] == "normal_guest_status"]
    check("a status line every 30 s", len(status) == 1 and status[0]["held"] == 2)
    play.end("stopped")
    ended = [line for line in notes() if line["event"] == "normal_given_back"]
    check("the end gives every run back in one line", bonus(near) == bonus(boss) == 1.0
          and play.held == {} and ended[0]["guest"] is True and ended[0]["speed"] == {"restored": 2})
    record = {"kills": 591, "state": "on", "saved": []}
    guest.hardcore = types.SimpleNamespace(
        state=lambda: record["state"], percent=lambda: record["kills"] // 100, kills=lambda: record["kills"],
        save=lambda why: record["saved"].append(why) or True,
        count=lambda dead: (record.__setitem__("kills", record["kills"] + dead)
                            or (record["kills"] // 100 if (record["kills"] - dead) // 100 != record["kills"] // 100
                                else None)))
    sent: list = []
    state["pc"] = types.SimpleNamespace(ServerSetSpectatorLocation=lambda where, turn: sent.append(where.Y))
    hard = guest.GuestPlay(options.Settings(predator, False), hunter, fails.append)
    hard.begin(300.0)
    door = state["hooks"][coop_messages.IDENTIFIER].fn
    hard.tick(301.0)
    check("nothing told before the host asks", sent == [])
    door(None, types.SimpleNamespace(S="ItFollows:ask"), None, None)
    hard.tick(302.0)
    check("asked, the percent told", sent == [5.0])
    door(None, types.SimpleNamespace(S="ItFollows:kills 8"), None, None)
    hard.tick(303.0)
    check("a kill the host tells counted, no step, nothing told", record["kills"] == 599 and sent == [5.0])
    door(None, types.SimpleNamespace(S="ItFollows:kills 1"), None, None)
    hard.tick(304.0)
    check("a step said and the new percent told", record["kills"] == 600 and sent == [5.0, 6.0]
          and any(line["event"] == "normal_hardcore_step" for line in notes()))
    door(None, types.SimpleNamespace(S="ItFollows:run 1200"), None, None)
    hard.tick(304.5)
    check("the host's run followed at once, on the enemies held", bonus(near) == 1.2 and hard.speed.factor == 1.2
          and any(line["event"] == "normal_guest_run" for line in notes()))
    door(None, types.SimpleNamespace(S="ItFollows:run 1200"), None, None)
    hard.tick(304.6)
    check("the same run again, nothing", not any(line["event"] == "normal_guest_run" for line in notes()))
    record["state"] = "off"
    hard.tick(305.0)
    check("switched off, 0 told", sent == [5.0, 6.0, 0.0])
    hard.tick(331.0)
    hard.end("stopped")
    check("kept with each status line and at the end, its door unhooked", record["saved"] == ["status", "end"]
          and coop_messages.IDENTIFIER not in state["hooks"])
    presence.look = lambda: presence.Seat(None, hunter, "guest")
    presence.players = lambda: 2
    guest_mode = mode.Mode(options.Settings(predator, False), fails.append)
    notes()
    check("the mode: a co-op guest's seat plays the guest's part, said", guest_mode.begin(200.0) == "playing"
          and isinstance(guest_mode.play, guest.GuestPlay)
          and [line for line in notes() if line["event"] == "normal_playing"][0]["guest"] is True)
    guest_mode.end("stopped")
    check("nothing failed", fails == [])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
