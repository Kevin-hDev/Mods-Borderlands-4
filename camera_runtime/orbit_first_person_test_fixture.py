"""Real controller and coordinator boundary for first-person Orbit tests."""
from types import SimpleNamespace as NS
from apex_camera_runtime.runtime import CameraRuntime
from native_climb_test_fixture import NativeClimbFixture


class OrbitFirstPersonFixture(NativeClimbFixture):
    def prepare(self, third=False):
        self.make()
        self.dispatch_transition_hooks()
        self.controller.stop()
        self.settings.enabled = third
        self.now = 10
        self.controller.clock = lambda: self.now
        self.setups = 0
        self.runtime = CameraRuntime(NS(stop=lambda: None, apply=lambda *_: None))
        self.runtime.register('camera', 100, self.settings)
        self.requests.clear()
        self.manager.pushes = self.manager.pops = 0
        self.tick()

    def dispatch_transition_hooks(self):
        native_call = self.pc.ClientSetCameraMode

        def request(mode):
            parameters = NS(NewCamMode=mode)
            for (path, kind, _identifier), callback in tuple(self.controller.hooks.items.items()):
                if path.endswith(':ClientSetCameraMode') and kind == 'PRE':
                    result = callback(self.pc, parameters, None, native_call)
                    if result is self.controller.hooks.Block:
                        return
            native_call(mode)

        self.pc.ClientSetCameraMode = request

    def setup(self, runtime):
        self.setups += 1
        runtime.set_third_person(self.controller)

    def tick(self):
        self.now += 10
        error = self.runtime.prepare_third_person('camera', self.settings.enabled, self.setup)
        if error is not None:
            raise error
        self.runtime.tick(self.pc, self.now)

    def enter_orbit(self):
        self.assertTrue(self.runtime.toggle_orbit('camera'))
        self.tick()
        self.tick()
        self.assertEqual(self.manager.mode, 'Orbit')
        self.assertTrue(self.settings.orbit)
