"""Configured console shortcuts cannot overwrite a working grapple binding."""

from types import SimpleNamespace as NS
import control_fixture as f
from apex_grapple.control_bindings import Bindings
from apex_grapple.control_reserved import console_keys

f.mod.is_enabled = True
settings = NS(ConsoleKeys=[NS(KeyName="G"), NS(KeyName="J")])
f.state["extra_classes"]["InputSettings"] = NS(ClassDefaultObject=settings)
bindings = Bindings()
assert bindings.save(("V",))[0]
saved = f.mod.saved
for chosen in (("G",), ("J",), ("LeftControl", "G"), ("Tilde",)):
    success, message = bindings.save(chosen)
    assert not success and "reserved" in message.lower(), (chosen, success, message)
    assert f.config.DEVICES[0].selection() == ("V",)
assert f.mod.saved == saved

# Refresh on each completed choice: no stale UObject or stale console-key cache.
settings.ConsoleKeys = [NS(KeyName="Tilde")]
assert bindings.save(("G",))[0]
# Native BL4 on the French keyboard reports both Tilde and the literal character ².
for symbol in ("²", "`", "é", "§"):
    settings.ConsoleKeys = [NS(KeyName="Tilde"), NS(KeyName=symbol)]
    assert bindings.save(("G",))[0], symbol
    assert console_keys() == frozenset(("Tilde", symbol))
    assert not bindings.save(("Tilde",))[0]
settings.ConsoleKeys = [NS(KeyName="Tilde"), NS(KeyName="²")]
assert bindings.save(("Gamepad_FaceButton_Bottom",))[0]
saved = f.mod.saved
invalid = ("bad key", "", " ", "\n", "\x00", "\u202e", "A" * 257)
for configured in ([NS(KeyName=name)] for name in invalid):
    settings.ConsoleKeys = configured
    assert not bindings.save(("J",))[0]
    assert f.mod.saved == saved
settings.ConsoleKeys = [NS(KeyName="G")] * 17
assert not bindings.save(("J",))[0]
assert f.mod.saved == saved
del f.state["extra_classes"]["InputSettings"]
assert not bindings.save(("J",))[0]
assert f.config.DEVICES[0].selection() == ("G",)
print("OK | console shortcuts reserved, bounded validation, no writes on rejection/read failure")
