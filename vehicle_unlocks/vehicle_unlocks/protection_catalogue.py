"""Read semantic DLC fields; DLCDataLayer references legitimately change on travel."""
from itertools import islice
import struct
from . import protection_config as cfg


class CataloguePending(RuntimeError):
    """The validated catalogue exists but has not loaded any definitions yet."""


def validate_layout(definition):
    if definition is None:
        raise ValueError('DLC layout unavailable')
    fields = tuple(islice(definition._properties(), cfg.MAX_FIELDS + 1))
    measured = tuple((str(p.Name), p.Offset_Internal, p.ElementSize)
                     for p in fields if str(p.Name) in {f[0] for f in cfg.FIELDS})
    if len(fields) > cfg.MAX_FIELDS or measured != cfg.FIELDS:
        raise ValueError('DLC layout differs')


class Catalogue:
    def __init__(self, memory, reward_type, trace=lambda _: None):
        self.memory = memory
        self.trace = trace
        self.base, _ = memory.identify()
        for rva, expected in cfg.BLOCKS:
            if memory.read(self.base + rva, len(expected)) != expected:
                raise ValueError('Native DLC contract differs')
        if type(reward_type) is not int or not cfg.MIN_ADDRESS <= reward_type < cfg.MAX_ADDRESS:
            raise ValueError('Reward type unavailable')
        self.kind = struct.pack('<Q', reward_type)

    def capture(self):
        read = self.memory.read
        cache_bytes = read(self.base + cfg.CACHE_RVA, 8)
        cache, = struct.unpack('<Q', cache_bytes)
        header = read(cache + cfg.ARRAY_OFFSET, 16)
        data, count, capacity = struct.unpack('<Qii', header)
        # Cold mod activation precedes DLC loading; never relax malformed bounds.
        if data == count == capacity == 0:
            if (read(self.base + cfg.CACHE_RVA, 8) == cache_bytes
                    and read(cache + cfg.ARRAY_OFFSET, 16) == header):
                raise CataloguePending()
            raise ValueError('DLC catalogue changed during read')
        if not 1 <= count <= capacity <= cfg.MAX_DLC:
            self.trace(f'protection catalogue_invalid count={count} capacity={capacity}')
            raise ValueError('DLC catalogue bound exceeded')
        pointers = read(data, count * 8)
        addresses = tuple(p for p, in struct.iter_unpack('<Q', pointers))
        if len(set(addresses)) != count:
            raise ValueError('Duplicate DLC definition')
        identity, targets = [], {}
        for address in addresses:
            raw = read(address, cfg.DEFINITION_SIZE)
            name_raw = raw[cfg.NAME_OFFSET:cfg.NAME_OFFSET + 8]
            name = self.memory.name(name_raw)
            link = raw[cfg.LINK_OFFSET:cfg.LINK_OFFSET + cfg.LINK_SIZE]
            fact = raw[cfg.FACT_OFFSET:cfg.FACT_OFFSET + cfg.FACT_SIZE]
            if name in cfg.DLC:
                if name in targets or link[8:16] != self.kind:
                    self.trace(f'protection definition_invalid dlc={name} duplicate={int(name in targets)} '
                               f'type_matches={int(link[8:16] == self.kind)}')
                    raise ValueError('Promotional definition differs')
                # Partial link writes must remain readable to permit exact rollback.
                targets[name] = address + cfg.LINK_OFFSET, link
                link = bytes(cfg.LINK_SIZE)
            else:
                # Other rewards populate type/instance caches during loading. We do
                # not own or write them; retain their reward name as the identity.
                link = link[:8] + bytes(cfg.LINK_SIZE - 8)
            identity.append((address, name_raw, link, fact))
        if set(targets) != set(cfg.DLC):
            self.trace(f'protection definitions_missing found={len(targets)} expected={len(cfg.DLC)}')
            raise ValueError('Promotional definitions unavailable')
        if (read(self.base + cfg.CACHE_RVA, 8) != cache_bytes
                or read(cache + cfg.ARRAY_OFFSET, 16) != header or read(data, count * 8) != pointers):
            raise ValueError('DLC catalogue changed during read')
        return (cache_bytes, header, pointers, tuple(identity)), targets

    def validate_originals(self, targets):
        for key, (_, link) in targets.items():
            named = self.memory.name(link[:8]) == cfg.DLC[key].reward
            pointer = struct.unpack('<Q', link[16:])[0]
            resolved = cfg.MIN_ADDRESS <= pointer < cfg.MAX_ADDRESS
            # The native resolver explicitly accepts zero and loads by name on first use.
            # Protect before that first use; waiting for resolution can allow removal first.
            if not named or (pointer != 0 and not resolved):
                self.trace(f'protection original_invalid dlc={key} name_matches={int(named)} '
                           f'resolved={int(resolved)}')
                raise ValueError('Original vehicle reward differs')
