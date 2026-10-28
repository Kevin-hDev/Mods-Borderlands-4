"""Atomic group of data links; unknown changes are never overwritten."""
from . import protection_config as cfg


def blank(original):
    return bytes(8) + original[8:16] + bytes(8)


class Links:
    def __init__(self, capture, write):
        self.capture, self.write = capture, write
        self.identity, self.original = capture()
        if (not 1 <= len(self.original) <= len(cfg.DLC)
                or any(key not in cfg.DLC or len(value[1]) != cfg.LINK_SIZE
                       or not any(value[1][:8]) or not any(value[1][8:16])
                       for key, value in self.original.items())):
            raise ValueError('Named original links required')
        self.active = ()
        self.failed = False

    def expected(self, selected):
        return {key: (address, blank(value) if key in selected else value)
                for key, (address, value) in self.original.items()}

    def check(self):
        if self.failed or self.capture() != (self.identity, self.expected(self.active)):
            raise RuntimeError('Protection state changed')

    def set(self, selected):
        if (type(selected) is not tuple or len(selected) > len(self.original)
                or any(key not in self.original for key in selected)
                or len(set(selected)) != len(selected)):
            raise ValueError('Invalid link selection')
        self.check()
        before, after = self.expected(self.active), self.expected(selected)
        touched = []
        try:
            for key in self.original:
                address, value = after[key]
                if value == before[key][1]:
                    continue
                touched.append(key)  # A failing setter may already have changed part of the link.
                self.write(address, before[key][1], value)
            if self.capture() != (self.identity, after):
                raise RuntimeError('Link readback differs')
        except Exception:
            try:
                for key in reversed(touched):
                    identity, current = self.capture()
                    address, value = current[key]
                    old, new = before[key][1], after[key][1]
                    if (identity != self.identity or address != before[key][0]
                            or len(value) != cfg.LINK_SIZE
                            or any(c not in (a, b) for c, a, b in zip(value, old, new))):
                        raise RuntimeError('Foreign link during rollback')
                    if value != old:
                        self.write(address, value, old)
                if self.capture() != (self.identity, before):
                    raise RuntimeError('Rollback incomplete')
            except Exception:
                self.failed = True
                raise
            raise
        self.active = selected
