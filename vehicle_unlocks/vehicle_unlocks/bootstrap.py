"""Elect one identical reward owner from the independently bundled copies."""
from importlib import import_module
import sys
from types import ModuleType

PROTOCOL = 3
STATE = '_kevin_vehicle_unlocks_runtime_v1'


def ensure():
    selected = sys.modules.get(STATE)
    if selected is not None:
        if getattr(selected, 'protocol', None) != PROTOCOL:
            raise RuntimeError('Vehicle reward runtime incompatible')
        return selected
    selected = ModuleType(STATE)
    selected.protocol = PROTOCOL
    for name in ('service', 'panel', 'text', 'menu', 'protection_runtime'):
        setattr(selected, name, import_module(f'{__package__}.{name}'))
    sys.modules[STATE] = selected
    return selected
