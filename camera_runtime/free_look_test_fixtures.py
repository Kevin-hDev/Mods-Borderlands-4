"""A fake player, camera and game memory for Free Look's tests."""

import struct
import types

from apex_camera_runtime.free_look_definitions import Layout
from apex_camera_runtime.free_look_lookup import Modes

SHAPE = Layout(blend=0x18, method=0x20, behaviors=0x28)
ADDRESSES = {"ThirdPerson": 0x4000_0000, "Orbit": 0x4000_0100, "Default": 0x4000_0200}


def rotator(pitch=0.0, yaw=0.0):
    return types.SimpleNamespace(Pitch=pitch, Yaw=yaw, Roll=0.0)


def vector(x=0.0, y=0.0):
    return types.SimpleNamespace(X=x, Y=y, Z=0.0)


class Sdk:
    @staticmethod
    def make_struct(_type, **fields):
        return types.SimpleNamespace(**fields)


class Memory:
    """The three definitions, FromCamera except Orbit."""

    def __init__(self):
        self.methods = {address + SHAPE.method: 1 if name == "Orbit" else 0 for name, address in ADDRESSES.items()}

    def read(self, address, size):
        if address in ADDRESSES.values() and size == SHAPE.size:
            data = bytearray(SHAPE.size)
            struct.pack_into("<f", data, SHAPE.blend, 0.6)
            struct.pack_into("<i", data, SHAPE.method, self.methods[address + SHAPE.method])
            struct.pack_into("<Qii", data, SHAPE.behaviors, 0x5000_0000, 9, 9)
            return bytes(data)
        return None

    def read_int(self, address):
        return self.methods.get(address)

    def write_int(self, address, value):
        if address not in self.methods:
            return False
        self.methods[address] = value
        return True

    def method(self, name):
        return self.methods[ADDRESSES[name] + SHAPE.method]


MODES = Modes(SHAPE, dict(ADDRESSES))


class Manager:
    def __init__(self, mode):
        self.mode = mode
        self.layers = []
        self.CameraModeState = types.SimpleNamespace(
            BaseRotationOffset=rotator(), bases=[],
            SetBaseRotation=lambda NewRotation: self.CameraModeState.bases.append(NewRotation.Yaw))

    def GetActorCameraMode(self, _actor):
        return self.layers[-1] if self.layers else self.mode

    def PushActorCameraMode(self, actor, mode, *_rest):
        self.layers.append(mode)

    def PopActorCameraMode(self, actor, mode, *_rest):
        if mode in self.layers:
            self.layers.remove(mode)


class Movement:
    def __init__(self, throttle):
        self.RawThrottleInput = throttle
        self.kept = []

    def SetThrottleInput(self, value):
        self.kept.append(value)


class Pawn:
    def __init__(self, speed, vehicle_throttle=None):
        self.velocity, self.pushes = vector(speed), []
        self.zooming = False
        self.ZoomState = types.SimpleNamespace(bWantsToZoom=False)
        if vehicle_throttle is not None:
            self.OakVehicleMovement = Movement(vehicle_throttle)

    def GetVelocity(self):
        return self.velocity

    def GetLastMovementInputVector(self):
        return vector(1.0)

    def AddMovementInput(self, **values):
        self.pushes.append(values)


def mapping(key, *modifiers):
    return types.SimpleNamespace(Action=types.SimpleNamespace(Name="Action_Move"), Key=types.SimpleNamespace(KeyName=key),
                                 Modifiers=[types.SimpleNamespace(Class=types.SimpleNamespace(Name=m)) for m in modifiers])


class Controller:
    def __init__(self, mode="ThirdPerson", speed=600.0, vehicle_throttle=None):
        self.Pawn = Pawn(speed, vehicle_throttle)
        self.OakCharacter = None if vehicle_throttle is not None else self.Pawn
        self.PlayerCameraManager = Manager(mode)
        self.view = rotator(5.0, 0.0)
        self.ignores = []
        self.held = {}
        self.PlayerInput = types.SimpleNamespace(EnhancedActionMappings=[
            mapping("Z", "InputModifierSwizzleAxis"), mapping("Q", "InputModifierNegate"),
            mapping("S", "InputModifierSwizzleAxis", "InputModifierNegate"), mapping("D")])

    def GetControlRotation(self):
        return self.view

    def SetControlRotation(self, rotation, bResetCamera):
        self.view = rotation

    def SetIgnoreMoveInput(self, value):
        self.ignores.append(value)

    def value(self, name):
        return self.held.get(name, 0.0)

    def IsInputKeyDown(self, key):
        return self.held.get(key.KeyName, 0.0) > 0.5

    def GetInputAnalogKeyState(self, key):
        return self.held.get(key.KeyName, 0.0)
