"""Tests whom an enemy targets and the hunter imposed as its target: the primary target reads none, player, other or
unavailable, and someone else is given itself; two wrappers of one object are the same character; a character is
alive only when the game says so, each reason kept; the imposed target goes through AISetScriptedTarget without
restrictions, owned before the call, read back, never over another script's target, never while the enemy or the
hunter is not alive; it is cleared only while it is still ours, never on an expired enemy, left owned while the
enemy is inactive or the clearing is not read back; the release announces the clearing first, calls nothing on a body
the game reuses, and says its error kind."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402
from sdk_stubs import FakeWeak  # noqa: E402

state = sdk_stubs.install()

import chaser_fixture  # noqa: E402
from chaser_fixture import character  # noqa: E402

game = chaser_fixture.Game(state)

from characters import target  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def raised(act: object, error: type) -> bool:
    try:
        act()
    except error:
        return True
    return False


def patch_on(enemy: object, hunter: object) -> target.TargetPatch:
    return target.imposed(FakeWeak(enemy), FakeWeak(hunter))


try:
    hunter, enemy, other = character(1), character(2), character(3)

    check("an enemy at rest targets nobody", target.primary(enemy, hunter) == "none")
    game.primary[2] = character(1)
    check("another wrapper of the hunter reads as the player", target.primary(enemy, hunter) == "player")
    game.primary[2] = other
    check("any other character reads as other", target.primary(enemy, hunter) == "other")
    check("aimed says other, and its class when it can be read", target.aimed(enemy, hunter) == "other:unreadable")
    game.primary[2] = types.SimpleNamespace(_get_address=lambda: 4,
                                            Class=types.SimpleNamespace(Name="OakVehicle" + "_C" * 30))
    check("the class is cut to MAX_TEXT", target.aimed(enemy, hunter) == "other:" + ("OakVehicle" + "_C" * 30)[:40]
          and target.primary(enemy, hunter) == "other")
    game.primary[2] = character(1)
    check("aimed reads the player as primary does", target.aimed(enemy, hunter) == "player")
    game.primary.pop(2)
    check("and nobody", target.aimed(enemy, hunter) == "none")
    check("aimed_at gives no target for nobody", target.aimed_at(enemy, hunter) == ("none", None))
    game.primary[2] = character(1)
    check("nor for the player", target.aimed_at(enemy, hunter) == ("player", None))
    game.primary[2] = other
    check("aimed_at gives someone else itself, with what aimed says",
          target.aimed_at(enemy, hunter) == ("other:unreadable", other))
    check("two wrappers of one object are the same character, two objects are not",
          target.same(character(1), hunter) and not target.same(other, hunter))
    check("a character without an address, or none, is never the player",
          target.same(object(), hunter) is False and target.same(None, hunter) is False
          and target.same(hunter, None) is False)
    library = state["classes"].pop("GbxTargetingFunctionLibrary")
    check("the library held through a weak pointer: found once, not looked for again",
          target.primary(enemy, hunter) != "unavailable" and isinstance(target._held["library"], FakeWeak))
    target._held["library"] = None
    check("when the game does not answer the target is unavailable", target.primary(enemy, hunter) == "unavailable"
          and target.aimed_at(enemy, hunter) == ("unavailable", None))
    state["classes"]["GbxTargetingFunctionLibrary"] = library
    game.primary.clear()

    check("a live character is alive", target.live_status(enemy) == "alive" and target.live(enemy))
    check("none is expired", target.live_status(None) == "expired" and not target.live(None))
    for value, reason in ((True, "dead"), (None, "health_unknown"), (0, "health_unknown"), (1, "health_unknown")):
        check(f"a death read as {value!r} is {reason}, never alive",
              target.live_status(character(5, value)) == reason and not target.live(character(5, value)))
    rootless = character(5)
    rootless.RootComponent = None
    check("without a root it is not alive", target.live_status(rootless) == "root_missing")

    class Unreadable:
        def __init__(self, health: bool) -> None:
            if health:
                self.HealthState = types.SimpleNamespace(bCurrentlyDead=False)

    check("a health that cannot be read says so", target.live_status(Unreadable(False)) == "health_read_failed"
          and not target.live(Unreadable(False)))
    check("a root that cannot be read says so", target.live_status(Unreadable(True)) == "root_read_failed")

    game.reset()
    patch = patch_on(enemy, hunter)
    check("a patch never applied restores nothing", patch.restore() == "inactive" and game.log == [])
    patch.apply()
    check("the player is imposed on the enemy without restrictions, owned, and read back",
          game.log == [("set", enemy, hunter, False)] and patch.pending and patch.read() == "player"
          and all(patch.verify() for _ in range(100)))
    check("applied once, it is refused a second time without a call",
          raised(patch.apply, ValueError) and len(game.log) == 1 and patch.pending)
    check("cleared while still ours", patch.restore() == "restored" and game.log[-1] == ("clear", enemy)
          and 2 not in game.imposed and not patch.pending)
    check("restored, it has nothing more to restore", patch.restore() == "inactive" and len(game.log) == 2)

    game.reset()
    game.imposed[2] = other
    refused = patch_on(enemy, hunter)
    check("another script's target is never replaced",
          raised(refused.apply, ValueError) and game.imposed[2] is other and game.log == [] and not refused.pending)

    game.reset()
    replaced = patch_on(enemy, hunter)
    replaced.apply()
    game.imposed[2] = other
    check("a target replaced meanwhile by another script is not cleared",
          not replaced.verify() and replaced.restore() == "superseded" and game.imposed[2] is other
          and ("clear", enemy) not in game.log and not replaced.pending)

    game.reset()
    gone_enemy = character(6)
    expiring = patch_on(gone_enemy, hunter)
    expiring.apply()
    gone_enemy.freed = True
    check("an expired enemy is never called, the patch let go",
          not expiring.verify() and expiring.restore() == "actor_expired" and ("clear", gone_enemy) not in game.log
          and not expiring.pending)

    game.reset()
    resting = character(7)
    waiting = patch_on(resting, hunter)
    waiting.apply()
    resting.RootComponent = None
    check("an inactive enemy is not called, the patch kept to try again",
          waiting.restore() == "actor_inactive_retry_stop" and waiting.pending and ("clear", resting) not in game.log)
    resting.freed = True
    check("until it expires", waiting.restore() == "actor_expired" and not waiting.pending)

    for value in (True, None, 0):
        game.reset()
        doubtful = character(8, value)
        check(f"an enemy whose death reads {value!r} is refused before any call",
              raised(patch_on(doubtful, hunter).apply, ValueError) and game.log == [])
    game.reset()
    check("a hunter who is not alive is never imposed",
          raised(patch_on(enemy, character(1, True)).apply, ValueError) and game.log == [])
    gone_hunter = character(1)
    gone_hunter.freed = True
    check("nor one who is gone", raised(patch_on(enemy, gone_hunter).apply, ValueError) and game.log == [])

    game.reset()
    game.set_fails = "after"
    partial = patch_on(enemy, hunter)
    check("a setter that writes then raises leaves the patch owned", raised(partial.apply, RuntimeError)
          and partial.pending)
    check("so that it is cleared all the same", partial.restore() == "restored" and 2 not in game.imposed)

    game.reset()
    game.set_fails = "before"
    refusing = patch_on(enemy, hunter)
    check("a setter that refuses raises, the patch owned and nothing to clear",
          raised(refusing.apply, RuntimeError) and refusing.pending and refusing.restore() == "already_original")

    game.reset()
    unconfirmed = patch_on(enemy, hunter)
    original_set = game._set

    def set_elsewhere(*, AIActor: object, TargetActor: object, bApplyRestrictions: bool) -> None:
        game.log.append(("set", AIActor, TargetActor, bApplyRestrictions))
        game.imposed[2] = other

    state["classes"]["GbxTargetingFunctionLibrary"].ClassDefaultObject.AISetScriptedTarget = set_elsewhere
    check("a write not read back raises, the patch owned",
          raised(unconfirmed.apply, ValueError) and unconfirmed.pending)
    state["classes"]["GbxTargetingFunctionLibrary"].ClassDefaultObject.AISetScriptedTarget = original_set

    game.reset()
    silent = patch_on(enemy, hunter)
    silent.apply()
    game.clear_silent = True
    check("a clearing not read back raises, the patch still owned", raised(silent.restore, ValueError)
          and silent.pending)

    game.reset()
    cleared = patch_on(enemy, hunter)
    cleared.apply()
    game.imposed.clear()
    check("a target the game cleared is not imposed again by the same patch, nor cleared",
          not cleared.verify() and raised(cleared.apply, ValueError) and cleared.restore() == "already_original"
          and game.log == [("set", enemy, hunter, False)])

    game.reset()
    announces: list[str] = []
    never_set = patch_on(enemy, hunter)
    check("a target never imposed has nothing to release",
          target.release(never_set, False, lambda: announces.append("x")) == "inactive" and announces == []
          and target.release(None, False, lambda: announces.append("x")) == "inactive")
    ours = patch_on(enemy, hunter)
    ours.apply()
    check("on a body the game reuses the imposed target is left, nothing called, nothing announced",
          target.release(ours, True, lambda: announces.append("x")) == "not_needed" and announces == []
          and game.log == [("set", enemy, hunter, False)] and game.imposed[2] is hunter)
    check("otherwise the clearing is announced, then done",
          target.release(ours, False, lambda: announces.append(game.log[-1][0])) == "restored"
          and announces == ["set"] and game.log[-1] == ("clear", enemy))
    game.reset()
    announces.clear()
    taken_back = patch_on(enemy, hunter)
    taken_back.apply()
    game.imposed.clear()
    check("a target the game already cleared is let go without a call or an announce",
          target.release(taken_back, False, lambda: announces.append("x")) == "already_original" and announces == []
          and ("clear", enemy) not in game.log)
    failing = patch_on(enemy, hunter)
    failing.apply()
    game.imposed[2] = object()
    check("a failing release says its error kind",
          target.release(failing, False, lambda: None) == "clear_error:AttributeError")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
