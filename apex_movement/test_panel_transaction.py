"""A menu transaction cannot wait forever after changing an earlier option."""

import pathlib
import sys
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import movement_ui_fixture  # noqa: E402

movement_ui_fixture.install()

from apex_movement.panel_transaction import TRANSACTION_TIMEOUT_NS, Transaction  # noqa: E402
from apex_camera_runtime.camera_option import CameraBoolOption  # noqa: E402


class Option:
    def __init__(self, identifier, value, wait=False):
        self.identifier = identifier
        self._value = value
        self.wait = wait
        self.camera_status = "confirmed"

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, target):
        if self.wait and target:
            self.camera_status = "waiting"
            return
        self._value = target
        self.camera_status = "confirmed"

    def cancel_pending(self):
        self.camera_status = "refused"
        return True


class Mod:
    def __init__(self):
        self.saved = 0

    def save_settings(self):
        self.saved += 1


now = [1]
mod = Mod()
third_person = Option("third_person", False)
shoulder = Option("shoulder_left", False, wait=True)
transaction = Transaction(mod, lambda *_args: None, clock=lambda: now[0])
outcome = transaction.start(
    ((third_person, True), (shoulder, True)),
    ((third_person, False), (shoulder, False)), "undo")
assert outcome is None and transaction.pending and third_person.value is True
now[0] += TRANSACTION_TIMEOUT_NS + 1
outcome = transaction.advance()
assert outcome[0] == "undo" and outcome[2] is False
assert not transaction.pending and third_person.value is False and shoulder.value is False
assert mod.saved == 1

native_target = [False]


def route(target):
    native_target[0] = target
    return True


def cancel_native():
    native_target[0] = False
    return True


camera_mod = Mod()
orbit = CameraBoolOption("orbit", False, route=route, cancel=cancel_native)
orbit.mod = NS(is_enabled=True)
camera_transaction = Transaction(camera_mod, lambda *_args: None)
assert camera_transaction.start(((orbit, True),), ((orbit, False),), "undo") is None
assert orbit.camera_status == "pending" and native_target[0] is True
cancelled = camera_transaction.cancel()
if native_target[0] is True:  # A late native answer may only commit the request still owned by the runtime.
    orbit.commit(True)
assert cancelled[2] is False and not camera_transaction.pending
assert orbit.value is False and native_target[0] is False and camera_mod.saved == 1

confirmed = [None]
framing = Option("camera_framing_zoom", 15)
framing.confirm_write = lambda **_kwargs: confirmed[0]
framing_mod = Mod()
framing_transaction = Transaction(framing_mod, lambda *_args: None, clock=lambda: now[0])
assert framing_transaction.start(((framing, 25),), ((framing, 15),), "write") is None
assert framing_mod.saved == 0 and framing_transaction.pending
confirmed[0] = False
assert framing_transaction.advance() is None
assert framing.value == 15 and framing_transaction.pending and framing_mod.saved == 0
confirmed[0] = True
now[0] += TRANSACTION_TIMEOUT_NS + 1
assert framing_transaction.advance()[2] is False
assert not framing_transaction.pending and framing_mod.saved == 1

failed_mod = Mod()
save = failed_mod.save_settings
failed_mod.save_settings = lambda: (_ for _ in ()).throw(OSError("private"))
failed_transaction = Transaction(failed_mod, lambda *_args: None, clock=lambda: now[0])
assert failed_transaction.start(((framing, 25),), ((framing, 15),), "write") is None
assert failed_transaction.pending and framing.value == 15
assert failed_transaction.advance() is None
failed_mod.save_settings = save
now[0] += TRANSACTION_TIMEOUT_NS + 1
assert failed_transaction.advance()[2] is False
assert not failed_transaction.pending

# A native request that cannot yet cancel must not retain the settings window forever.
# Its native owner remains responsible for safe cleanup; the menu must not save success.
uncancelled_target = [False]
blocked_option = CameraBoolOption("orbit", False,
                                 route=lambda value: uncancelled_target.__setitem__(0, value) or True,
                                 cancel=lambda: False)
blocked_option.mod = NS(is_enabled=True)
blocked_mod = Mod()
blocked_transaction = Transaction(blocked_mod, lambda *_: None, clock=lambda: now[0])
assert blocked_transaction.start(((blocked_option, True),), ((blocked_option, False),), "write") is None
assert blocked_option.camera_status == "pending"
now[0] += 60_000_000_000
outcome = blocked_transaction.cancel()
assert outcome is not None, "Unacknowledged cancellation still owns the window"
assert outcome[2] is False and not blocked_transaction.pending
assert blocked_mod.saved == 0
assert blocked_option.camera_status == "refused" and uncancelled_target[0]

# The failed menu choice no longer blocks unrelated settings or a subsequent Restore.
outcome = blocked_transaction.start(((blocked_option, False),), ((blocked_option, False),), "restore")
assert outcome is not None and outcome[2] is True
assert blocked_option.value is False and blocked_mod.saved == 1

# Earlier scalar writes must not leak into the next save after an unacknowledged cancellation.
fov = Option("fov", 110)
blocked_mod.saved = 0
assert blocked_transaction.start(((fov, 120), (blocked_option, True)),
                                 ((fov, 110), (blocked_option, False)), "write") is None
now[0] += 60_000_000_000
assert blocked_transaction.advance()[2] is False
assert fov.value == 110, "Failed camera transaction leaked its earlier FOV change"
assert blocked_option.value is False and blocked_option.camera_status == "refused"
assert blocked_mod.saved == 0

logical_calls = []
logical_option = CameraBoolOption("orbit", False, route=lambda _: True,
                                 cancel=lambda *, restore=True: logical_calls.append(restore) or True)
logical_option.mod = NS(is_enabled=True)
logical_transaction = Transaction(Mod(), lambda *_: None)
assert logical_transaction.start(((logical_option, True),), ((logical_option, False),), "write") is None
assert logical_transaction.abort()[2] is False
assert logical_calls == [False], "Invalid window context issued a physical camera restore"
assert logical_option.value is False and logical_option.camera_status == "refused"

print("RESULTAT: TOUS LES TESTS PASSENT")
