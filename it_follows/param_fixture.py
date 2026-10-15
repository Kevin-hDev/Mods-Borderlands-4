"""The fake game of the hidden values, for the tests of gbx_param.py and of the normal mode's dodges and camps: a real
block of bytes, read and written with ctypes as the game's would be, holding structs whose fields lie where their
layout says, and GbxParams of 56 bytes; camps with their getters, and enemies whose dodge state keeps its own copy of
their family's file. Taken from the trials' fixture (docs/RUN/sondes/params_fixture.py).
"""

import ctypes
import struct
import types
from typing import Any

SIZE = 56


def param(whole: int | None = None, decimal: tuple[float, float] | None = None, single: float | None = None,
          pointer: int = 0, kind: int | None = None) -> bytes:
    """A GbxParam's bytes as trial 21 read them: pointer at +0, value at +8, its size at +32, its kind at +40 (2 a
    whole number, 3 a decimal one, 11 a range of two floats)."""
    raw = bytearray(SIZE)
    struct.pack_into("<Q", raw, 0, pointer)
    if whole is not None:
        struct.pack_into("<i", raw, 8, whole)
        size, found = 4, 2
    elif single is not None:
        struct.pack_into("<f", raw, 8, single)
        size, found = 4, 3
    elif decimal is not None:
        struct.pack_into("<ff", raw, 8, *decimal)
        size, found = 8, 11
    else:
        size, found = 0, 0
    struct.pack_into("<H", raw, 32, size)
    raw[40] = found if kind is None else kind
    return bytes(raw)


class Prop:
    def __init__(self, size: int, offset: int) -> None:
        self.ElementSize, self.Offset_Internal = size, offset


class Kind:
    """A struct type or a class: its name and where its fields lie."""

    def __init__(self, name: str, props: dict[str, Prop]) -> None:
        self.Name, self.props = name, props

    def _find_prop(self, name: str) -> Prop:
        if name not in self.props:
            raise ValueError(f"no field {name}")
        return self.props[name]


PARAM_KIND = Kind("GbxParam", {})


class Param:
    def __init__(self, address: int, kind: Kind = PARAM_KIND) -> None:
        self._address, self._type = address, kind

    def _get_address(self) -> int:
        return self._address


class Memory:
    """The block of bytes the fake game lives in."""

    def __init__(self, size: int = 1 << 17) -> None:
        self.buffer = ctypes.create_string_buffer(size)
        self.base = ctypes.addressof(self.buffer)
        self.used = 0

    def take(self, size: int) -> int:
        """Reserves size bytes; refuses past the block's end, where a write would hit the test's own memory."""
        if self.used + size > len(self.buffer):
            raise MemoryError("fake game memory full")
        address = self.base + self.used
        self.used += (size + 15) // 16 * 16
        return address

    def put(self, address: int, raw: bytes) -> None:
        ctypes.memmove(address, raw, len(raw))

    def value(self, param_view: Any) -> bytes:
        """The 56 bytes a field's view points at."""
        return ctypes.string_at(param_view._get_address(), SIZE)


class Built:
    """A struct (or an object, when named) laid in the memory: a new view at each ask, at the same address, as the SDK
    hands them out; copies=True hands out a new address at each ask instead, as a copy would. Plain fields are kept
    as values, and written as the game's would be."""

    def __init__(self, memory: Memory, address: int, kind: Kind, values: dict, name: str | None,
                 copies: bool = False) -> None:
        self.__dict__.update(_memory=memory, _address=address, _values=values, _copies=copies)
        if name is None:
            self.__dict__["_type"] = kind
        else:
            self.__dict__.update(Class=kind, Name=name)

    def _get_address(self) -> int:
        return self._address

    def __getattr__(self, name: str) -> Any:
        values = self.__dict__["_values"]
        if name not in values:
            raise AttributeError(name)
        value = values[name]
        if not isinstance(value, tuple):
            return value
        kind, offset = value
        address = self._address + offset
        if self._copies:
            address = self._memory.take(SIZE)
        return Param(address, kind)

    def __setattr__(self, name: str, value: Any) -> None:
        values = self.__dict__["_values"]
        if name in values and isinstance(values[name], tuple):
            raise AttributeError(f"{name} is a GbxParam: the SDK cannot write it")
        if isinstance(value, Built) and name in values and value is values[name]:
            return
        values[name] = value


def build(memory: Memory, kind_name: str, fields: dict[str, Any], name: str | None = None, at: int | None = None,
          copies: bool = False, sizes: dict[str, int] | None = None, kinds: dict[str, Kind] | None = None) -> Built:
    """Lays a struct: each bytes value is a GbxParam (of sizes[field] bytes when given, of kinds[field] type when
    given), each dict a struct inside it, any other value a plain field."""
    layout: dict[str, Prop] = {}
    plain: dict[str, Any] = {}
    offset = 0
    nested: dict[str, tuple[int, str, dict]] = {}
    for field, value in fields.items():
        if isinstance(value, bytes):
            layout[field] = Prop((sizes or {}).get(field, SIZE), offset)
            offset += SIZE
        elif isinstance(value, dict):
            size = _size(value)
            layout[field] = Prop(size, offset)
            nested[field] = (offset, value.get("__kind__", field), value)
            offset += size
        else:
            plain[field] = value
    address = memory.take(max(offset, 16)) if at is None else at
    values: dict[str, Any] = dict(plain)
    for field, value in fields.items():
        if isinstance(value, bytes):
            memory.put(address + layout[field].Offset_Internal, value)
            values[field] = ((kinds or {}).get(field, PARAM_KIND), layout[field].Offset_Internal)
    for field, (inner_offset, inner_kind, inner) in nested.items():
        values[field] = build(memory, inner_kind, {k: v for k, v in inner.items() if k != "__kind__"},
                              at=address + inner_offset, copies=copies)
    return Built(memory, address, Kind(kind_name, layout), values, name, copies)


def _size(fields: dict) -> int:
    return sum(SIZE if isinstance(v, bytes) else _size(v) if isinstance(v, dict) else 0
               for k, v in fields.items() if k != "__kind__")


def at(metres: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(X=metres * 100.0, Y=0.0, Z=0.0)


class Getter:
    """A camp's getter: its answer, and each call written in calls."""

    def __init__(self, name: str, answer: int, calls: list) -> None:
        self.name, self.answer, self.calls = name, answer, calls

    def __call__(self, *args: object) -> int:
        self.calls.append((self.name, args))
        return self.answer


def camp_style(memory: Memory, total: Any, wave: Any = None, style: str = "SpawnerStyleDef_Waves") -> Built:
    """A camp's numbers: NumTotalActors and NumWaveActors for waves, NumActors for a bunch; a whole number, or a
    (centre, half width) range."""
    def held(value: Any) -> bytes:
        return param(decimal=value) if isinstance(value, tuple) else param(whole=value)

    if style.endswith("Bunch"):
        fields = {"NumActors": held(total), "NumActorsPassive": param(whole=0)}
    else:
        fields = {"NumTotalActors": held(total), "NumWaveActors": held(total if wave is None else wave),
                  "NumWaveActorsPassive": param(whole=0)}
    return build(memory, style, fields)


def camp(name: str, metres: float, style: Built, calls: list, enemy: str = "Mix_GRA_Bandit_Coastal",
         born: int = 0, total: int = 4) -> Any:
    """A camp of the game: its enemy's definition, its numbers, its getters, and ResetSpawner, each call written in
    calls. A reset draws again from the numbers written: its total becomes NumTotalActors' (or NumActors')."""
    component = types.SimpleNamespace(
        GbxActorDef=types.SimpleNamespace(_name=enemy), SpawnerStyleData=types.SimpleNamespace(InlineDef=style),
        GetNumTotalActors=Getter(f"{name}.total", total, calls),
        GetNumSpawnedActors=Getter(f"{name}.spawned", born, calls),
        GetNumAliveActors=Getter(f"{name}.alive", born, calls))

    def reset(destroy: bool) -> None:
        calls.append((f"{name}.reset", (destroy,)))
        field = "NumTotalActors" if "NumTotalActors" in style._values else "NumActors"
        raw = style._memory.value(getattr(style, field))
        # A range draws within itself: its centre stands for the draw.
        drawn = struct.unpack_from("<f", raw, 8)[0] if raw[40] == 11 else struct.unpack_from("<i", raw, 8)[0]
        component.GetNumTotalActors.answer = round(drawn)

    component.ResetSpawner = reset
    return types.SimpleNamespace(Name=name, SpawnerComponent=component, K2_GetActorLocation=lambda: at(metres),
                                 freed=False)


def dodge_fields(chance: float, moving: float = 10.0) -> dict:
    """A dodge file's GbxParams and conditions, laid as the game's field map says and filled as trial 21 read a
    human's: the chance a decimal number, the rest after a dodge a range, the conditions limited."""
    info = {"__kind__": "AIDodgeInfo", "Chance": param(single=chance), "delay": param(single=0.0),
            "cooldown": param(decimal=(8.0, 2.0)), "MinShooterDistance": 800.0, "MaxShooterDistance": 2048.0,
            "MaxDistance": 200.0, "bLimitMinShooterDistance": True, "bLimitMaxShooterDistance": True,
            "bLimitAngle": True, "bLimitDistance": True, "bRemoveAllDelay": False, "bUseTicketSettings": True}
    return {"GlobalCooldown": param(), "CombatStartedWarmup": param(single=2.0),
            "IsMovingSpeed": param(single=moving), "DodgeBullet": dict(info), "DodgeGrenade": dict(info),
            "DodgeZone": dict(info),
            "DodgeRandom": {"__kind__": "AIDodgeBasicInfo", "cooldown": param(single=4.0),
                            "bUseTicketSettings": True}}


def dodge_file(memory: Memory, family: str, chance: float = 0.15) -> Built:
    """A family's dodge file, an object of the game, with its own tickets switch."""
    return build(memory, "AIDodgeData", {**dodge_fields(chance), "bUseTicketSettings": True}, name=family)


def copy_of(memory: Memory, data: Built) -> dict:
    """An enemy's own copy of its family's file, as the game makes one at birth: the file's bytes and conditions."""
    fields: dict[str, Any] = {}
    for field, value in data._values.items():
        if isinstance(value, tuple):
            fields[field] = memory.value(getattr(data, field))
        elif isinstance(value, Built):
            inner = {"__kind__": value._type.Name}
            for inner_field, inner_value in value._values.items():
                inner[inner_field] = (memory.value(getattr(value, inner_field)) if isinstance(inner_value, tuple)
                                      else inner_value)
            fields[field] = inner
    fields.pop("bUseTicketSettings", None)
    return fields


def enemy(memory: Memory, name: str, metres: float, data: Built, dead: bool = False) -> Any:
    """An enemy whose state keeps its own copy of its family's file, taken when it is made, as at the game's birth."""
    state = build(memory, "AIDodgeState", {**copy_of(memory, data), "CurrentDodgeData": data})
    return types.SimpleNamespace(Name=name, AIDodgeState=state, HealthState=types.SimpleNamespace(bCurrentlyDead=dead),
                                 K2_GetActorLocation=lambda: at(metres), freed=False)
