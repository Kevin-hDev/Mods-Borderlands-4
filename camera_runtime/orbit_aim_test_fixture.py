"""Real ADS, controller and hooks with only SDK/native boundaries substituted."""
from types import SimpleNamespace as NS
from collections import deque

from ads_sdk_test_fixtures import Native, player
from apex_camera_runtime.ads_context import ContextReader
from apex_camera_runtime.ads_session import AdsSession
from apex_camera_runtime.third_person import ThirdPersonController
from camera_test_fixtures import Bridge, Hooks, Settings, args


class OrbitAimFixture:
    def make(self, third=False, enabled=True):
        self.pc, self.actor, self.manager, self.animation, self.weapon, collector = player()
        self.actor.ZoomState = NS(bWantsToZoom=False)
        self.ladder = NS(CurrentClimbable=None)
        self.climb_animation = NS(CurrentType=0)
        self.actor.CharacterMovement = NS(LadderState=self.ladder, LadderAnimState=self.climb_animation)
        self.manager.mode = 'Default'
        self.manager.GetActorCameraMode = lambda _actor: self.manager.mode
        self.requests = []
        self.camera_calls = deque(maxlen=64)
        self.accept = True
        self.refused_modes = ()
        self.raise_modes = ()
        self.hooks, self.bridge, self.native, self.logs = Hooks(), Bridge(), Native(), []
        self.settings = Settings()
        self.settings.enabled, self.settings.orbit = third, True
        self.settings.third_person_ads = lambda: enabled
        reader = ContextReader(lambda item: lambda: item, self.native.identify, lambda _: [collector])
        self.ads = AdsSession(self.native, reader, self.logs.append)
        self.now = 1
        self.controller = ThirdPersonController(self.hooks, self.bridge, 'orbit_aim',
            log=self.logs.append, clock=lambda: self.now, ads=self.ads)

        def native_call(api, mode, *values):
            self.requests.append(mode)
            self.camera_calls.append((api, mode, values))
            if mode in self.raise_modes:
                raise RuntimeError('native request refused')
            if self.accept and mode not in self.refused_modes:
                self.manager.mode = mode

        def dispatch(suffix, mode, *values):
            parameters = NS(NewCamMode=mode) if suffix == ':ClientSetCameraMode' else args(mode)
            if values:
                for name, value in zip(('Transition', 'BlendTimeOverride', 'bTeleport', 'bForceResetMode'), values):
                    setattr(parameters, name, value)
            call = lambda rewritten, *rest: native_call(suffix, rewritten, *rest)
            for (path, kind, _identifier), callback in tuple(self.hooks.items.items()):
                if path.endswith(suffix) and kind == 'PRE':
                    if callback(self.pc, parameters, None, call) is self.hooks.Block:
                        return
            call(mode, *values)

        self.pc.ClientSetCameraMode = lambda mode: dispatch(':ClientSetCameraMode', mode)
        self.pc.CameraTransition = lambda mode, *values: dispatch(':CameraTransition', mode, *values)
        self.frame()
        self.requests.clear()
        self.camera_calls.clear()

    def frame(self):
        self.now += 1
        self.controller.sync('camera', self.pc, self.settings, self.now)

    def aim(self):
        self.actor.ZoomState.bWantsToZoom = True
        self.pc.CameraTransition('Default')
        self.frame()
        self.frame()

    def release(self):
        self.actor.ZoomState.bWantsToZoom = False
        self.native.status.fov_writes += 1
        self.frame()
        self.native.status.fov_writes += 1
        self.native.status.zoom_scale = 1.0
        self.frame()
        self.frame()
