"""Tests the one SDK hook on the animation update for every beat (audit of 24 October 2026, C2): the first beat sets
it under the mod's name, a second shares it, each called in the order it was set with the hook's arguments; a beat
removed during a call runs no more, one set during a call runs from the next; the last beat removed outside a call
removes the SDK's hook at once, during a call at its end, and not at all when another beat is set within that call; a
beat that raises is said once by its name and kind and the others still run; set again, the SDK's hook comes back."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from characters import animation_hook  # noqa: E402

fails: list[str] = []
calls: list[tuple] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def call(obj: object = None) -> None:
    state["hooks"][animation_hook.IDENTIFIER].fn(obj, "args", "ret", "func")


def failures() -> list[dict]:
    return [line for line in state["info"] if "animation_beat_failed" in line]


try:
    first = animation_hook.beat("mod:first", lambda *args: calls.append(("first", args)))
    second = animation_hook.beat("mod:second", lambda *args: calls.append(("second", args)))
    check("nothing set: no hook", not animation_hook.hooked() and animation_hook.IDENTIFIER not in state["hooks"])
    first.enable()
    check("the first beat sets the SDK's hook, under the mod's name",
          animation_hook.IDENTIFIER == "characters:animation"
          and list(state["hooks"]) == [animation_hook.IDENTIFIER] and animation_hook.hooked())
    second.enable()
    check("a second beat shares it", list(state["hooks"]) == [animation_hook.IDENTIFIER]
          and list(animation_hook.beats()) == ["mod:first", "mod:second"])
    call("anim")
    check("each beat called, in the order it was set, with the hook's arguments",
          calls == [("first", ("anim", "args", "ret", "func")), ("second", ("anim", "args", "ret", "func"))])

    calls.clear()
    third = animation_hook.beat("mod:third", lambda *args: calls.append(("third", args)))
    first.callback = lambda *args: (calls.append(("first", args)), second.disable(), third.enable())
    first.enable()
    call()
    check("a beat removed during a call runs no more, one set during a call not yet",
          [name for name, _ in calls] == ["first"] and list(animation_hook.beats()) == ["mod:first", "mod:third"])
    calls.clear()
    first.callback = lambda *args: calls.append(("first", args))
    first.enable()
    call()
    check("one set during a call runs from the next", [name for name, _ in calls] == ["first", "third"])
    third.disable()
    check("a beat removed while others remain: the SDK's hook stays", animation_hook.hooked())
    first.disable()
    check("the last removed outside a call: the SDK's hook removed at once",
          not animation_hook.hooked() and animation_hook.IDENTIFIER not in state["hooks"]
          and not animation_hook.beats())

    calls.clear()
    lone = animation_hook.beat("mod:lone", lambda *args: (calls.append(("lone", args)), lone.disable(),
                                                          calls.append(("after", animation_hook.hooked()))))
    lone.enable()
    call()
    check("the last removed during a call: the SDK's hook kept until the call's end, then removed",
          calls[-1] == ("after", True) and not animation_hook.hooked()
          and animation_hook.IDENTIFIER not in state["hooks"])
    strays = animation_hook.beat("mod:strays", lambda *args: calls.append(("strays", args)))
    team = animation_hook.beat("mod:team", lambda *args: (team.disable(), strays.enable()))
    team.enable()
    before = state["hooks"][animation_hook.IDENTIFIER]
    call()
    check("a beat stopping and another starting within one call: the SDK's hook left as it was",
          state["hooks"].get(animation_hook.IDENTIFIER) is before and list(animation_hook.beats()) == ["mod:strays"])
    strays.disable()

    calls.clear()
    broken = animation_hook.beat("mod:broken", lambda *args: (_ for _ in ()).throw(ValueError("bad")))
    after = animation_hook.beat("mod:after", lambda *args: calls.append(("after", args)))
    broken.enable()
    after.enable()
    call()
    call()
    check("a beat that raises said once by its name and kind, the others still run",
          len(failures()) == 1 and '"beat":"mod:broken"' in failures()[0] and "ValueError:bad" in failures()[0]
          and [name for name, _ in calls] == ["after", "after"])
    broken.disable()
    stale = animation_hook.beat("mod:after", lambda *args: None)
    stale.disable()
    check("a handle whose name another beat holds now takes nothing away",
          list(animation_hook.beats()) == ["mod:after"] and animation_hook.beats()["mod:after"] is after.callback)
    after.disable()
    check("the last gone: nothing set, no hook", not animation_hook.beats() and not animation_hook.hooked())
    first.enable()
    check("set again, the SDK's hook comes back", animation_hook.hooked()
          and animation_hook.IDENTIFIER in state["hooks"])
    first.disable()
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
