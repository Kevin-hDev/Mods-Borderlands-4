"""Tests gbx_param.py on a real block of memory (param_fixture.py): the three kinds read; a field refused for its size,
its type, an address that moves (a copy made for Python) or lies outside its owner, a value not in place or of an
unknown kind; a write read back, with the bytes for its give back; replace writing only over the bytes expected, and
saying when the wanted ones are already there or the game put others."""

import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

import param_fixture as fx  # noqa: E402
from it_follows import gbx_param  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def whole_at(owner: object, field: str) -> int:
    return struct.unpack_from("<i", memory.value(getattr(owner, field)), 8)[0]


try:
    memory = fx.Memory()
    other_kind = fx.Kind("FloatProperty", {})
    style = fx.build(memory, "SpawnerStyleDef_Waves", {
        "NumTotalActors": fx.param(whole=4), "Chance": fx.param(single=0.15), "cooldown": fx.param(decimal=(8.0, 2.0)),
        "Small": fx.param(whole=1), "Other": fx.param(whole=1), "Pointed": fx.param(whole=3, pointer=0x1000),
        "Empty": fx.param(), "Odd": fx.param(whole=2, kind=7)},
        sizes={"Small": 48}, kinds={"Other": other_kind})
    check("a whole number, a decimal one, a range read",
          gbx_param.read(style, "NumTotalActors") == (2, 4) and gbx_param.read(style, "Chance") == (3, 0.15)
          and gbx_param.read(style, "cooldown") == (11, [8.0, 2.0]))
    check("refused: a field not of 56 bytes, not a GbxParam, unknown",
          gbx_param.read(style, "Small") == "size" and gbx_param.read(style, "Other") == "type"
          and gbx_param.read(style, "Missing").startswith("unreadable:"))
    check("a value not in place, empty, or of an unknown kind reads None",
          gbx_param.read(style, "Pointed") == (2, None) and gbx_param.read(style, "Empty") == (0, None)
          and gbx_param.read(style, "Odd") == (7, None))
    copied = fx.build(memory, "Copied", {"NumTotalActors": fx.param(whole=4)}, copies=True)
    check("refused: an address that moves from one ask to the next (a copy)",
          gbx_param.read(copied, "NumTotalActors") == "moving")
    outside = fx.build(memory, "Outside", {"NumTotalActors": fx.param(whole=4)})
    outside._values["NumTotalActors"] = (fx.PARAM_KIND, 4096)
    check("refused: a field lying outside its owner", gbx_param.read(outside, "NumTotalActors") == "outside_owner")

    done = gbx_param.change(style, "NumTotalActors", lambda kind, value: value * 2)
    check("a whole number written and read back, its bytes kept", done["before"] == 4 and done["after"] == 8
          and whole_at(style, "NumTotalActors") == 8 and done["old"] == struct.pack("<i", 4).hex()
          and done["new"] == struct.pack("<i", 8).hex())
    ranged = gbx_param.change(style, "cooldown", lambda kind, value: [value[0] / 20, value[1] / 20])
    check("a range written whole", ranged["after"] == [0.4, 0.1] and ranged["kind"] == gbx_param.RANGE)
    check("refused: a write on a value not in place, or a field refused",
          gbx_param.change(style, "Pointed", lambda kind, value: 9) == {"refused": "kind:2"}
          and gbx_param.change(style, "Small", lambda kind, value: 9) == {"refused": "size"}
          and whole_at(style, "Pointed") == 3)

    check("replace: the old bytes back over the new ones",
          gbx_param.replace(style, "NumTotalActors", done["new"], done["old"]) == "written"
          and whole_at(style, "NumTotalActors") == 4)
    check("replace: already there", gbx_param.replace(style, "NumTotalActors", done["new"], done["old"]) == "already")
    memory.put(style.NumTotalActors._get_address() + 8, struct.pack("<i", 6))
    check("replace: the game put others, left", gbx_param.replace(style, "NumTotalActors", done["old"], done["new"])
          == "different" and whole_at(style, "NumTotalActors") == 6)
    check("replace: bytes of the wrong size refused",
          gbx_param.replace(style, "NumTotalActors", ranged["old"], ranged["new"]).startswith("refused:kind")
          and gbx_param.replace(style, "Pointed", done["old"], done["new"]) == "refused:kind:2"
          and gbx_param.replace(style, "Other", done["old"], done["new"]) == "refused:type")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
