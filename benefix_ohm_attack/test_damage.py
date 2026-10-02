"""Tests one hit: the signature read from the game, every parameter filled, and a refusal instead of a guess."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import damage  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def refused(action) -> str:
    try:
        action()
    except damage.Refused as error:
        return str(error)
    return ""


def function(props):
    return sdk_stubs.Named("CauseDamage", fields=props)


rows = damage.describe(function(sdk_stubs.cause_damage()))
by_name = {row["name"]: row for row in rows}
check("the twenty-two parameters are read", len(rows) == 22)
check("a handle inside a struct is found with its field's own type",
      by_name["ImpactForceOverride"]["handles"] == [(("attribute",), sdk_stubs.FORCE_TYPE)]
      and by_name["SourceLocationOverride"]["handles"] == [])
returned = sdk_stubs.Prop("ReturnValue", "BoolProperty", sdk_stubs.PARAM | sdk_stubs.RETURN)
local = sdk_stubs.Prop("Local", "IntProperty", flags=0)
check("a return value and a local are not arguments", damage.describe(function([returned, local])) == [])
check("a kind with no known empty value is refused when the signature is read",
      refused(lambda: damage.describe(function([sdk_stubs.Prop("Definition", "GbxDefPtrProperty")])))
      == "Definition: no empty value known for GbxDefPtrProperty")
many = [sdk_stubs.Prop(f"P{index}", "IntProperty") for index in range(damage.MAX_PARAMETERS + 1)]
check("a runaway parameter list is refused", refused(lambda: damage.describe(function(many))) != "")
wide = sdk_stubs.struct("Wide", "/Script/GbxGame.Wide",
                        [sdk_stubs.Prop(f"F{index}", "IntProperty") for index in range(damage.MAX_STRUCT_FIELDS + 1)])
check("a struct with a runaway field list is refused", refused(lambda: damage.describe(function([wide]))) != "")
level = sdk_stubs.struct("L4", "/Script/GbxGame.L4", [sdk_stubs.handle("Deep", 5)])
for depth in (3, 2, 1):
    level = sdk_stubs.struct(f"L{depth}", f"/Script/GbxGame.L{depth}", [level])
check("a struct nested too deep is refused", refused(lambda: damage.describe(function([level]))) != "")

filled = damage.arguments(rows, {"DamageOverride": 40.0}, {"DamageData": "some_data", "DamageTypeOverride": "Fire"})
check("every parameter is filled", set(filled) == set(by_name))
check("what is given is passed as is, a named handle takes its parameter's type",
      filled["DamageOverride"] == 40.0 and filled["DamageData"] == ("handle", sdk_stubs.DATA_TYPE, "some_data")
      and filled["DamageTypeOverride"] == ("handle", sdk_stubs.TYPE_TYPE, "Fire"))
check("a handle inside an empty struct points at nothing, with its field's own type",
      filled["ImpactForceOverride"].attribute == ("handle", sdk_stubs.FORCE_TYPE, "None")
      and filled["ImpactEffectOverride"].Handle == ("handle", sdk_stubs.EFFECT_TYPE, "None"))
check("the rest gets the empty value of its kind",
      filled["DamageCauser"] is None and filled["bAppendDamageSource"] is False
      and filled["SourceSocketOverride"] == "None" and filled["DamageRadiusOverride"] == 0.0)
check("a given name the game does not have is refused",
      refused(lambda: damage.arguments(rows, {"DamageAmount": 1.0}, {})) == "not in the signature: DamageAmount")
check("a handle name on something else than a handle is refused",
      "expected a game data handle" in refused(lambda: damage.arguments(rows, {}, {"DamageOverride": "Fire"})))

character, enemy, where = object(), object(), object()
check("a hit is made and said made", damage.hit(character, enemy, where, 30.0, "Fire") is True and len(state["hits"]) == 1)
sent = state["hits"][0]
check("on the target, from the player's body, for the amount, where the ray landed",
      sent["DamageTarget"] is enemy and sent["DamageCauser"] is character and sent["DamageInstigator"] is character
      and sent["DamageOverride"] == 30.0 and sent["TargetedHitInfo"] is where and len(sent) == 22)
check("through the game's own player damage data, as the element asked",
      sent["DamageData"] == ("handle", sdk_stubs.DATA_TYPE, "damage_player_shared_targeted")
      and sent["DamageTypeOverride"] == ("handle", sdk_stubs.TYPE_TYPE, "Fire"))

state["props"] = [sdk_stubs.Prop("Other", "IntProperty")]
damage.hit(character, enemy, where, 30.0, "Shock")
check("the signature is read once: a second hit does not read it again", len(state["hits"]) == 2 and len(state["hits"][1]) == 22)

state["hit_raises"] = RuntimeError("FGameDataHandle type mismatch")
check("a hit the game refuses is said once and returns False",
      damage.hit(character, enemy, where, 30.0, "Fire") is False and len(state["errors"]) == 1
      and "type mismatch" in state["errors"][0])
state["hit_raises"] = None
check("after a refusal no hit is tried again", damage.hit(character, enemy, where, 30.0, "Fire") is False
      and len(state["hits"]) == 3)
damage.forget()
state["props"] = sdk_stubs.cause_damage()
check("forgetting reads the signature anew and tries again", damage.hit(character, enemy, where, 30.0, "Fire") is True)

state["props"] = sdk_stubs.cause_damage(extra=[sdk_stubs.Prop("Definition", "GbxDefPtrProperty")])
damage.forget()
check("a signature this mod cannot fill deals no hit at all",
      damage.hit(character, enemy, where, 30.0, "Fire") is False and len(state["hits"]) == 4)

real_make = sys.modules["unrealsdk"].make_struct


def bare_only(name, **fields):
    if "/" in name:
        raise ValueError("no such struct")
    return real_make(name, **fields)


sys.modules["unrealsdk"].make_struct = bare_only
state["props"] = sdk_stubs.cause_damage()
damage.forget()
hits = len(state["hits"])
check("an SDK that only takes a struct by its bare name is given it: the hit is made",
      damage.hit(character, enemy, where, 30.0, "Fire") is True and len(state["hits"]) == hits + 1
      and state["hits"][-1]["ImpactForceOverride"].made_from == "ForceSelection")
sys.modules["unrealsdk"].make_struct = real_make

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
