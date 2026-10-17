"""Tests the enemies' own time (normal/enemy_time.py): hooked under its own name, one look every FRAME_GAP_S at most;
a dodge sped up by the level's factor while it lasts, its own time given back at its end; given back after LONGEST_S
even if the state still says dodging, and not taken again until it says otherwise; an enemy out of the list still
given back; an enemy gone forgotten; MAX_HELD at once; a time that cannot be read said once and not retried in the
same dodge. The gestures (decisions 121 and 124): a blow, a leap or a thrown weapon sped up by the gesture's factor,
a grenade, a turret set down or a stagger not; read every GESTURE_GAP_S only, on the GESTURE_MOST nearest; a dodge
within a gesture takes the dodge's factor and gives the gesture's back, the enemy's own time kept from before both;
each script sped named once; past its LONGEST_S given back, and not taken again while that script plays, even after
a dodge; the gestures of an enemy held still read once out of the nearest; a read that fails said once; the dodges not
sped, a dodge within a gesture left to the game too, the gestures still sped. A value the game wrote meanwhile is kept
as its own. A dodge's state that cannot be read said once. A look that raises ends the mode; the stop gives every time
back and unhooks; the enemies given back stay bounded."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import frame  # noqa: E402
from it_follows.normal import enemy_time, gestures  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Scripts(list):
    fail = False

    def __iter__(self):
        if self.fail:
            raise RuntimeError("read")
        return super().__iter__()


def pawn(name: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(Name=name, freed=False,
                                 AIDodgeState=types.SimpleNamespace(ActiveDodge=types.SimpleNamespace(Action=None)),
                                 TrickData=types.SimpleNamespace(InstancedScripts=Scripts()),
                                 CustomTimeDilation=types.SimpleNamespace(BaseValue=1.0, Value=0.8))


def plays(enemy: types.SimpleNamespace, *names: str) -> None:
    enemy.TrickData.InstancedScripts[:] = [types.SimpleNamespace(Class=types.SimpleNamespace(Name=n)) for n in names]


def time_of(enemy: types.SimpleNamespace) -> tuple[float, float]:
    return enemy.CustomTimeDilation.BaseValue, enemy.CustomTimeDilation.Value


def weak(*enemies: types.SimpleNamespace) -> dict:
    return {enemy.Name: sdk_stubs.FakeWeak(enemy) for enemy in enemies}


def near(value: tuple[float, float], wanted: tuple[float, float]) -> bool:
    return abs(value[0] - wanted[0]) < 1e-9 and abs(value[1] - wanted[1]) < 1e-9


clock = {"now": 100.0}
frame.now = lambda: clock["now"]

try:
    check("a blow, a leap, a thrown weapon, a spin are sped up",
          all(gestures.sped(name) for name in ("TRAnim_Psycho_MeleeSwing_Script_Instanced_C",
                                               "TLeap_Psycho_LeapAttack_Script_Instanced_C",
                                               "TAnim_Psycho_RUpperThrow_Script_Instanced_C",
                                               "TRAnim_Psycho_ThrowMelee_Script_Instanced_C",
                                               "T_Psycho_Lunge_Script_Instanced_C", "TRAnim_Cat_LungeBite_Script_C",
                                               "TLoop_PsychoBadass_Spin_Script_Instanced_C",
                                               "TRAnim_GunToter_Rifle_Melee_Script_Instanced_C")))
    check("a grenade, a turret set down, a stagger, a retreat, a turret's shots, an effect are not",
          not any(gestures.sped(name) for name in ("TRAnim_GunToter_Rifle_ThrowGrenade_Script_Instanced_C",
                                                   "T_Cat_MeleeRetreat_Script_Instanced_C",
                                                   "TRAnim_GunToter_Rifle_ThrowTurret_Script_Instanced_C",
                                                   "TDir_Striker_Stagger_Script_Instanced_C",
                                                   "TLoop_Turret_RocketArc_Script_Instanced_C",
                                                   "CFX_Trait_Order_FFExit_Script_Instanced_C",
                                                   "Trick_CE_Digistruct_In_Script_Instanced_C")))

    lines: list[tuple[str, dict]] = []
    failures: list[str] = []
    speed = enemy_time.EnemyTime(lambda event, **f: lines.append((event, f)), 3.0, None, failures.append)
    speed.start()
    check("hooked under its own name", enemy_time.IDENTIFIER in state["hooks"]
          and enemy_time.IDENTIFIER not in ("it_follows:run", "it_follows:normal"))
    psycho, bandit = pawn("Char_Psycho"), pawn("Char_Bandit")
    speed.follow(weak(psycho, bandit))
    psycho.AIDodgeState.ActiveDodge.Action = "Dodge_Left"
    state["hooks"][enemy_time.IDENTIFIER].fn()
    check("a dodge sped up three times", near(time_of(psycho), (3.0, 2.4)) and time_of(bandit) == (1.0, 0.8)
          and speed.counts["dodge"] == 1)
    clock["now"] += 0.004
    psycho.AIDodgeState.ActiveDodge.Action = None
    state["hooks"][enemy_time.IDENTIFIER].fn()
    check("within FRAME_GAP_S no look", time_of(psycho)[0] == 3.0)
    clock["now"] += 0.01
    state["hooks"][enemy_time.IDENTIFIER].fn()
    check("its end: its own time given back", time_of(psycho) == (1.0, 0.8) and speed.held == {})
    plays(psycho, "TRAnim_Psycho_MeleeSwing_Script_Instanced_C")
    speed.look(150.0)
    check("without a gesture factor, a gesture is left to the game", time_of(psycho) == (1.0, 0.8))
    plays(psycho)

    bandit.AIDodgeState.ActiveDodge.Action = "Dodge_Back"
    speed.look(200.0)
    speed.look(200.0 + enemy_time.LONGEST_S["dodge"] + 0.1)
    check("past LONGEST_S given back though still dodging", time_of(bandit) == (1.0, 0.8))
    speed.look(205.0)
    check("and not taken again while the state says so", time_of(bandit) == (1.0, 0.8) and speed.counts["dodge"] == 2)
    bandit.AIDodgeState.ActiveDodge.Action = None
    speed.look(206.0)
    bandit.AIDodgeState.ActiveDodge.Action = "Dodge_Right"
    speed.look(207.0)
    check("its state cleared, its next dodge sped up", time_of(bandit)[0] == 3.0 and speed.counts["dodge"] == 3)
    speed.follow({})
    bandit.AIDodgeState.ActiveDodge.Action = None
    speed.look(207.2)
    check("out of the list, still given back at its end", time_of(bandit) == (1.0, 0.8) and speed.held == {})

    cat = pawn("Char_Cat")
    speed.follow(weak(cat))
    cat.AIDodgeState.ActiveDodge.Action = "Dodge"
    speed.look(210.0)
    cat.freed = True
    speed.look(210.1)
    check("an enemy gone while held is forgotten", speed.held == {})

    crowd = [pawn(f"Char_{number}") for number in range(enemy_time.MAX_HELD + 2)]
    for enemy in crowd:
        enemy.AIDodgeState.ActiveDodge.Action = "Dodge"
    speed.follow(weak(*crowd))
    speed.look(220.0)
    check("MAX_HELD at once", len(speed.held) == enemy_time.MAX_HELD)

    blind = pawn("Char_Blind")
    del blind.CustomTimeDilation
    blind.AIDodgeState.ActiveDodge.Action = "Dodge"
    speed.follow(weak(blind))
    for moment in (230.0, 230.1, 230.2):
        speed.look(moment)
    check("a time that cannot be read: said once, not retried in that dodge",
          [event for event, _ in lines] == ["normal_time_failed"] and "Char_Blind" in speed.stuck)

    stopped = speed.stop()
    check("the stop gives every time back and unhooks", stopped["hook"] == "removed" and speed.held == {}
          and all(time_of(enemy) == (1.0, 0.8) for enemy in crowd)
          and enemy_time.IDENTIFIER not in state["hooks"] and stopped["dodges"] == speed.counts["dodge"])
    check("a second stop: inactive", speed.stop()["hook"] == "inactive")

    lines.clear()
    both = enemy_time.EnemyTime(lambda event, **f: lines.append((event, f)), 3.0, 1.2, failures.append)
    psycho, bandit = pawn("Char_Psycho"), pawn("Char_Bandit")
    both.follow(weak(psycho, bandit))
    plays(psycho, "TRAnim_Psycho_MeleeSwing_Script_Instanced_C")
    plays(bandit, "TRAnim_GunToter_Rifle_ThrowGrenade_Script_Instanced_C")
    both.look(300.0)
    check("a blow sped up by the gesture's factor, a grenade left to the game",
          near(time_of(psycho), (1.2, 0.96)) and time_of(bandit) == (1.0, 0.8) and both.counts["gesture"] == 1)
    check("the script sped named once", [f["script"] for event, f in lines if event == "normal_gesture_sped"]
          == ["TRAnim_Psycho_MeleeSwing_Script_Instanced_C"])
    psycho.AIDodgeState.ActiveDodge.Action = "Dodge"
    both.look(300.01)
    check("a dodge within the gesture takes the dodge's factor", near(time_of(psycho), (3.0, 2.4)))
    psycho.AIDodgeState.ActiveDodge.Action = None
    both.look(300.02)
    check("the dodge over, the gesture's factor back, on the enemy's own time", near(time_of(psycho), (1.2, 0.96)))
    plays(psycho)
    both.look(300.03)
    check("the gesture's end not seen before GESTURE_GAP_S", near(time_of(psycho), (1.2, 0.96)))
    both.look(300.03 + enemy_time.GESTURE_GAP_S)
    check("then its own time given back", time_of(psycho) == (1.0, 0.8) and both.held == {})
    plays(psycho, "TLeap_Psycho_LeapAttack_Script_Instanced_C")
    plays(bandit, "TLeap_Psycho_LeapAttack_Script_Instanced_C")
    both.look(301.0)
    check("two enemies on a new script: it is named once", [f["script"] for event, f in lines]
          == ["TRAnim_Psycho_MeleeSwing_Script_Instanced_C", "TLeap_Psycho_LeapAttack_Script_Instanced_C"])
    both.look(301.0 + enemy_time.LONGEST_S["gesture"] + 0.1)
    check("past its LONGEST_S given back though still playing", time_of(psycho) == (1.0, 0.8)
          and both.stuck.get("Char_Psycho") == "TLeap_Psycho_LeapAttack_Script_Instanced_C")
    psycho.AIDodgeState.ActiveDodge.Action = "Dodge"
    both.look(309.2)
    psycho.AIDodgeState.ActiveDodge.Action = None
    both.look(309.21)
    check("a dodge then: sped, and the same script still playing not taken again", time_of(psycho) == (1.0, 0.8)
          and both.stuck.get("Char_Psycho") == "TLeap_Psycho_LeapAttack_Script_Instanced_C")
    far_ones = [pawn(f"Char_Far_{number}") for number in range(enemy_time.GESTURE_MOST + 1)]
    for enemy in far_ones:
        plays(enemy, "TRAnim_Psycho_MeleeSwing_Script_Instanced_C")
    both.follow(weak(*far_ones))
    both.look(320.0)
    check("only the GESTURE_MOST nearest read", sum(1 for enemy in far_ones if time_of(enemy) != (1.0, 0.8))
          == enemy_time.GESTURE_MOST and time_of(far_ones[-1]) == (1.0, 0.8))
    broken_read = pawn("Char_Unread")
    broken_read.TrickData.InstancedScripts.fail = True
    both.follow(weak(broken_read))
    for moment in (321.0, 321.1, 321.2):
        both.look(moment)
    check("a read that fails said once, the enemy left to the game",
          [f["what"] for event, f in lines if event == "normal_time_failed"] == ["gesture_read"]
          and time_of(broken_read) == (1.0, 0.8))
    check("the enemies held still read once out of the nearest, still sped",
          sum(1 for enemy in far_ones if near(time_of(enemy), (1.2, 0.96))) == enemy_time.GESTURE_MOST)
    ended = both.stop()
    check("the stop gives the gestures' times back and counts them",
          all(time_of(enemy) == (1.0, 0.8) for enemy in far_ones) and ended["gestures"] == 16)

    no_dodges = enemy_time.EnemyTime(lambda event, **f: None, None, 1.3, failures.append)
    lone = pawn("Char_Lone")
    no_dodges.follow(weak(lone))
    lone.AIDodgeState.ActiveDodge.Action = "Dodge"
    no_dodges.look(400.0)
    check("dodges not sped: a dodge left to the game", time_of(lone) == (1.0, 0.8))
    plays(lone, "T_Psycho_Melee180_Script_Instanced_C")
    no_dodges.look(401.0)
    check("a dodge within a gesture left to the game too", time_of(lone) == (1.0, 0.8))
    lone.AIDodgeState.ActiveDodge.Action = None
    no_dodges.look(402.0)
    check("and a gesture still sped up", near(time_of(lone), (1.3, 1.04)))
    lone.AIDodgeState.ActiveDodge.Action = "Dodge"
    no_dodges.look(402.01)
    check("a dodge begun within it: the enemy's own time given back", time_of(lone) == (1.0, 0.8))
    no_dodges.stop()

    kept = enemy_time.EnemyTime(lambda event, **f: None, 3.0, 1.2, failures.append)
    slowed = pawn("Char_Slowed")
    kept.follow(weak(slowed))
    plays(slowed, "TRAnim_Psycho_MeleeSwing_Script_Instanced_C")
    kept.look(500.0)
    slowed.CustomTimeDilation.Value = 0.5
    slowed.AIDodgeState.ActiveDodge.Action = "Dodge"
    kept.look(500.01)
    check("a value the game wrote meanwhile kept as its own, the new factor laid on it",
          near(time_of(slowed), (3.0, 1.5)))
    slowed.AIDodgeState.ActiveDodge.Action = None
    plays(slowed)
    kept.look(500.1)
    check("and given back as the game left it", near(time_of(slowed), (1.0, 0.5)) and kept.held == {})
    kept.stop()

    unread = enemy_time.EnemyTime(lambda event, **f: lines.append((event, f)), 3.0, 1.2, failures.append)
    odd = pawn("Char_Odd")
    del odd.AIDodgeState
    unread.follow(weak(odd))
    lines.clear()
    for moment in (600.0, 600.1):
        unread.look(moment)
    check("a dodge's state that cannot be read said once", [f["what"] for event, f in lines] == ["dodge_read"])
    unread.stop()

    many = enemy_time.EnemyTime(lambda event, **f: None, 3.0, None, failures.append)
    for number in range(enemy_time.MAX_STUCK + 5):
        many._stick(f"Char_{number}", "dodge")
    check("the enemies given back stay bounded, the oldest forgotten", len(many.stuck) == enemy_time.MAX_STUCK
          and "Char_0" not in many.stuck and f"Char_{enemy_time.MAX_STUCK + 4}" in many.stuck)

    broken = enemy_time.EnemyTime(lambda event, **f: None, 2.0, None, failures.append)
    broken.start()
    broken.watched = {"Char_Broken": None}
    clock["now"] += 1.0
    state["hooks"][enemy_time.IDENTIFIER].fn()
    check("a look that raises ends the mode", failures == ["time_error:TypeError"])
    broken.stop()
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
