"""Tests value ownership: the game's value kept at the first write, restores, character values forgotten."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_movement import ownership  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def accessors(target: types.SimpleNamespace, name: str) -> tuple:
    return (lambda: getattr(target, name)), (lambda value: setattr(target, name, value))


movement = types.SimpleNamespace(MinAnalogWalkSpeed=0.0)
asset = types.SimpleNamespace(constant=720.0)

ownership.write("floor", ownership.CHARACTER, *accessors(movement, "MinAnalogWalkSpeed"), 672.0)
check("a write reaches the game", movement.MinAnalogWalkSpeed == 672.0)
ownership.write("floor", ownership.CHARACTER, *accessors(movement, "MinAnalogWalkSpeed"), 960.0)
check("the game's value is kept from the first write", ownership.original("floor") == 0.0)
check("a written value is owned", ownership.is_owned("floor"))

ownership.restore("floor")
check("restore puts the game's value back", movement.MinAnalogWalkSpeed == 0.0 and not ownership.is_owned("floor"))
ownership.restore("floor")
check("restoring a value not owned does nothing", movement.MinAnalogWalkSpeed == 0.0)

steering = types.SimpleNamespace(constant=55.0, loaded=True)
duration = types.SimpleNamespace(constant=1.35)


def put_steering(value: float) -> None:
    # As a put through game.slide_asset() while the game has unloaded the asset.
    if not steering.loaded:
        raise AttributeError("asset not loaded")
    steering.constant = value


ownership.write("steering", ownership.ASSET, lambda: steering.constant, put_steering, 350.0)
steering.loaded = False
raised = False
try:
    ownership.restore("steering")
except AttributeError:
    raised = True
check("a value that cannot be put back raises", raised)
check("and stays owned with the game's value, to put back later",
      ownership.is_owned("steering") and ownership.original("steering") == 55.0)
steering.loaded = True
ownership.restore("steering")
check("the next restore puts the game's value back", steering.constant == 55.0 and not ownership.is_owned("steering"))

ownership.write("steering", ownership.ASSET, lambda: steering.constant, put_steering, 350.0)
ownership.write("duration", ownership.ASSET, *accessors(duration, "constant"), 30.0)
steering.loaded = False
failures = ownership.restore_each(["steering", "duration"])
check("restore_each puts the next values back after one fails",
      duration.constant == 1.35 and not ownership.is_owned("duration"))
check("and returns the failure, the value still owned",
      failures == ["could not restore steering: AttributeError('asset not loaded')"]
      and ownership.original("steering") == 55.0)
steering.loaded = True
ownership.restore("steering")

# The title screen (2026-09-19, 06:40:34): the game has unloaded Move_Slide, and loads it again from its files.
timer = types.SimpleNamespace(constant=1.35, loaded=True)


def put_timer(value: float) -> None:
    ownership.loaded(timer if timer.loaded else None).constant = value


ownership.write("timer", ownership.ASSET, lambda: timer.constant, put_timer, 30.0)
timer.loaded = False
failures = ownership.restore_each(["timer"])
check("a value whose asset the game unloaded is no failure: the game loads it again with its own value", failures == [])
check("it stays owned with the game's value, and is counted",
      ownership.original("timer") == 1.35 and ownership.unloaded_count() == 1)
timer.loaded, timer.constant = True, 1.35
ownership.write("timer", ownership.ASSET, lambda: timer.constant, put_timer, 30.0)
check("written again once loaded, it keeps the game's value and is no longer counted",
      ownership.original("timer") == 1.35 and ownership.unloaded_count() == 0)
ownership.restore("timer")
check("and is put back as any other", timer.constant == 1.35 and not ownership.is_owned("timer"))

ownership.write("floor", ownership.CHARACTER, *accessors(movement, "MinAnalogWalkSpeed"), 672.0)
ownership.write("slide", ownership.ASSET, *accessors(asset, "constant"), 850.0)
ownership.forget_character()
check("a level change forgets character values without writing them", movement.MinAnalogWalkSpeed == 672.0 and not ownership.is_owned("floor"))
check("asset values survive a level change", ownership.is_owned("slide"))

new_movement = types.SimpleNamespace(MinAnalogWalkSpeed=0.0)
ownership.write("floor", ownership.CHARACTER, *accessors(new_movement, "MinAnalogWalkSpeed"), 672.0)
ownership.write("floor", ownership.CHARACTER, *accessors(new_movement, "MinAnalogWalkSpeed"), 700.0)


def broken_put(value: float) -> None:
    raise RuntimeError("object gone")


ownership.write("broken", ownership.ASSET, lambda: 1.0, lambda value: None, 2.0)
ownership._entries["broken"]["put"] = broken_put
failures = ownership.restore_all()
check("restore_all puts every value back", new_movement.MinAnalogWalkSpeed == 0.0 and asset.constant == 720.0)
check("a value that cannot be put back is reported, not raised", failures == ["could not restore broken: RuntimeError('object gone')"])
check("every value put back is forgotten", list(ownership._entries) == ["broken"])
# Kept, not forgotten (2026-09-18): forgotten, the next enable would read the mod's value still in the game and take it
# for the game's own, and never put the real one back.
check("a value that could not be put back stays owned, with the game's own value", ownership.original("broken") == 1.0)
ownership.write("broken", ownership.ASSET, lambda: 2.0, lambda value: None, 3.0)
check("so a later write does not take the mod's value for the game's", ownership.original("broken") == 1.0)

# Owning without writing: the game already holds what the movement wants, and a value the mod does not own is a
# value it never gives back (2026-09-20).
kept = types.SimpleNamespace(value=5.0)
ownership.claim("kept", ownership.CHARACTER, *accessors(kept, "value"))
check("claiming a value writes nothing", kept.value == 5.0)
check("but the mod owns it and knows the game's own value",
      ownership.is_owned("kept") and ownership.original("kept") == 5.0)
kept.value = 9.0
ownership.restore("kept")
check("so it is given back even though the mod never wrote it", kept.value == 5.0)

twice = types.SimpleNamespace(value=1.0)
ownership.write("twice", ownership.CHARACTER, *accessors(twice, "value"), 2.0)
ownership.claim("twice", ownership.CHARACTER, *accessors(twice, "value"))
check("claiming a value already owned keeps the game's value, not the mod's", ownership.original("twice") == 1.0)
ownership.restore("twice")

# A put that changes nothing raises nothing either: on 2026-09-20 the mod announced every value restored while the
# game kept the gravity it had been given.
stuck = types.SimpleNamespace(value=1.0)
ownership.write("stuck", ownership.CHARACTER, *accessors(stuck, "value"), 2.0)
ownership._entries["stuck"]["put"] = lambda value: None
failures = ownership.restore_each(["stuck"])
check("a value the game did not take back is reported instead of counted as given back",
      len(failures) == 1 and "still reads 2.0 after putting 1.0 back" in failures[0])
check("and it stays owned, with the game's own value",
      ownership.is_owned("stuck") and ownership.original("stuck") == 1.0)

unreadable = types.SimpleNamespace(value=1.0)
ownership.write("unreadable", ownership.CHARACTER, *accessors(unreadable, "value"), 2.0)
ownership._entries["unreadable"]["get"] = lambda: (_ for _ in ()).throw(RuntimeError("gone"))
check("a value that cannot be read again is reported, not raised",
      "cannot be read again" in ownership.restore_each(["unreadable"])[0])

curve = types.SimpleNamespace(value=types.SimpleNamespace(keys=[1.0, 2.0]))
ownership.write("curve", ownership.ASSET, *accessors(curve, "value"), "other")
ownership._entries["curve"]["put"] = lambda value: None
check("a value the mod cannot compare is left alone rather than called wrong",
      ownership.restore_each(["curve"]) == [] and not ownership.is_owned("curve"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
