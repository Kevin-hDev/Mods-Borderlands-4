"""Real controller fixture with independently controlled native traversal fields."""
import types

from apex_camera_runtime.third_person import ThirdPersonController
from camera_test_fixtures import Bound, Bridge, Hooks, Manager, Settings, args


class NativeClimbFixture:
    def make(self, orbit=False):
        self.manager, self.bridge, self.settings = Manager(), Bridge(), Settings()
        self.settings.orbit = orbit
        self.ladder = types.SimpleNamespace(CurrentClimbable=None)
        self.animation = types.SimpleNamespace(CurrentType=0)
        self.actor = types.SimpleNamespace(
            CharacterMovement=types.SimpleNamespace(
                LadderState=self.ladder, LadderAnimState=self.animation),
            ZoomState=types.SimpleNamespace(bWantsToZoom=False))
        self.requests, self.notes = [], []
        self.accept = True

        def request(mode):
            self.requests.append(mode)
            if self.accept:
                self.manager.mode = mode

        self.pc = types.SimpleNamespace(_get_address=lambda: 10, OakCharacter=self.actor,
            PlayerCameraManager=self.manager, ClientSetCameraMode=request,
            CameraTransition=lambda mode, *_args: request(mode))
        self.controller = ThirdPersonController(Hooks(), self.bridge, "climb", log=self.notes.append)
        self.frame(1)
        self.requests.clear()

    def frame(self, now):
        self.controller.sync("apex_movement", self.pc, self.settings, now)

    def enter(self, now=2):
        self.ladder.CurrentClimbable = object()
        self.manager.mode = "ladder"
        self.frame(now)

    def rewritten_modes(self):
        modes = []
        for path, kind, identifier in self.controller.hooks.items:
            original = Bound()
            parameters = (types.SimpleNamespace(NewCamMode="Default")
                          if path.endswith(":ClientSetCameraMode") else args("Default"))
            callback = self.controller.hooks.items[(path, kind, identifier)]
            result = callback(self.pc, parameters, None, original)
            self.assertIs(result, self.controller.hooks.Block)
            modes.append(original.calls[0][0])
        return modes
