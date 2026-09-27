"""Small SDK doubles shared by the third-person runtime tests."""

import types


class Hooks:
    class Type:
        PRE = "PRE"
        POST = "POST"

    Block = object()

    def __init__(self):
        self.items = {}

    def add_hook(self, path, kind, identifier, callback):
        self.items[(path, kind, identifier)] = callback

    def has_hook(self, path, kind, identifier):
        return (path, kind, identifier) in self.items

    def remove_hook(self, path, kind, identifier):
        self.items.pop((path, kind, identifier))


class Bound:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)


def args(mode):
    return types.SimpleNamespace(NewMode=mode, Transition="Default", BlendTimeOverride=-1.0,
                                 bTeleport=False, bForceResetMode=False)


class Manager:
    def __init__(self):
        self.mode = "Default"
        self.pushes = 0
        self.pops = 0

    def PushActorCameraMode(self, _actor, mode, *_args):
        self.mode = mode
        self.pushes += 1

    def PopActorCameraMode(self, _actor, *_args):
        self.mode = "Default"
        self.pops += 1

    def GetActorCameraMode(self, _actor):
        return self.mode


class Bridge:
    def __init__(self):
        self.starts = self.stops = 0
        self.fail_stop = False
        self.suspended = []
        self.start_rights = []
        self.rights = []

    def start(self, _manager, right, _pc):
        self.starts += 1
        self.start_rights.append(right)
        return True

    def set_right(self, right):
        self.rights.append(right)
        return True

    def stop(self):
        self.stops += 1
        if self.fail_stop:
            raise RuntimeError("temporary")

    def suspend(self, value):
        self.suspended.append(bool(value))


class Settings:
    enabled = True

    def __init__(self):
        self.left = False
        self.orbit = False
        self.orbit_saves = 0
        self.orbit_rejections = 0
        self.notes = []

    def third_person_enabled(self):
        return self.enabled

    def shoulder_left(self):
        return self.left

    def set_shoulder_left(self, value):
        self.left = value

    def orbit_enabled(self):
        return self.orbit

    def set_orbit(self, value):
        self.orbit = value
        self.orbit_saves += 1

    def reject_orbit(self):
        self.orbit_rejections += 1

    def note(self, message):
        self.notes.append(message)
