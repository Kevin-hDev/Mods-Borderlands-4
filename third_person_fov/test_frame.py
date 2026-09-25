"""Only the played body clocks the camera, with one final update when gameplay ends."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["settings_exists"] = True

from third_person_fov import frame  # noqa: E402

played = sdk_stubs.body("BPAnim_Player_3rd_C", 10)
enemy = sdk_stubs.body("BPAnim_Player_3rd_C", 20)
other = sdk_stubs.body("EnemyAnimation", 30)
state["pc"] = sdk_stubs.player(played)
seen = []
frame.camera.on_frame = lambda now: seen.append(now)

frame.on_frame(enemy, 1)
frame.on_frame(other, 2)
frame.on_frame(played, 3)
state["pc"] = None
frame.on_frame(other, 4)
frame.on_frame(other, 5)

ok = seen == [3, 4]
print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
raise SystemExit(0 if ok else 1)
