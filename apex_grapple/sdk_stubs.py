"""Installs the fake SDK; object families live separately to keep responsibilities small."""

import types
from collections import deque
from typing import Any


from sdk_mods import FakeOption, FakeNested, FakeButton, FakeHook, FakeMod, FakeKeybind
from sdk_objects import (vector, event, Mode, mapping, FakeMovement, FakeComponent, FakeCharacter,
                         FakeKismet, FakePoint, FakeSequence, FakeArms, player)
from sdk_niagara import FakeNiagara


def install() -> dict:
    """Registers the fake modules and returns the state the tests read and drive."""
    state: dict = {"misc": [], "warnings": [], "errors": [], "pc": None, "keybinds": {}, "mods": [],
                   "settings_exists": True, "kismet": FakeKismet(), "points": [],
                   "points_raise": False, "find_all_calls": [], "anim_instances": [],
                   "niagara_components": [], "niagara_raise": False,
                   "classes": [], "by_class": {}, "classes_raise": False, "extra_classes": {},
                   "destroyed": []}
    state["niagara"] = FakeNiagara(state)
    state["audio_calls"] = deque(maxlen=64)
    state["audio_stops"] = deque(maxlen=64)

    def audio_post(**kwargs):
        handle = object()
        state["audio_calls"].append((kwargs, handle))
        return handle

    audio_library = types.SimpleNamespace(PostWwiseEventOnActor=audio_post,
        Stop=lambda **kwargs: state["audio_stops"].append(kwargs["PlaybackInstance"]))
    # The game's own grapple assets, at the paths its settings name.
    state["objects"] = {
        ("AnimSequence",
         "/Game/PlayerCharacters/_Shared/Animation/1st/SharedSkills/AS_Grapple.AS_Grapple"): FakeSequence(),
        ("NiagaraSystem", "/Game/PlayerCharacters/_Shared/Skills/Effects/Systems/GrappleGrabber/"
                          "NS_Grapple_Beam.NS_Grapple_Beam"): types.SimpleNamespace(
            # As the game printed it on 2026-09-20, cut down to what the names are read from.
            # The eleven names the game really printed on 2026-09-20.
            ExposedParameters="{SortedParameterOffsets: ["
                              "{Name: 'User.Color Scale'}, {Name: 'User.Color'}, {Name: 'User.Lifetime'}, "
                              "{Name: 'User.Radius'}, {Name: 'User.Width'}, {Name: 'User.Target'}, "
                              "{Name: 'User.Emissive Scale'}, {Name: 'User.OffsetCamera'}, "
                              "{Name: 'User.Delay'}, {Name: 'User.Source'}, {Name: 'User.BeamColor'}]}"),
    }
    # The game's own shape, read from its key list on 2026-09-20: there is no grapple action, the
    # grapple lives on melee, and R3 is the button Kevin presses.
    state["mappings"] = [
        mapping("Action_Melee", "Gamepad_RightThumbstick"),
        mapping("Action_Melee", "V"),
        mapping("Action_Jump_HoldToGlide", "Gamepad_FaceButton_Bottom"),
        mapping("Action_Jump_HoldToGlide", "SpaceBar"),
    ]

    logging_module = types.ModuleType("unrealsdk.logging")
    logging_module.misc = lambda text: state["misc"].append(text)
    logging_module.warning = lambda text: state["warnings"].append(text)
    logging_module.error = lambda text: state["errors"].append(text)

    class WeakPointer:
        def __init__(self, obj: Any = None) -> None:
            self.obj = obj

        def __call__(self) -> Any:
            return None if getattr(self.obj, "destroyed", False) else self.obj

    unreal_module = types.ModuleType("unrealsdk.unreal")
    unreal_module.WeakPointer = WeakPointer
    unreal_module.FGbxDefPtr = lambda name, kind: types.SimpleNamespace(_name=name, _kind=kind)

    hooks_module = types.ModuleType("unrealsdk.hooks")
    hooks_module.Type = types.SimpleNamespace(POST="POST", PRE="PRE")
    hooks_module.Block = type("Block", (), {})

    def find_class(name: str) -> Any:
        if name in state["extra_classes"]:
            return state["extra_classes"][name]
        if name == "NiagaraFunctionLibrary":
            return types.SimpleNamespace(ClassDefaultObject=state["niagara"])
        if name == "GbxAudioBlueprintFunctionLibrary":
            return types.SimpleNamespace(ClassDefaultObject=audio_library)
        if name != "KismetSystemLibrary":
            raise ValueError(f"no class {name}")
        return types.SimpleNamespace(ClassDefaultObject=state["kismet"])

    unrealsdk_module = types.ModuleType("unrealsdk")
    unrealsdk_module.logging = logging_module
    unrealsdk_module.hooks = hooks_module
    unrealsdk_module.unreal = unreal_module
    unrealsdk_module.find_class = find_class

    def find_all(class_name: str, exact: bool = True) -> Any:
        state["find_all_calls"].append(class_name)
        if class_name == "/Script/Engine.AnimInstance":
            return iter(list(state["anim_instances"]))
        if class_name == "Class":
            if state["classes_raise"]:
                raise RuntimeError("the game is still loading")
            return iter([types.SimpleNamespace(Name=n) for n in state["classes"]])
        if class_name in state["by_class"]:
            return iter(list(state["by_class"][class_name]))
        if class_name == "NiagaraComponent":
            if state["niagara_raise"]:
                raise RuntimeError("the level is streaming")
            return iter(list(state["niagara_components"]))
        if state["points_raise"]:
            raise RuntimeError("the level is streaming")
        return iter(list(state["points"]))

    def find_object(class_name: str, path: str) -> Any:
        found = state["objects"].get((class_name, path))
        if found is None:
            raise ValueError(f"no object {path}")
        return found

    unrealsdk_module.find_object = find_object

    unrealsdk_module.find_all = find_all
    unrealsdk_module.make_struct = lambda name, **fields: types.SimpleNamespace(**fields)

    mods_base = types.ModuleType("mods_base")
    mods_base.BoolOption = FakeOption
    mods_base.SliderOption = FakeOption
    mods_base.NestedOption = FakeNested
    mods_base.ButtonOption = FakeButton
    mods_base.KeybindOption = FakeOption
    mods_base.SpinnerOption = FakeOption
    mods_base.get_pc = lambda **kwargs: state["pc"]
    mods_base.hook = lambda path, kind, hook_identifier="": (lambda fn: FakeHook(fn, path, hook_identifier))
    mods_base.keybind = lambda identifier, key=None, callback=None, **kwargs: FakeKeybind(
        state, identifier, key, callback)

    def build_mod(**kwargs: Any) -> FakeMod:
        made = FakeMod(state, **kwargs)
        state["mods"].append(made)
        return made

    mods_base.Mod = FakeMod
    mods_base.build_mod = build_mod

    import sys
    for name, module in {
        "unrealsdk": unrealsdk_module,
        "unrealsdk.logging": logging_module,
        "unrealsdk.hooks": hooks_module,
        "unrealsdk.unreal": unreal_module,
        "mods_base": mods_base,
    }.items():
        sys.modules[name] = module
    return state
