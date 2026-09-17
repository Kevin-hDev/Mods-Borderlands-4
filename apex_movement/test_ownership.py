"""Tests value ownership: the game's value kept at the first write, restores, character values forgotten."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

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
check("nothing is owned after restore_all", not ownership._entries)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
