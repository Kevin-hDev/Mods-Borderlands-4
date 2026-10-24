"""Refresh live container fields, holding the containers only by weak pointers."""
import math
import struct
from itertools import islice
from typing import Any, Callable, NamedTuple

from .loot_constants import (BASE_DISTANCE, FIELD_OFFSET, FIELD_SIZE, LOOT_DEFINITION,
                             MAX_MULTIPLIER, MAX_OBJECTS, MAX_PATH, MAX_SCAN)


class Owned(NamedTuple):
    original: bytes
    # None marks a competing write until that object unloads.
    last: bytes | None
    # The container while the game keeps it, None once destroyed.
    pointer: Callable[[], Any]


class LootFields:
    def __init__(self, containers, memory, weak):
        self.containers = containers
        self.memory = memory
        self.weak = weak
        # Keys are scalar identities.
        self.saved = {}

    @property
    def pending(self):
        return any(owned.last is not None for owned in self.saved.values())

    @staticmethod
    def identity(obj):
        try:
            path, address = str(obj._path_name()), int(obj._get_address())
            if (not path or len(path) > MAX_PATH or not 0x10000 <= address < 2**63
                    or address % 8):
                return None
            return path, address + FIELD_OFFSET
        except Exception:
            return None

    @staticmethod
    def eligible(obj, path):
        if 'Default__' in path or path.startswith('/Script/'):
            return False
        try:
            config = obj.UsabilityConfigInfo
            return (config.bUseExternalDef is True and config.bRequireTrace is True
                    and str(config.UsabilityDataDef._name).lower() == LOOT_DEFINITION)
        except Exception:
            return False

    def live(self, world):
        objects = list(islice(self.containers(world), MAX_SCAN + 1))
        if len(objects) > MAX_SCAN:
            raise RuntimeError('Loot scan budget exceeded')
        seen = set()
        for obj in objects:
            key = self.identity(obj)
            if key is not None:
                seen.add(key)
                if self.eligible(obj, key[0]):
                    yield key, obj
        # The world's list leaves out the cells being unloaded, whose containers the game has not destroyed yet:
        # only a destroyed container is forgotten.
        for key, owned in tuple(self.saved.items()):
            if key not in seen and owned.pointer() is None:
                del self.saved[key]

    @staticmethod
    def valid(data):
        if data is None or len(data) != FIELD_SIZE:
            return False
        flag, distance = struct.unpack('<Bf', data)
        return flag in (0, 1) and math.isfinite(distance) and 0 <= distance <= 3000

    def apply(self, distance, world):
        if (not math.isfinite(distance)
                or not BASE_DISTANCE <= distance <= BASE_DISTANCE * MAX_MULTIPLIER):
            raise ValueError('Invalid loot range')
        for key, obj in self.live(world):
            before = self.memory.read(key[1], FIELD_SIZE)
            if not self.valid(before):
                continue
            owned = self.saved.get(key)
            if owned is not None and owned.pointer() is None:
                # Destroyed and replaced at the same path and address since the last refresh: a new container whose
                # value is the game's, extended like any other (Kevin, 2026-10-24).
                del self.saved[key]
                owned = None
            if owned is not None:
                if owned.last is None or before != owned.last:
                    self.saved[key] = owned._replace(last=None)
                    continue
                original = owned.original
            else:
                if len(self.saved) >= MAX_OBJECTS:
                    raise RuntimeError('Loot ownership budget exceeded')
                original = before
            flag, original_distance = struct.unpack('<Bf', original)
            # Extending reach must not shorten a container's longer native/custom reach.
            value = max(distance, original_distance) if flag else distance
            target = struct.pack('<Bf', 1, value)
            if before == target:
                continue
            pointer = owned.pointer if owned is not None else self.weak(obj)
            self.saved[key] = Owned(original, target, pointer)
            if (not self.memory.write(key[1], target)
                    or self.memory.read(key[1], FIELD_SIZE) != target):
                observed = self.memory.read(key[1], FIELD_SIZE)
                self.saved[key] = Owned(original, observed if observed is not None else target, pointer)
                raise RuntimeError('Loot update refused')

    def restore(self):
        failed = False
        for key, owned in tuple(self.saved.items()):
            if owned.last is None:
                continue
            obj = owned.pointer()
            if obj is None:
                del self.saved[key]
                continue
            if not self.eligible(obj, key[0]):
                continue
            before = self.memory.read(key[1], FIELD_SIZE)
            if before is None:
                failed = True
                continue
            if before != owned.last:
                self.saved[key] = owned._replace(last=None)
                continue
            if (self.memory.write(key[1], owned.original)
                    and self.memory.read(key[1], FIELD_SIZE) == owned.original):
                del self.saved[key]
            else:
                failed = True
        if failed or self.pending:
            raise RuntimeError('Loot restoration incomplete')
