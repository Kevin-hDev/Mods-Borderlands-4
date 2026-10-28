"""UMG tree doubles: verify attachment, styling calls and form/view integration, not visual fidelity."""

import copy
from types import SimpleNamespace as NS
import panel_fixture as pf
import unrealsdk

created = []  # every constructed node, in order, for the tests to inspect


class Struct:
    """Any Unreal struct: unknown fields spring into existence as nested structs, set fields are kept."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        value = Struct()
        setattr(self, name, value)
        return value


class Enum:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, member):
        if member.startswith("__"):
            raise AttributeError(member)
        return f"{self.name}.{member}"


class Node(pf.Widget):
    def __init__(self, kind, owner):
        super().__init__()
        self.kind, self.owner, self.children, self.attributes, self.slots = kind, owner, [], {}, []
        self.Font = Struct()
        created.append(self)

    def __getattr__(self, name):
        if name.startswith("Set") or name.startswith("AddChildTo") or name == "AddChild":
            return lambda *args: self._call(name, args)
        if name[:1].isupper():
            value = Struct()
            setattr(self, name, value)
            return value
        raise AttributeError(name)

    def _call(self, name, args):
        if name == "SetContent":
            self.children[:] = [args[0]]
            return None
        if name.startswith("AddChild"):
            self.children.append(args[0])
            slot = Node("Slot", self)
            self.slots.append(slot)
            return slot
        self.attributes[name] = copy.deepcopy(args) if name != "SetBrushFromTexture" else args
        return None

    def SetText(self, text):
        self.text = text


def install():
    created.clear()
    unrealsdk.construct_object = Node
    unrealsdk.find_enum = Enum
