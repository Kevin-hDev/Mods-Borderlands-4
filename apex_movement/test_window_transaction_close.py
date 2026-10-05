"""External window closure waits for a pending settings compensation."""

import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS

events = []
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=events.append)
sdk.hooks = NS(remove_hook=lambda *_args: None, has_hook=lambda *_args: False,
               Type=NS(POST=1))
sdk.commands = NS(remove_command=lambda *_args: None, has_command=lambda *_args: False)
sdk.find_enum = lambda _name: NS(Default=0, DoNotLock=0)
sys.modules["unrealsdk"] = sdk
base = ModuleType("mods_base")
sys.modules["mods_base"] = base
character = NS()
pc = NS(bShowMouseCursor=False, CurrentMouseCursor=0, OakCharacter=character)
base.get_pc = lambda **_kwargs: pc

PACKAGE = "_movement_transaction_close_test"
package = ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).with_name("apex_movement"))]
sys.modules[PACKAGE] = package
window = importlib.import_module(f"{PACKAGE}.control_window")


def session(ready_values):
    root = NS(RemoveFromParent=lambda: events.append("removed"),
              SetKeyboardFocus=lambda: None)
    form = NS(focus=lambda: root, poll=lambda: False, selecting=lambda: False,
              close_ready=lambda: ready_values.pop(0))
    library = NS(SetInputMode_GameOnly=lambda *_args: None)
    item = window.Session(lambda: pc, lambda: root, lambda: library, False,
                          form, NS(ready=lambda: True), lambda: character)
    window._active = item
    return item


command = session([False, True])
command.close("command")
assert not command.closed and command.deferred_close == "command"
command.poll(1)
assert command.closed and "removed" in events

events.clear()
changed = session([False, True])
window.get_pc = lambda **_kwargs: NS()
changed.poll(1)
assert changed.closed and "removed" in events

events.clear()
window.get_pc = lambda **_kwargs: pc
waiting = session([False, False, False])
waiting.form.close_abort = lambda: events.append("aborted")
waiting.close("command")
waiting.close_deadline = 0
waiting.poll(window.POLL_NS + 1)
assert waiting.closed and "aborted" in events and "removed" in events

events.clear()
context = session([False, False, False])
context.form.close_abort = lambda: events.append("aborted")
context.close("command")
window.get_pc = lambda **_kwargs: NS()
context.poll(window.POLL_NS + 1)
assert context.closed and "aborted" in events

print("RESULTAT: TOUS LES TESTS PASSENT")
