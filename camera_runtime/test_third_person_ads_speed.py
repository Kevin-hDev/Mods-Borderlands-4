"""Aiming enters and leaves first person without a visible camera blend."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

events = []


class RecordedManager(Manager):
    def __init__(self):
        super().__init__()
        self.push_calls = []
        self.pop_calls = []

    def PushActorCameraMode(self, actor, mode, *args):
        self.push_calls.append((actor, mode, *args))
        super().PushActorCameraMode(actor, mode, *args)

    def PopActorCameraMode(self, actor, *args):
        events.append("pop")
        self.pop_calls.append((actor, *args))
        super().PopActorCameraMode(actor, *args)


zoom = types.SimpleNamespace(bWantsToZoom=False)
actor = types.SimpleNamespace(ZoomState=zoom)
manager = RecordedManager()
transitions = []
client_modes = []


def transition(*args):
    events.append("transition")
    transitions.append(args)
    manager.mode = "Default"


pc = types.SimpleNamespace(
    _get_address=lambda: 90,
    OakCharacter=actor,
    PlayerCameraManager=manager,
    CameraTransition=transition,
    ClientSetCameraMode=lambda mode: client_modes.append(mode),
)
controller = ThirdPersonController(Hooks(), Bridge(), identifier="ads_speed")
controller.sync("apex_movement", pc, Settings(), 1)
events.clear()

zoom.bWantsToZoom = True
controller.sync("apex_movement", pc, Settings(), 2)
aim_pop = manager.pop_calls[-1]
entry_ok = (
    transitions == [("Default", "Default", 0.0, True, True)]
    and client_modes == []
    and aim_pop[1:] == ("ThirdPerson", "Default", 0.0, True)
    and events == ["pop", "transition"]
)

zoom.bWantsToZoom = False
controller.sync("apex_movement", pc, Settings(), 3)
aim_push = manager.push_calls[-1]
exit_ok = aim_push[1:] == ("ThirdPerson", "Default", 0.0, True)

print(("OK   " if entry_ok else "ECHEC") + " | aiming enters first person instantly")
print(("OK   " if exit_ok else "ECHEC") + " | releasing aim restores third person instantly")
print("RESULTAT:", "TOUS LES TESTS PASSENT" if entry_ok and exit_ok else "ECHEC")
sys.exit(0 if entry_ok and exit_ok else 1)
