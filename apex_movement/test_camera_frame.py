"""The full pack's existing frame hook also clocks the shared camera runtime."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from apex_movement import frame  # noqa: E402


class Camera:
    def __init__(self) -> None:
        self.frames = []

    def on_frame(self, now_ns: int) -> None:
        self.frames.append(now_ns)


camera = Camera()
player_animation = object()
original_refresh = frame.game.refresh
original_character = frame.game.character
original_animation = frame.game.anim
frame.game.refresh = lambda _now: ""
frame.game.character = lambda: object()
frame.game.anim = lambda: player_animation
frame.set_camera(camera)
frame.tick(object(), None, None, None)
frame.tick(player_animation, None, None, None)
frame.game.character = lambda: None
frame.tick(object(), None, None, None)
frame.tick(object(), None, None, None)
frame.set_camera(None)
frame.game.refresh = original_refresh
frame.game.character = original_character
frame.game.anim = original_animation
ok = len(camera.frames) == 2
print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
sys.exit(0 if ok else 1)
