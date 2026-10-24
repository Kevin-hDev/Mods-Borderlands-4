"""Tests a Lemmy just born dressed as a hunter (companions/dress.py), in two steps, the game drawing a new model only
a while after the call, as at trial 190: start() hides him, then gives his own mesh the hunter's upper body, nothing
more; step() waits while his mesh does not draw it, then hangs each of the hunter's other parts on it, following it,
gives his mesh and each part their model's own materials, and shows him again: worn, with how long it waited. The
game never drawing it: given up after WAIT_S, shown, nothing hung. Nothing done, not hidden, when the hunter is
unknown, he wears a hunter already, his mesh is not his own, a call's parameters differ or a part cannot be loaded;
hiding refused: nothing more; a swap refused: shown again; a part that cannot be hung, a painting that fails: stopped
there, shown again; gone: said; the team stopping: shown again; showing refused: said. What the player wears (colours
and head) read once, before; his head in place of the base one when it is that hunter's and loads. A guest (decision
77): Lilith's parts hung as a hunter's; as the phoenix, her materials put over each slot's own, by that own material,
once every part has its own back, the mouth left; Moxxi's one model, nothing hung; a phoenix material that cannot be
loaded: nothing done."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from characters.companions import dress, hunters, wear  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def ns(**fields: object) -> types.SimpleNamespace:
    return types.SimpleNamespace(**fields)


def find_object(kind: str, path: str) -> object:
    try:
        return state["objects"][(kind, path)]
    except KeyError:
        raise ValueError(path) from None


sys.modules["unrealsdk"].find_object = find_object
events: list = []


def model(path: str, skeleton: str, slots: int = 2) -> types.SimpleNamespace:
    name = path.rsplit(".", 1)[-1]
    return ns(Name=name, _path_name=lambda: path, Skeleton=ns(Name=skeleton),
              Materials=[ns(MaterialInterface=f"MI_{name}_{index}") for index in range(slots)])


class Mesh:
    """A skeletal mesh component as the game holds it: its model in SkinnedAsset. late: a model given is drawn only
    once draw_now() is called, as from the hook; fail: the call it refuses."""

    def __init__(self, name: str, asset: object, late: bool = False) -> None:
        self.Name, self.SkinnedAsset, self.late, self.fail, self.pending = name, asset, late, "", None

    def _call(self, name: str, *args: object) -> None:
        if self.fail == name:
            raise RuntimeError("refused by the game")
        events.append((name, self.Name, *args))

    def SetSkeletalMeshAsset(self, asset: object) -> None:
        self._call("model", asset.Name)
        if self.late:
            self.pending = asset
        else:
            self.SkinnedAsset = asset

    def draw_now(self) -> None:
        if self.pending is not None:
            self.SkinnedAsset, self.pending = self.pending, None

    def SetMobility(self, mobility: int) -> None:
        pass

    def K2_AttachToComponent(self, parent: object, *rest: object) -> None:
        self._call("attach", parent.Name)

    def SetLeaderPoseComponent(self, leader: object, force: bool, tick: bool) -> None:
        self._call("leader", leader.Name)

    def SetMaterial(self, index: int, given: object) -> None:
        self._call("paint", index, given)


class Lemmy:
    """A Lemmy just born: his own mesh on the gunners' skeleton; failing: the part made at that count refuses its
    model; refuses: the hidden flags he refuses."""

    def __init__(self, late: bool = True) -> None:
        self.Name = "Lemmy_1"
        self.Mesh = Mesh("CharacterMesh", model("/Engine/Transient.Transient_Gestalt", dress.SKELETON, 3), late)
        self.parts, self.failing, self.hidden, self.refuses = [], None, False, set()

    def SetActorHiddenInGame(self, hidden: bool) -> None:
        if hidden in self.refuses:
            raise RuntimeError("no")
        events.append(("hidden", hidden))
        self.hidden = hidden

    def AddComponentByClass(self, kind: object, manual: bool, placed: object, deferred: bool) -> tuple:
        made = Mesh(f"SkeletalMeshComponent_{len(self.parts) + 1}", None)
        made.fail = "model" if self.failing == len(self.parts) + 1 else ""
        self.parts.append(made)
        events.append(("add", made.Name))
        return made, None

    def FinishAddComponent(self, made: object, manual: bool, placed: object) -> None:
        pass


def calls(params: dict | None = None) -> None:
    for path, names in {**wear.CALLS, **(params or {})}.items():
        state["objects"][("Function", path)] = ns(_properties=lambda names=names: [
            ns(Name=name, PropertyFlags=0) for name in names])


def parts(missing: str = "") -> None:
    for look in hunters.LOOKS:
        for path in (look.upper, *look.followers):
            state["objects"].pop(("SkeletalMesh", path), None)
            if not (missing and path.endswith(missing)):
                state["objects"][("SkeletalMesh", path)] = model(path, f"SK_{look.name}_Skeleton")


state["classes"].update({"SkeletalMeshComponent": "ComponentClass", "SkeletalMesh": ns(_path_name=lambda: "/S.M"),
                         "GestaltSkeletalMesh": ns(_path_name=lambda: "/S.G"),
                         "AssetRegistryHelpers": ns(ClassDefaultObject=ns(GetAsset=lambda data: None))})
calls()
parts()
RAFA, VEX = hunters.BY_NAME["Rafa"], hunters.BY_NAME["Vex"]
clock = ns(now=10.0)


def short(path: str) -> str:
    return path.rsplit(".", 1)[-1]


def dressing(lemmy: object, name: str = "Rafa") -> dress.Dressing:
    return dress.Dressing(lambda: lemmy, name, lambda: clock.now)


lemmy = Lemmy()
one = dressing(lemmy)
events.clear()
check("started: hidden first, then his mesh given the upper body, nothing more", one.start() == {
      "done": "swapped", "hunter": "Rafa"} and events == [("hidden", True), ("model", "CharacterMesh",
                                                                              short(RAFA.upper))]
      and lemmy.hidden and lemmy.parts == [])
clock.now = 10.5
check("the game not drawing it yet: waiting, still hidden, nothing hung", one.step() is None and lemmy.hidden
      and lemmy.parts == [] and len(events) == 2)
lemmy.Mesh.draw_now()
clock.now = 10.75
check("drawn: the rest put on, he is shown, said with how long it waited", one.step() == {
      "done": "worn", "hunter": "Rafa", "hung": 2, "slots": 6, "waited_s": 0.75} and not lemmy.hidden)
check("each other part hung on his mesh, following it, in order", [event for event in events[2:10]] == [
      ("add", "SkeletalMeshComponent_1"), ("model", "SkeletalMeshComponent_1", short(RAFA.followers[0])),
      ("attach", "SkeletalMeshComponent_1", "CharacterMesh"), ("leader", "SkeletalMeshComponent_1", "CharacterMesh"),
      ("add", "SkeletalMeshComponent_2"), ("model", "SkeletalMeshComponent_2", short(RAFA.followers[1])),
      ("attach", "SkeletalMeshComponent_2", "CharacterMesh"), ("leader", "SkeletalMeshComponent_2", "CharacterMesh")])
check("then every mesh drawing him given its model's own materials, and only then shown", events[10:] == [
      ("paint", "CharacterMesh", 0, f"MI_{short(RAFA.upper)}_0"),
      ("paint", "CharacterMesh", 1, f"MI_{short(RAFA.upper)}_1"),
      ("paint", "SkeletalMeshComponent_1", 0, f"MI_{short(RAFA.followers[0])}_0"),
      ("paint", "SkeletalMeshComponent_1", 1, f"MI_{short(RAFA.followers[0])}_1"),
      ("paint", "SkeletalMeshComponent_2", 0, f"MI_{short(RAFA.followers[1])}_0"),
      ("paint", "SkeletalMeshComponent_2", 1, f"MI_{short(RAFA.followers[1])}_1"), ("hidden", False)])
events.clear()
check("dressed already: nothing done, never hidden", dressing(lemmy, "Vex").start() == {"done": "dressed_already"}
      and events == [])

vex = Lemmy(late=False)
one = dressing(vex, "Vex")
one.start()
check("drawn at once, as from the console: the rest put on at the next step, Vex's jacket included",
      one.step()["hung"] == 3 and [part.SkinnedAsset.Name for part in vex.parts] == [
          short(path) for path in VEX.followers] and not vex.hidden)

never = Lemmy()
one = dressing(never)
clock.now = 20.0
one.start()
clock.now = 20.0 + dress.WAIT_S - 0.01
check("not drawn within WAIT_S: still waiting", one.step() is None and never.hidden)
clock.now = 20.0 + dress.WAIT_S
check("not drawn after WAIT_S: given up, shown, nothing hung", one.step() == {
      "done": "swap_not_taken", "waited_s": dress.WAIT_S} and not never.hidden and never.parts == [])

events.clear()
check("a hunter unknown: nothing done", dressing(Lemmy(), "Nobody").start() == {"done": "no_look"} and events == [])
other = Lemmy()
other.Mesh.Name = "Mesh"
check("a mesh not his own: nothing done", dressing(other).start() == {
      "done": "not_himself", "mesh": "Mesh", "skeleton": dress.SKELETON} and events == [])
other = Lemmy()
other.Mesh.SkinnedAsset = model("/Game/Other.Other", "SK_Other")
check("a mesh on another skeleton: nothing done", dressing(other).start()["done"] == "not_himself" and events == [])
other.Mesh.SkinnedAsset = None
check("a mesh drawing nothing: nothing done", dressing(other).start() == {
      "done": "not_himself", "mesh": "CharacterMesh", "skeleton": None} and events == [])
calls({"/Script/Engine.Actor:SetActorHiddenInGame": ("bHidden",)})
check("a call's parameters differ: nothing done, the call said", dressing(Lemmy()).start() == {
      "done": "calls_differ", "calls": ["SetActorHiddenInGame"]} and events == [])
calls()
parts(missing="SK_ExoSoldier_Base_Head")
check("a part that cannot be loaded: nothing done, the part said", dressing(Lemmy()).start() == {
      "done": "not_loaded", "parts": ["SK_ExoSoldier_Base_Head"]} and events == [])
parts()
check("gone: said, nothing done", dressing(None).start() == {"done": "gone"} and dressing(None).step() == {
      "done": "gone"} and events == [])
check("a step before any start, or after a start that did nothing: nothing done", dressing(Lemmy()).step() == {
      "done": "gone"} and events == [])

shy = Lemmy()
shy.refuses = {True}
outcome = dressing(shy).start()
check("hiding refused: said, nothing more", outcome["done"] == "hide_failed" and events == [])
refused = Lemmy()
refused.Mesh.fail = "model"
outcome = dressing(refused).start()
check("the swap refused: said, shown again", outcome["done"] == "swap_failed"
      and outcome["error"].startswith("RuntimeError:refused") and not refused.hidden and refused.parts == [])
half = Lemmy(late=False)
half.failing = 2
one = dressing(half)
one.start()
events.clear()
outcome = one.step()
check("a part that cannot be hung: stopped there, nothing painted, shown again", outcome["done"] == "wear_failed"
      and len(half.parts) == 2 and not any(event[0] == "paint" for event in events) and not half.hidden)
unpainted = Lemmy(late=False)
unpainted.Mesh.SetMaterial = lambda index, given: 1 / 0
one = dressing(unpainted)
one.start()
outcome = one.step()
check("a painting that fails: stopped, said, shown again", outcome["done"] == "paint_failed"
      and outcome["error"].startswith("ZeroDivisionError") and len(unpainted.parts) == 2 and not unpainted.hidden)
stopped = Lemmy()
one = dressing(stopped)
one.start()
one.give_up()
check("the team stopping before he is dressed: shown again as he is", not stopped.hidden and stopped.parts == [])
stuck = Lemmy(late=False)
one = dressing(stuck)
one.start()
stuck.refuses = {False}
check("showing refused: said with the outcome", one.step()["shown"] == "failed:RuntimeError")

painted: list = []
real_paint = dress.player_paint.paint
dress.player_paint.paint = lambda drawn, made: painted.append((drawn, made)) or 5
PREMIUM = ("/Game/PlayerCharacters/Customizations/DarkSiren/HeadSwaps/DS_Head_16_Premium/Model/Rig/"
           "SK_DS_Head_16_Premium.SK_DS_Head_16_Premium")
state["objects"][("SkeletalMesh", PREMIUM)] = model(PREMIUM, "SK_DS_Head_16_Premium_Skeleton")
asked_own: list = []


def wearing(paints: dict, head: str | None, parts: tuple = ()):
    return lambda: asked_own.append(1) or dress.player_paint.Own(paints, head, parts)


coloured = Lemmy(late=False)
one = dress.Dressing(lambda: coloured, "Rafa", lambda: clock.now, wearing({"a": 1, "b": 2}, None))
one.start()
events.clear()
outcome = one.step()
drawn, made = painted[-1]
check("the player's colours: put last, over every mesh drawing him with its model, said", outcome["done"] == "worn"
      and outcome["player"] == 5 and outcome["player_paints"] == 2 and outcome["player_head"] is None
      and made == {"a": 1, "b": 2} and [(mesh.Name, short(part._path_name())) for mesh, part in drawn] == [
          ("CharacterMesh", short(RAFA.upper)), ("SkeletalMeshComponent_1", short(RAFA.followers[0])),
          ("SkeletalMeshComponent_2", short(RAFA.followers[1]))] and not coloured.hidden)
check("his own materials first, then the player's", any(event[0] == "paint" for event in events))
check("what the player wears read once, before he is dressed", asked_own == [1])
own = Lemmy(late=False)
one = dressing(own)
one.start()
painted.clear()
check("his own outfit: the player's colours never asked", "player" not in one.step() and painted == [])
broken_colours = Lemmy(late=False)
one = dress.Dressing(lambda: broken_colours, "Rafa", lambda: clock.now, lambda: 1 / 0)
one.start()
outcome = one.step()
check("what the player wears unread: dressed in his own, said, shown", outcome["done"] == "worn"
      and outcome["player"].startswith("ZeroDivisionError") and outcome["hung"] == 2 and painted == []
      and not broken_colours.hidden)

headed = Lemmy(late=False)
one = dress.Dressing(lambda: headed, "Vex", lambda: clock.now, wearing({}, PREMIUM))
one.start()
outcome = one.step()
check("the player's head: worn in place of the base one, the other parts kept, said", outcome["done"] == "worn"
      and outcome["player_head"] == "SK_DS_Head_16_Premium" and "player_parts" not in outcome
      and outcome["hung"] == 3
      and [part.SkinnedAsset.Name for part in headed.parts] == [short(VEX.followers[0]), short(VEX.followers[1]),
                                                                 "SK_DS_Head_16_Premium"])
check("its slots painted from its own model", any(event[1] == "SkeletalMeshComponent_3" and event[0] == "paint"
                                                  and event[3] == "MI_SK_DS_Head_16_Premium_0" for event in events))
elsewhere = Lemmy(late=False)
one = dress.Dressing(lambda: elsewhere, "Rafa", lambda: clock.now, wearing({}, PREMIUM, ("/A.A", PREMIUM)))
one.start()
outcome = one.step()
check("a head of another hunter: his base head kept, his parts said", outcome["player_head"] is None
      and outcome["player_parts"] == ["/A.A", PREMIUM]
      and elsewhere.parts[-1].SkinnedAsset.Name == short(RAFA.followers[-1]))
state["objects"].pop(("SkeletalMesh", PREMIUM))
unloaded = Lemmy(late=False)
one = dress.Dressing(lambda: unloaded, "Vex", lambda: clock.now, wearing({}, PREMIUM))
started = one.start()
outcome = one.step()
check("his head not loadable: dressed with the base head rather than not at all", started["done"] == "swapped"
      and outcome["done"] == "worn" and outcome["player_head"] is None
      and unloaded.parts[-1].SkinnedAsset.Name == short(VEX.followers[-1]))
dress.player_paint.paint = real_paint


def material(path: str) -> types.SimpleNamespace:
    return ns(Name=path.rsplit(".", 1)[-1], _path_name=lambda: path)


LILITH_MATERIALS = "/Game/AI/NPC/_Unique/Lilith/Model/Materials/"
MOUTH = "/Game/Common/MaterialTemplateLibrary/Character/MI_Template_Char_Mouth.MI_Template_Char_Mouth"
# Each part's slots as the game files list them (docs/renforts/releves/2026-10-24-lilith-et-moxxi/pieces/).
OWN = {"Body": ["MI_Lilith_Skin", "MI_Lilith_Lowerbody_Normal"], "Head": ["MI_Lilith_Head"],
       "Hair": ["MI_Lilith_Hair_Top", "MI_Lilith_Hair_Bottom"], "Outfit_01": ["MI_Lilith_Upperbody"],
       "Eyes": ["MI_Lilith_Eye"], "Teeth": ["MI_Lilith_Head", None], "Wings": ["MI_Lilith_Wings"]}


def guest_parts(missing: str = "") -> None:
    """The guests' models, their slots holding Lilith's own materials (the mouth's a template of the game's), and the
    phoenix's materials, all loadable but the one named missing."""
    for part, owns in OWN.items():
        path = f"/Game/AI/NPC/_Unique/Lilith/Model/Rig/SKPart_Lilith_{part}.SKPart_Lilith_{part}"
        slots = [material(MOUTH if own is None else f"{LILITH_MATERIALS}{own}.{own}") for own in owns]
        state["objects"][("SkeletalMesh", path)] = ns(Name=path.rsplit(".", 1)[-1], _path_name=lambda p=path: p,
                                                      Skeleton=ns(Name="SK_Lilith_Skeleton"),
                                                      Materials=[ns(MaterialInterface=slot) for slot in slots])
    moxxi = hunters.BY_NAME["Moxxi"].upper
    state["objects"][("SkeletalMesh", moxxi)] = model(moxxi, "SK_Moxxi_Skeleton", 12)
    for _own, put in hunters.BY_NAME["Lilith Phoenix"].paints:
        state["objects"].pop(("MaterialInstanceConstant", put), None)
        if not (missing and put.endswith(missing)):
            state["objects"][("MaterialInstanceConstant", put)] = material(put)


state["classes"]["MaterialInstanceConstant"] = ns(_path_name=lambda: "/S.MIC")
guest_parts()
PHOENIX = hunters.BY_NAME["Lilith Phoenix"]
phoenix = Lemmy(late=False)
one = dressing(phoenix, "Lilith Phoenix")
check("the phoenix: started as a hunter is, his mesh given Lilith's body", one.start() == {
      "done": "swapped", "hunter": "Lilith Phoenix"} and phoenix.Mesh.SkinnedAsset.Name == "SKPart_Lilith_Body")
events.clear()
outcome = one.step()
check("the phoenix worn: her six other parts hung, ten slots given their own, nine painted over, shown",
      outcome == {"done": "worn", "hunter": "Lilith Phoenix", "hung": 6, "slots": 10, "painted_over": 9,
                  "waited_s": 0.0} and not phoenix.hidden
      and [part.SkinnedAsset.Name for part in phoenix.parts] == [short(path) for path in PHOENIX.followers])
paints = [event for event in events if event[0] == "paint"]
over = paints[10:]
check("the phoenix's materials put after every part has its own back", len(paints) == 19
      and all("hoenix" not in event[3].Name for event in paints[:10]))
bare = Mesh("Bare", None)
events.clear()
check("a slot holding no material: never painted over", wear.overpaint(bare, ns(Materials=[
      ns(MaterialInterface=None), ns(MaterialInterface=material(f"{LILITH_MATERIALS}MI_Lilith_Eye.MI_Lilith_Eye"))]),
      {f"{LILITH_MATERIALS}MI_Lilith_Eye.MI_Lilith_Eye".lower(): "PUT"}, dress.MAX_SLOTS) == 1
      and events == [("paint", "Bare", 1, "PUT")])
check("each slot of Lilith's own given its phoenix one, by its own material; the mouth left as it is",
      [(event[1], event[2], event[3].Name) for event in over] == [
          ("CharacterMesh", 0, "MI_Lilith_Skin_Phoenix"), ("CharacterMesh", 1, "MI_Lilith_Lowerbody_Phoenix"),
          ("SkeletalMeshComponent_1", 0, "MI_Lilith_Head__Phoenix"),
          ("SkeletalMeshComponent_2", 0, "MI_Lilith_Hair_Top_Phoenix"),
          ("SkeletalMeshComponent_2", 1, "MI_Lilith_Hair_Bottom_Phoenix"),
          ("SkeletalMeshComponent_3", 0, "MI_Lilith_Upperbody_Phoenix"),
          ("SkeletalMeshComponent_4", 0, "MI_Lilith_Eye_PHoenix"),
          ("SkeletalMeshComponent_5", 0, "MI_Lilith_Head__Phoenix"),
          ("SkeletalMeshComponent_6", 0, "MI_Lilith_Wings_Phoenix_Full")])
lilith = Lemmy(late=False)
one = dressing(lilith, "Lilith")
one.start()
events.clear()
check("Lilith: her five other parts hung, her own materials only, nothing said painted over", one.step() == {
      "done": "worn", "hunter": "Lilith", "hung": 5, "slots": 9, "waited_s": 0.0}
      and not any(str(getattr(event[3], "Name", "")).endswith("hoenix") for event in events if event[0] == "paint"))
moxxi = Lemmy(late=False)
one = dressing(moxxi, "Moxxi")
one.start()
check("Moxxi: her one model drawn by his mesh, nothing hung, its twelve slots its own", one.step() == {
      "done": "worn", "hunter": "Moxxi", "hung": 0, "slots": 12, "waited_s": 0.0} and moxxi.parts == []
      and moxxi.Mesh.SkinnedAsset.Name == "SK_Moxxi")
check("a guest dressed already: nothing done", dressing(moxxi, "Lilith").start() == {"done": "dressed_already"})
guest_parts(missing="MI_Lilith_Wings_Phoenix_Full")
events.clear()
check("a phoenix material that cannot be loaded: nothing done, the material said", dressing(
      Lemmy(), "Lilith Phoenix").start() == {"done": "not_loaded", "parts": ["MI_Lilith_Wings_Phoenix_Full"]}
      and events == [])
guest_parts()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
