"""Prepare the shared native zoom reader inputs using reflected object sizes."""

from .ads_category import address
from .generated_ads import ADS_ABI, MAX_TYPE_BYTES, PathsConfig


def object_parts(item):
    pointer, size = address(item), item.Class._get_struct_size()
    if type(size) is not int or not 8 <= size <= MAX_TYPE_BYTES:
        raise ValueError("invalid ADS type size")
    return pointer, size


def make_config(pc, manager, weapon):
    objects = (manager.CameraModeState, manager.CameraModeInputs, pc, weapon)
    parts = [object_parts(item) if item is not None else (0, 0) for item in objects]
    if any(not pointer for pointer, _ in parts[:3]):
        raise ValueError("ADS camera unavailable")
    return PathsConfig(ADS_ABI, 0, *(pointer for pointer, _ in parts),
                       *(size for _, size in parts))
