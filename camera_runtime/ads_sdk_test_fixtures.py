"""SDK-shaped test objects shared by ADS tests; never packaged with the runtime."""

import enum
from types import SimpleNamespace as NS


class Kind(enum.IntEnum):
    Pistol = 1
    SMG = 2
    Ordinary = 3
    Assault = 4
    Sniper = 5
    Heavy = 6
    Precision = 8
    Invalid = 1000000


def obj(pointer, size=8192, **values):
    return NS(_get_address=lambda: pointer,
              Class=NS(_get_struct_size=lambda: size), **values)


def player():
    weapon = obj(0x11000)
    animation = obj(0x12000, CurrentWeapon=obj(0x11000), WeaponType=Kind.Assault)
    actor = obj(0x13000, Mesh=NS(GetAnimInstance=lambda: animation),
                ActiveWeapons=NS(Slots=[NS(Weapon=weapon)]))
    state, inputs = obj(0x14000), obj(0x15000)
    manager = obj(0x16000, CameraModeState=state, CameraModeInputs=inputs)
    pc = obj(0x17000, OakCharacter=actor, PlayerCameraManager=manager)
    state.Inputs, inputs.Controller = inputs, pc
    collector = obj(0x18000, Outer=obj(0x13000))
    return pc, actor, manager, animation, weapon, collector


class Native:
    """Native API boundary double; policy and context logic remain real in tests."""
    def __init__(self):
        self.supported = True
        self.contexts, self.clears, self.releases = [], [], []
        self.status = NS(generation=0, fov_writes=0, zoom_scale=1.0, pending=0, active=0, error=0, wrong_thread=0)

    def prepare(self): return self.supported

    def identify(self, item):
        from apex_camera_runtime.ads_category import address
        from apex_camera_runtime.generated_ads import ObjectId
        return ObjectId(address(item), address(item) // 16, 1)

    def publish(self, context):
        self.contexts.append(context)
        self.status.generation, self.status.active = context.generation, 1

    def clear(self, generation):
        self.clears.append(generation)
        self.status.active = 0
        self.status.error = 0
        return not self.status.pending

    def release(self, generation):
        self.releases.append(generation)

    def stats(self): return self.status
