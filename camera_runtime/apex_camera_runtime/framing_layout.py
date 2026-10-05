"""Qualify reflected body fields once per live identity, never cache coordinates."""
import ctypes
from .ads_paths_reader import object_parts
from .generated_ads import FramingContext, ObjectId, VIEW_ABI


def field(owner, name, kind, size):
    prop = owner.Class._find_prop(name)
    offset = prop.Offset_Internal
    total = object_parts(owner)[1]
    if (type(offset) is not int or not 0 <= offset <= total - size
            or prop.ElementSize != size or prop.ArrayDim != 1 or str(prop.Class.Name) != kind):
        raise ValueError("Camera body layout unavailable")
    return offset


def make_context(actor, root, identities, values):
    vector = root.Class._find_prop("RelativeLocation").Struct
    if str(vector.Name) != "Vector" or vector._get_struct_size() != 3 * ctypes.sizeof(ctypes.c_double):
        raise ValueError("Camera body vector unavailable")
    result = FramingContext()
    result.abi, result.size = VIEW_ABI, ctypes.sizeof(result)
    result.references = (ObjectId * 4)(*identities)
    result.actor_size = object_parts(actor)[1]
    result.root_size = object_parts(root)[1]
    result.root_offset = field(actor, "RootComponent", "ObjectProperty", 8)
    result.capsule_offset = field(actor, "CapsuleComponent", "ObjectProperty", 8)
    result.location_offset = field(root, "RelativeLocation", "StructProperty", 24)
    result.parent_offset = field(root, "AttachParent", "ObjectProperty", 8)
    result.values[:] = values
    return result
