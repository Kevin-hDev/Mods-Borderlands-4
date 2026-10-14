"""Tests look_hook.py: the hook built hidden and dressed in our images; put with its base hole on the rope's end, its
point along its way, at the player's size; shown and hidden calling the game only when that changes; removed."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_assets, look_hook, look_load  # noqa: E402
import look_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, within=1e-9):
    return all(abs(x - y) <= within for x, y in zip(a, b))


PIECE = look_assets.PIECES["hook"]
check("the hook needs its mesh, the character material and its three images",
      [path for _, path in look_hook.wanted()]
      == [PIECE["mesh"], look_assets.MATERIAL, *(image["texture"] for image in PIECE["textures"])])
check("base hole to point: 11.2 cm at A, 1.4 and 1.8 times that at B and C",
      abs(look_hook.length("A") - 11.2) < 0.01 and abs(look_hook.length("B") - 11.2 * 1.4) < 0.02
      and abs(look_hook.length("C") - 11.2 * 1.8) < 0.02)
check("its point turned along its way: ahead, up, and to the side",
      near(look_hook.facing((1.0, 0.0, 0.0)), (0.0, 0.0)) and near(look_hook.facing((0.0, 0.0, 1.0)), (90.0, 0.0))
      and near(look_hook.facing((0.0, 1.0, 0.0)), (0.0, 90.0)))

record = look_fixture.install(state)
character = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
hook = look_hook.Hook(character, look_load.fetch(look_hook.wanted()))
made = hook.made
check("built hidden, of the hook's mesh, in a new instance of the character material with its images",
      look_fixture.mesh_of(made) == PIECE["mesh"] and made.called("SetVisibility") == [(False, False)]
      and record["materials"][0].parent.path == look_assets.MATERIAL
      and len(record["materials"][0].called("SetTextureParameterValueByInfo")) == 3)

hook.put((100.0, 0.0, 50.0), (0.0, 1.0, 0.0), "C")
hook.put((120.0, 0.0, 50.0), (0.0, 1.0, 0.0), "C")
where, turn = made.called("K2_SetWorldLocationAndRotation")[-1][:2]
size = made.called("SetWorldScale3D")[-1][0]
check("put: its base hole where asked, its point along its way, at size C",
      near((where.X, where.Y, where.Z), (120.0, 0.0, 50.0))
      and near((turn.Pitch, turn.Yaw, turn.Roll), (0.0, 90.0, 0.0))
      and near((size.X, size.Y, size.Z), (1.8, 1.8, 1.8)))
check("shown once, however often it is put", made.called("SetVisibility") == [(False, False), (True, False)])
hook.hide()
hook.hide()
check("hidden once", made.called("SetVisibility")[-1] == (False, False) and len(made.called("SetVisibility")) == 3)
hook.destroy()
check("removed from its character", made.called("K2_DestroyComponent") == [(character,)])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
