"""FFYL keeps the selected third-person camera without stacking owned modes."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.third_person import ThirdPersonController  # noqa: E402
from camera_test_fixtures import Bridge, Hooks, Manager, Settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


settings = Settings()
manager, bridge = Manager(), Bridge()
actor = types.SimpleNamespace(ZoomState=types.SimpleNamespace(bWantsToZoom=False))
pc = types.SimpleNamespace(
    _get_address=lambda: 31,
    OakCharacter=actor,
    PlayerCameraManager=manager,
)
controller = ThirdPersonController(Hooks(), bridge, identifier="ffyl")
controller.sync("third_person_fov", pc, settings, 1)

manager.mode = "FFYL"
controller.sync("third_person_fov", pc, settings, 2)
check("an observed FFYL override requests one owned ThirdPerson recovery",
      manager.mode == "ThirdPerson" and manager.pushes == 2 and manager.pops == 1
      and controller.foot_mode.pending)

controller.sync("third_person_fov", pc, settings, 3)
controller.sync("third_person_fov", pc, settings, 4)
check("confirmed FFYL recovery never stacks another camera layer",
      manager.mode == "ThirdPerson" and manager.pushes == 2 and manager.pops == 1
      and not controller.foot_mode.pending and not controller._recovery_requested)
controller.stop()

death_manager, death_bridge = Manager(), Bridge()
death_pc = types.SimpleNamespace(
    _get_address=lambda: 32,
    OakCharacter=actor,
    PlayerCameraManager=death_manager,
)
death = ThirdPersonController(Hooks(), death_bridge, identifier="death")
death.sync("third_person_fov", death_pc, settings, 10)
death_manager.mode = "DeathCamera"
death.sync("third_person_fov", death_pc, settings, 11)
check("FFYL recovery does not rewrite the separate death camera",
      death_manager.mode == "DeathCamera" and death_manager.pushes == 1 and death_manager.pops == 0)
death.stop()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
