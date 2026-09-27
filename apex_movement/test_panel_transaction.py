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

print("RESULTAT: TOUS LES TESTS PASSENT")
