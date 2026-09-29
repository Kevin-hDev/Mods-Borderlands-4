"""A fake game for Hunter Change's tests, built on what the game showed (docs/reverse-and-change-hunters, essais 22 to
31): each hunter's body and head pickers live the whole session and are shared by every game of that hunter; a
character holds one choice per selection, a chosen part (kind def) or Default, which names the picker's current
default; the part setter takes a text, chooses what it names and leaves every other selection Default, then builds the
body from the chosen body part or else the body picker's default; the first-person legs hang from the body mesh."""

import enum
import types
from typing import Any

from sdk_stubs import FakeDefPtr

GESTALT = types.SimpleNamespace(_path_name=lambda: "/Script/GbxGame.GbxActorPartDef_Gestalt")
COLOUR = "Cosmetics_Colorization_Primary"
rule = {"refuse": None, "ignore": None, "setter_refused": False, "scale_refused": False}


class EGbxActorPartChoiceType(enum.IntEnum):
    """As the SDK hands the game's enum: str() gives the number; the names are the field map's."""
    Default = 0
    def_ = 1
    Param = 2


EGbxActorPartChoiceType.def_._name_ = "def"


class Picker:
    def __init__(self, name: str, default: str) -> None:
        self._name, self.PickableParts = name, [FakeDefPtr(f"{name}01_Prison", GESTALT)]
        self.writes: list[str] = []
        object.__setattr__(self, "DefaultPart", FakeDefPtr(default, GESTALT))

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "DefaultPart":
            if rule["refuse"] == value._name:
                raise RuntimeError("Ref type does not inherit")
            self.writes.append(value._name)
            if rule["ignore"] == value._name:
                return
        object.__setattr__(self, name, value)


class Choice:
    def __init__(self, picker: Picker, part: str | None = None) -> None:
        self.picker, self.part = picker, part
        self.type = EGbxActorPartChoiceType.Default if part is None else EGbxActorPartChoiceType.def_

    @property
    def ChosenDef(self) -> FakeDefPtr:
        return self.picker.DefaultPart if self.part is None else FakeDefPtr(self.part)


class Legs:
    Name = "FirstPersonLegs"

    def __init__(self) -> None:
        self.RelativeScale3D = types.SimpleNamespace(X=1.0, Y=1.0, Z=1.0)

    def SetRelativeScale3D(self, vector: Any) -> None:
        if rule["scale_refused"]:
            raise RuntimeError("no")
        self.RelativeScale3D = vector


class Character:
    """A class instance, as the game's are, so that WeakPointer can follow it."""

    def __init__(self, selections: list, legs: Legs) -> None:
        self.GbxActorPartOwnerState = types.SimpleNamespace(ReplicatedSelections=selections)
        self.Mesh = types.SimpleNamespace(AttachChildren=[types.SimpleNamespace(Name="FirstPersonArms"), legs],
                                          GestaltMeshParts=[])


_pickers: dict[str, tuple[Picker, Picker, Picker]] = {}
colour_picker = Picker(COLOUR, "None")
handed: list[str] = []


def pickers_of(code: str) -> tuple[Picker, Picker, Picker]:
    """The body, head and skin pickers of a hunter, made once for the session."""
    if code not in _pickers:
        # The game spells two picker names differently from their parts (read in essai 24).
        spelled = {"CorpoHacker": "Corpohacker", "RoboDealer": "Robodealer"}.get(code, code)
        _pickers[code] = (Picker(f"Cosmetics_{spelled}_Body", f"Cosmetics_{code}_Body00_Default"),
                          Picker(f"Cosmetics_{spelled}_Head", f"Cosmetics_{code}_Head00_Default"),
                          Picker(f"Cosmetics_{spelled}_Skin", f"Cosmetics_{code}_SkinFilter00_Default"))
    return _pickers[code]


def id_words(game: str) -> types.SimpleNamespace:
    words = [int(game[index:index + 8], 16) for index in range(0, 32, 8)]
    return types.SimpleNamespace(**{name: word - (1 << 32) if word >= 1 << 31 else word
                                    for name, word in zip("ABCD", words)})


def load(state: dict, code: str, game: str, outfit: str = "gap,") -> Character:
    """A game of `code` loaded with the outfit its save holds: a new character, the session's pickers."""
    selections = [types.SimpleNamespace(SelectorDef=picker, choices=[Choice(picker)])
                  for picker in (*pickers_of(code), colour_picker)]
    character = Character(selections, Legs())
    player_state = types.SimpleNamespace(ReplicatedCharacterDef=f"Char_{code}", ActiveCharGuid=id_words(game))

    def setter(_actor_type: str, text: str) -> None:
        if rule["setter_refused"]:
            raise RuntimeError("no")
        handed.append(text)
        named = dict(item[:-1].split("[", 1) for item in text.removeprefix("gap,").split(",") if item)
        for selection in selections:
            selection.choices = [Choice(selection.SelectorDef, named.get(selection.SelectorDef._name))]
        body = selections[0].SelectorDef
        character.Mesh.GestaltMeshParts = [types.SimpleNamespace(Name=named.get(body._name, body.DefaultPart._name))]

    player_state.ServerSetGbxActorParts = setter
    setter("character", outfit)
    handed.clear()
    state["pc"] = types.SimpleNamespace(OakCharacter=character, Pawn=character, PlayerState=player_state)
    return character


def body_drawn(character: Character) -> str:
    return character.Mesh.GestaltMeshParts[0].Name


def legs_scale(character: Character) -> float:
    return character.Mesh.AttachChildren[1].RelativeScale3D.Z


def outfit_worn(character: Character) -> str:
    """The text a save would write now (essai 30): the chosen parts in order."""
    entries = [f"{selection.SelectorDef._name}[{selection.choices[0].part}]"
               for selection in character.GbxActorPartOwnerState.ReplicatedSelections
               if selection.choices[0].part is not None]
    return "gap," + ",".join(entries)
