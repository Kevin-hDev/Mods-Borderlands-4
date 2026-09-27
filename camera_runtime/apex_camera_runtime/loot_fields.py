"""Refresh live container fields without retaining Unreal object references."""
import math
import struct

from .loot_constants import (BASE_DISTANCE, FIELD_OFFSET, FIELD_SIZE, LOOT_DEFINITION,
                             MAX_MULTIPLIER, MAX_OBJECTS, MAX_PATH, MAX_SCAN)


class LootFields:
    def __init__(self, objects, memory):
        self.objects = objects
        self.memory = memory
        # Keys are scalar identities; None marks a competing write until that object unloads.
        self.saved = {}

    @property
    def pending(self):
        return any(last is not None for _original, last in self.saved.values())

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

    def live(self):
        seen = set()
        complete = True
        for index, obj in enumerate(self.objects()):
            if index >= MAX_SCAN:
                raise RuntimeError('Loot scan budget exceeded')
            key = self.identity(obj)
            if key is not None:
                seen.add(key)
                if self.eligible(obj, key[0]):
                    yield key
            else:
                complete = False
        # Only a completed live enumeration proves that a previous identity disappeared.
        for key in tuple(self.saved):
            if complete and key not in seen:
                del self.saved[key]

    @staticmethod
    def valid(data):
        if data is None or len(data) != FIELD_SIZE:
            return False
        flag, distance = struct.unpack('<Bf', data)
        return flag in (0, 1) and math.isfinite(distance) and 0 <= distance <= 3000

    def apply(self, distance):
        if (not math.isfinite(distance)
                or not BASE_DISTANCE <= distance <= BASE_DISTANCE * MAX_MULTIPLIER):
            raise ValueError('Invalid loot range')
        for key in self.live():
            before = self.memory.read(key[1], FIELD_SIZE)
            if not self.valid(before):
                continue
            if key in self.saved:
                original, last = self.saved[key]
                if last is None or before != last:
                    self.saved[key] = (original, None)
                    continue
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
            self.saved[key] = (original, target)
            if (not self.memory.write(key[1], target)
                    or self.memory.read(key[1], FIELD_SIZE) != target):
                observed = self.memory.read(key[1], FIELD_SIZE)
                self.saved[key] = (original, observed if observed is not None else target)
                raise RuntimeError('Loot update refused')

    def restore(self):
        failed = False
        for key in self.live():
            if key not in self.saved:
                continue
            original, last = self.saved[key]
            if last is None:
                continue
            before = self.memory.read(key[1], FIELD_SIZE)
            if before is None:
                failed = True
                continue
            if before != last:
                self.saved[key] = (original, None)
                continue
            if (self.memory.write(key[1], original)
                    and self.memory.read(key[1], FIELD_SIZE) == original):
                del self.saved[key]
            else:
                failed = True
        if failed or self.pending:
            raise RuntimeError('Loot restoration incomplete')
