"""Installs a fake SDK and a fake game for the beam attack's tests: no game, no library to install."""

import enum
import math
import sys
import types

PARAM, OUT, RETURN = 0x80, 0x100, 0x400
DATA_TYPE, TYPE_TYPE, FORCE_TYPE, EFFECT_TYPE = 12293, 12290, 4026532048, 777
FIRE_BEAM = "/Game/Gear/Weapons/_Shared/Effects/Systems/GenericLaser/NS_Beam_Energy_Incendiary.NS_Beam_Energy_Incendiary"
HAND_POSE = "/Game/PlayerCharacters/_Shared/Animation/1st/BeamAtk/AS_Beam_Hold.AS_Beam_Hold"
BODY_POSE = "/Game/PlayerCharacters/_Shared/Animation/1st/BeamAtk/AS_Beam_Body.AS_Beam_Body"


class Named:
    """A class or a struct: its name, its path when it has one, and the fields it holds."""

    def __init__(self, name, path=None, fields=()):
        self.Name = name
        self._path = path
        self.fields = list(fields)

    def _path_name(self):
        return self._path

    def _properties(self):
        return iter(self.fields)


class Prop:
    def __init__(self, name, kind, flags=PARAM, **extra):
        self.Name = name
        self.Class = Named(kind)
        self.PropertyFlags = flags
        for key, value in extra.items():
            setattr(self, key, value)


def struct(name, path, fields=(), flags=PARAM):
    return Prop(name, "StructProperty", flags, Struct=Named(path.rsplit(".", 1)[-1], path, fields))


def handle(name, kind):
    return Prop(name, "GameDataHandleProperty", TypeHandle=kind)


def cause_damage(extra=()):
    """DamageStatics.CauseDamage as read in game on 2026-10-01: twenty-two parameters, no return value."""
    effect = [handle("Handle", EFFECT_TYPE)]
    force = [Prop("Selection", "EnumProperty"), handle("attribute", FORCE_TYPE), Prop("force", "FloatProperty")]
    return [
        Prop("DamageCauser", "ObjectProperty"), Prop("DamageInstigator", "ObjectProperty"),
        handle("DamageData", DATA_TYPE), Prop("DamageTarget", "ObjectProperty"),
        Prop("DamageOverride", "FloatProperty"),
        struct("TargetedHitInfo", "/Script/Engine.HitResult", [Prop("Distance", "FloatProperty")], PARAM | OUT),
        handle("DamageTypeOverride", TYPE_TYPE),
        struct("DamageSourceOverride", "/Script/GbxGame.DamageSourceContainer"),
        Prop("bAppendDamageSource", "BoolProperty"), Prop("SourceActorOverride", "ObjectProperty"),
        struct("SourceLocationOverride", "/Script/CoreUObject.Vector"),
        struct("SourceRotationOverride", "/Script/CoreUObject.Rotator"),
        Prop("SourceSocketOverride", "NameProperty"), Prop("DamageRadiusOverride", "FloatProperty"),
        struct("DamageExtentOverride", "/Script/CoreUObject.Vector"),
        struct("ImpactForceOverride", "/Script/GbxGame.ForceSelection", force),
        struct("SourceEffectOverride", "/Script/GbxGame.ImpactEffectSelection", effect),
        struct("ImpactEffectOverride", "/Script/GbxGame.ImpactEffectSelection", effect),
        Prop("DurationOverride", "FloatProperty"),
        struct("DamageTags", "/Script/GbxGame.DamageTags", flags=PARAM | OUT),
        Prop("bInheritTimeDilation", "BoolProperty"), Prop("bServerAuthorityOverride", "BoolProperty"),
        *extra,
    ]


class Made:
    """A struct as make_struct gives it: named, and taking whatever field is set on it."""

    def __init__(self, name, **fields):
        self.made_from = name
        for key, value in fields.items():
            setattr(self, key, value)


def spot(vector):
    return vector.X, vector.Y, vector.Z


class Actor:
    """A character of the game: its name, where it stands, whether it is dead. Equal only to itself, as two of
    the game's objects are (two SimpleNamespace of the same fields would be equal)."""

    def __init__(self, name, at=(0.0, 0.0, 0.0), dead=False):
        self.Name, self.at = name, at
        self.HealthState = types.SimpleNamespace(bCurrentlyDead=dead)

    def K2_GetActorLocation(self):
        return types.SimpleNamespace(X=self.at[0], Y=self.at[1], Z=self.at[2])


# The game's own enum, as read in its field map on 2026-10-02: lower-case names.
ETeamAttitude = enum.IntEnum("ETeamAttitude", {"friendly": 0, "neutral": 1, "hostile": 2})


def met(actor, distance, at=None):
    """A ray's answer: that actor met that far, at that spot when the game says where."""
    result = types.SimpleNamespace(HitObjectHandle=types.SimpleNamespace(Actor=actor), Distance=distance)
    if at is not None:
        result.ImpactPoint = types.SimpleNamespace(X=at[0], Y=at[1], Z=at[2])
    return True, result


class Beam:
    """A beam component: remembers where it was put, what it was told, and what was done to it."""

    def __init__(self, state):
        self.state = state
        self.bAutoDestroy = False
        self.poses, self.targets, self.positions = [], [], []
        self.refuses_target = False
        # What the game says of it once lit: whether it runs, and how big it is drawn.
        self.active, self.radius = True, 2500.0

    def IsActive(self):
        return self.active

    def K2_SetWorldLocationAndRotation(self, location, rotation, sweep, hit, teleport):
        self.poses.append((spot(location), (rotation.Pitch, rotation.Yaw)))

    def SetVariableVec3(self, name, value):
        if self.refuses_target:
            raise AttributeError("no such function")
        self.targets.append((name, spot(value)))

    def SetVariablePosition(self, name, value):
        self.positions.append((name, spot(value)))

    def Activate(self, reset):
        self.aimed_when_lit = bool(self.poses and (self.targets or self.positions))
        self.state["events"].append("LIT")

    def Deactivate(self):
        self.state["events"].append("OFF")

    def GetOwner(self):
        return "owner"

    def K2_DestroyComponent(self, owner):
        self.state["events"].append("REMOVED")
        self.state["gone"].add(id(self))


class ArmsAnimation:
    """An animation instance, the arms' or the body's: what it was asked to play and to stop. Only the arms' writes
    its moves in the game's events."""

    def __init__(self, state, mesh, gives="a montage", in_events=True):
        self.state, self.Outer = state, mesh
        self.played, self.stopped = [], []
        self.gives = gives
        self.in_events = in_events
        self.refuses = False

    def PlaySlotAnimationAsDynamicMontage(self, **asked):
        if self.refuses:
            raise RuntimeError("the arms refuse")
        if self.in_events:
            self.state["events"].append("HAND UP")
        self.played.append(asked)
        return self.gives

    def Montage_Stop(self, blend_out, montage):
        if self.in_events:
            self.state["events"].append("HAND DOWN")
        self.stopped.append((blend_out, montage))


class Option:
    """As mods_base's options: a value, its bounds (a slider) or its choices (a spinner), and what a menu shows."""

    def __init__(self, identifier, value, *args, **kwargs):
        self.identifier, self.value, self.default_value = identifier, value, value
        self.args, self.kwargs = args, kwargs
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.step, self.is_integer = kwargs.get("step", 1), kwargs.get("is_integer", True)
        self.is_hidden = kwargs.get("is_hidden", False)
        if len(args) == 1:
            self.choices = args[0]
        elif args:
            self.min_value, self.max_value = args[:2]


def _refused(option, value):
    sys.modules["unrealsdk"].logging.error(
        f"'{value}' is not a valid value for option '{option.identifier}', sticking with the default")


class SliderOption(Option):
    """Loads from the settings file as the game's own does (mods_base/options.py, read on 2026-10-01): any number
    is taken, in range or not, and only a ValueError is caught."""

    def _from_json(self, value):
        try:
            self.value = float(value)
            if self.is_integer:
                self.value = round(self.value)
        except ValueError:
            _refused(self, value)


class SpinnerOption(Option):
    def _from_json(self, value):
        value = str(value)
        if value in self.choices:
            self.value = value
        else:
            _refused(self, value)


class BoolOption(Option):
    def _from_json(self, value):
        self.value = bool(value) and not (isinstance(value, str) and value.strip().lower() == "false")


class KeybindOption(Option):
    """As mods_base's KeybindOption: made from a bind, a change of the option reaches the bind, not the reverse."""

    @classmethod
    def from_keybind(cls, bind):
        option = cls(bind.identifier, bind.key, display_name=bind.display_name, description=bind.description,
                     is_hidden=bind.is_hidden)
        option.default_value = bind.default_key
        option.bind = bind
        return option

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "value" and "bind" in self.__dict__:
            self.bind.key = value


class NestedOption:
    def __init__(self, identifier, children, **kwargs):
        self.identifier, self.children = identifier, children
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")


class Keybind:
    """As mods_base's keybind: a key the player may change, and the callback the SDK runs on its events."""

    def __init__(self, identifier, key, callback, **kwargs):
        self.identifier, self.key, self.default_key, self.callback = identifier, key, key, callback
        self.display_name = kwargs.get("display_name", identifier)
        self.description = kwargs.get("description", "")
        self.is_hidden = kwargs.get("is_hidden", False)
        self.event_filter = kwargs.get("event_filter", "IE_Pressed")


class Mod:
    """As mods_base's Mod: switched on and off, its settings saved; a save fails while state["refuse_saves"]."""

    def __init__(self, state, **kwargs):
        self.__dict__.update(kwargs)
        self.state, self.settings_file, self.is_enabled = state, None, False

    def enable(self):
        self.is_enabled = True
        self.on_enable()

    def disable(self):
        self.is_enabled = False
        self.on_disable()

    def save_settings(self):
        if self.state["refuse_saves"]:
            raise OSError("disk full")
        self.state["saves"] += 1

    def iter_display_options(self):
        yield from self.options


class Enum:
    """Any of the game's enums: each member is its own name."""

    def __getattr__(self, name):
        return name


def install() -> dict:
    """Registers the fake modules and returns the state the tests read and drive."""
    state: dict = {"log": [], "errors": [], "events": [], "gone": set(), "hits": [], "spawns": [], "beams": [],
                   "pc": None, "props": cause_damage(), "hit_raises": None,
                   "objects": {FIRE_BEAM: "the fire beam", HAND_POSE: "the hand pose", BODY_POSE: "the body pose"},
                   "camera_mode": "Default",
                   "loads": [], "load_classes": [], "in_archives": True, "trace": (False, None), "anim_instances": [],
                   "mods": [], "scans": 0, "scanned": [], "rays": [], "spawn_gives": "beam",
                   # A ray's answer by its two ends, when a test's world holds more than one thing: a function of
                   # (start, end) giving (met, result), or None to leave the ray to state["trace"].
                   "line": None,
                   # What the game says one actor is to the player, by the actor's id; hostile when not told.
                   "attitudes": {}, "attitude_calls": [], "attitude_raises": None,
                   # The game's objects of a class, by its name: the window's side, and the game's characters (none
                   # until a test puts some; None, and their walk fails). Then the mod's saves.
                   "all": {"OakCharacter": []}, "saves": 0, "refuse_saves": False,
                   # Every walk of the game's objects asked for: (the class, exact or not).
                   "finds": []}

    def cause(**arguments):
        state["events"].append("HIT")
        state["hits"].append(arguments)
        if state["hit_raises"] is not None:
            raise state["hit_raises"]

    def spawn(context, system, location, rotation, scale, auto_destroy, auto_activate, pooling, precull):
        made = Beam(state)
        state["spawns"].append((context, system, spot(location), auto_destroy, auto_activate))
        state["beams"].append(made)
        # What the game hands back: the beam, the beam in a tuple, an empty tuple or nothing.
        return {"beam": made, "tuple": (made,), "empty": (), "nothing": None}[state["spawn_gives"]]

    def find_object(kind, path):
        if path not in state["objects"]:
            raise ValueError("not found")
        return state["objects"][path]

    def get_asset(data):
        state["loads"].append(f"{data.PackageName}.{data.AssetName}")
        state["load_classes"].append(f"{data.AssetClassPath.PackageName}.{data.AssetClassPath.AssetName}")
        if state["in_archives"]:
            state["objects"].setdefault(f"{data.PackageName}.{data.AssetName}", "a loaded beam")

    def find_all(name, exact=True):
        state["finds"].append((name, exact))
        if name in state["all"]:
            return iter(state["all"][name])
        state["scans"] += 1
        state["scanned"].append((name, exact))
        return iter(state["anim_instances"])

    def bounds(component, origin, extent, radius):
        # As the SDK hands back a function without a result: an ellipsis, then what the function wrote.
        return ..., origin, extent, component.radius

    def line(*arguments):
        state["rays"].append(arguments)
        state.setdefault("traced", []).append(arguments[2])
        answer = state["line"](spot(arguments[1]), spot(arguments[2])) if state["line"] is not None else None
        found, result = answer if answer is not None else state["trace"]
        return found, [], result

    def attitude(source, target):
        state["attitude_calls"].append((source, target))
        if state["attitude_raises"] is not None:
            raise state["attitude_raises"]
        return state["attitudes"].get(id(target), ETeamAttitude.hostile)

    classes = {
        "DamageStatics": types.SimpleNamespace(_find=lambda name: Named("CauseDamage", fields=state["props"]),
                                               ClassDefaultObject=types.SimpleNamespace(CauseDamage=cause)),
        "KismetSystemLibrary": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
            LineTraceSingle=line, GetComponentBounds=bounds)),
        "GbxTeamFunctionLibrary": types.SimpleNamespace(
            ClassDefaultObject=types.SimpleNamespace(GetAttitudeTowards=attitude)),
        "NiagaraFunctionLibrary": types.SimpleNamespace(
            ClassDefaultObject=types.SimpleNamespace(SpawnSystemAtLocation=spawn)),
        "AssetRegistryHelpers": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(GetAsset=get_asset)),
        "NiagaraSystem": Named("NiagaraSystem", "/Script/Niagara.NiagaraSystem"),
        "AnimSequence": Named("AnimSequence", "/Script/Engine.AnimSequence"),
        # The game's console keys, which the window's COMMANDS page must refuse.
        "InputSettings": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
            ConsoleKeys=[types.SimpleNamespace(KeyName="Tilde"), types.SimpleNamespace(KeyName="F10")])),
    }
    sdk = types.ModuleType("unrealsdk")
    sdk.find_class = classes.__getitem__
    sdk.find_object, sdk.find_all, sdk.make_struct = find_object, find_all, Made
    sdk.find_enum = lambda name: Enum()
    sdk.logging = types.SimpleNamespace(info=state["log"].append, error=state["errors"].append)
    unreal = types.ModuleType("unrealsdk.unreal")
    unreal.FGameDataHandle = lambda kind, name: ("handle", kind, name)
    unreal.WeakPointer = lambda obj: (lambda: None if id(obj) in state["gone"] else obj)
    sdk.unreal = unreal
    hooks = types.ModuleType("unrealsdk.hooks")
    hooks.Type = types.SimpleNamespace(POST="post")
    base = types.ModuleType("mods_base")
    base.get_pc = lambda possibly_loading=False: state["pc"]
    base.BoolOption, base.SliderOption, base.SpinnerOption = BoolOption, SliderOption, SpinnerOption
    base.KeybindOption, base.NestedOption, base.keybind = KeybindOption, NestedOption, Keybind
    base.hook = lambda path, kind, hook_identifier=None: (
        lambda function: types.SimpleNamespace(path=path, kind=kind, identifier=hook_identifier, run=function))

    def build_mod(**kwargs):
        made = Mod(state, **kwargs)
        state["mods"].append(made)
        return made

    base.build_mod = build_mod
    sys.modules.update({"unrealsdk": sdk, "unrealsdk.unreal": unreal, "unrealsdk.hooks": hooks, "mods_base": base})
    for name in [name for name in sys.modules if name == "benefix_ohm_attack" or name.startswith("benefix_ohm_attack.")]:
        del sys.modules[name]
    return state


def player(state, level=10):
    """Puts a player on foot in the fake game, looking along X from (0, 0, 50); returns (controller, character)."""
    # Named as a character of the game is: only being the player himself keeps him from being a target.
    character = types.SimpleNamespace(Name="Char_Player_0")
    # The world and the first-person arms each have a field of view: the same one here, until a test sets them apart.
    state["fov"] = state["arms_fov"] = 90.0

    class CameraModeState:
        ViewModelFOV = property(lambda self: state["arms_fov"])

    # Where the camera looks, (pitch, yaw) in degrees: straight along X until a test turns it.
    state["look"] = (0.0, 0.0)
    camera = types.SimpleNamespace(GetCameraLocation=lambda: types.SimpleNamespace(X=0.0, Y=0.0, Z=50.0),
                                   GetCameraRotation=lambda: types.SimpleNamespace(Pitch=state["look"][0],
                                                                                   Yaw=state["look"][1]),
                                   GetActorCameraMode=lambda actor: state["camera_mode"],
                                   GetFOVAngle=lambda: state["fov"], CameraModeState=CameraModeState())
    state["body_sockets"] = {"FX_L_Hand": (30.0, -15.0, 120.0), "L_Hand": (28.0, -14.0, 118.0)}
    body = types.SimpleNamespace(
        Name="CharacterMesh0", Outer=character, DoesSocketExist=lambda name: name in state["body_sockets"],
        GetSocketLocation=lambda name: types.SimpleNamespace(**dict(zip("XYZ", state["body_sockets"][name]))))
    state["body_animation"] = ArmsAnimation(state, body, gives="a body montage", in_events=False)
    body.GetAnimInstance = lambda: state["body_animation"]
    character.Mesh = body
    tracks = [types.SimpleNamespace(ExperienceId="{Name: 'Specialization'}", ExperienceLevel=3),
              types.SimpleNamespace(ExperienceId="{Name: 'Character'}", ExperienceLevel=level)]
    state["pc"] = types.SimpleNamespace(OakCharacter=character, PlayerCameraManager=camera,
                                        PlayerState=types.SimpleNamespace(ExperienceState=tracks))
    state["sockets"] = {"FX_L_Hand_Weave": (10.0, -20.0, 40.0), "FX_L_Hand_Grapple": (2.0, -22.0, 38.0)}
    arms = types.SimpleNamespace(
        Name="FirstPersonArms", Outer=character, DoesSocketExist=lambda name: name in state["sockets"],
        GetSocketLocation=lambda name: types.SimpleNamespace(**dict(zip("XYZ", state["sockets"][name]))))
    instance = ArmsAnimation(state, arms)
    arms.GetAnimInstance = lambda: instance
    state["anim_instances"] = [instance]
    state["arms_animation"] = instance
    return state["pc"], character


def world(state, *things):
    """A world of balls for the scenes that hold several things: each thing is (actor, radius), the ball standing
    where the actor does, so moving the actor moves it. A ray meets the nearest ball it enters, at its skin; an
    actor that left the world is met no more."""
    def line(start, end):
        span = [b - a for a, b in zip(start, end)]
        length = math.sqrt(sum(part * part for part in span))
        if length == 0.0:
            return False, None
        way = [part / length for part in span]
        nearest = None
        for actor, radius in things:
            if id(actor) in state["gone"]:
                continue
            to = [c - a for a, c in zip(start, actor.at)]
            along = sum(a * b for a, b in zip(to, way))
            beside = sum(part * part for part in to) - along * along
            if beside > radius * radius:
                continue
            entry = along - math.sqrt(radius * radius - beside)
            if 0.0 <= entry <= length and (nearest is None or entry < nearest[1]):
                nearest = (actor, entry)
        if nearest is None:
            return False, None
        return met(nearest[0], nearest[1], at=tuple(a + part * nearest[1] for a, part in zip(start, way)))

    state["line"] = line


def aim_at(state, name=None, distance=500.0):
    """What the camera's ray meets: nothing when the name is None, else an actor of that name, standing where the
    ray meets it; returns the actor. These scenes hold one thing at a time: the actor met before leaves the world."""
    previous = state.pop("aimed_at", None)
    if previous is not None:
        state["gone"].add(id(previous))
    if name is None:
        state["trace"] = (False, None)
        return None
    actor = state["aimed_at"] = Actor(name, (distance, 0.0, 50.0))
    state["trace"] = met(actor, distance)
    return actor
