"""Tests look_rope.py: as many pieces as the range needs and a quarter more, built hidden and dressed in our images,
C with its glow beside it in the game's effect material; the light at the player's strength; each piece laid from one
place on the curve to the next, glow and rope alike, stretched rather than short when the curve is longer than the
pieces; hidden again; every piece removed even when one refuses."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_assets, look_hook, look_load, look_rope, rope_motion  # noqa: E402
import look_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a, b, within=1e-6):
    return all(abs(x - y) <= within for x, y in zip(a, b))


ROPE, PIECES = look_assets.ROPE, look_assets.PIECES
check("a piece is 45.6 cm drawn 1 cm across, 54.7 cm at L",
      abs(look_rope.piece_cm("A", "L") - 45.6 * 1.2) < 1e-3 and abs(look_rope.piece_cm("C", "K") - 45.6 * 0.7) < 1e-3)
check("30 m at L takes 69 pieces, 100 m at K 392: a quarter more than the range",
      look_rope.count("A", "L", 3000.0) == 69 and look_rope.count("C", "K", 10000.0) == 392)

record = look_fixture.install(state)
character = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
objects = look_load.fetch(look_rope.wanted("A", "ORANGE") + look_rope.wanted("C", "GREEN") + look_hook.wanted())

rope = look_rope.Rope(character, "A", "L", 5, objects, "ORANGE")
pieces = rope.strands[0][0]
first_material = record["materials"][0]
check("A: five pieces of A's mesh, one strand, all hidden and free to move",
      len(rope.strands) == 1 and len(pieces) == 5
      and all(look_fixture.mesh_of(made) == PIECES["rope_a"]["mesh"] for made in pieces)
      and all(made.called("SetVisibility") == [(False, False)] for made in pieces)
      and all(made.called("SetMobility") == [(look_rope.look_pieces.MOVABLE,)] for made in pieces))
check("each added with no move, no turn and full size, never a bare transform",
      all(made.transform.Scale3D.X == made.transform.Scale3D.Y == made.transform.Scale3D.Z == 1.0
          and made.transform.Rotation.W == 1.0 for made in pieces))
check("the first dressed in a new instance of the character material, our four images in their slots",
      len(record["materials"]) == 1 and first_material.parent.path == look_assets.MATERIAL
      and [args[1].path for args in first_material.called("SetTextureParameterValueByInfo")]
      == [image["texture"] for image in PIECES["rope_a"]["textures"]]
      and first_material.called("SetTextureParameterValueByInfo")[3][0].Index == 1)
check("the others wear that same instance", all(made.called("SetMaterial") == [(look_fixture.SLOT_INDEX,
                                                                                 first_material)]
                                                for made in pieces[1:]))
rope.light(12.0, "ORANGE", "F")
painted = look_assets.GLOW_PAINTED
colours = [(c.R, c.G, c.B) for _, c in first_material.called("SetVectorParameterValueByInfo")]
check("the light at the strength asked on each channel of its mask, the face's share for the glow alone",
      [args[1] for args in first_material.called("SetScalarParameterValueByInfo")] == [12.0] * 3)
check("orange lights the mask's red as painted, its other channels dark: the thread's orange as before",
      [args[0].Name for args in first_material.called("SetVectorParameterValueByInfo")]
      == [entry["name"] for entry in ROPE["vectors"]] and colours[1:] == [(0.0, 0.0, 0.0)] * 2
      and near([part * painted[0] for part in colours[0]], painted, 1e-9))
rope.light(12.0, "RED", "D")
red = first_material.called("SetVectorParameterValueByInfo")[-3][1]
check("another colour lights the painted red in that colour",
      near([part * painted[0] for part in (red.R, red.G, red.B)], look_assets.COLOURS["RED"], 1e-9))

shown = rope.lay([(0.0, 0.0, 0.0), (50.0, 0.0, 0.0), (100.0, 0.0, 0.0)])
pitch, yaw = pieces[0].called("K2_SetWorldLocationAndRotation")[-1][1].Pitch, \
    pieces[0].called("K2_SetWorldLocationAndRotation")[-1][1].Yaw
size = pieces[0].called("SetWorldScale3D")[-1][0]
check("a metre of rope at L is two pieces end to end, each turned along it and stretched to reach the next",
      shown == 2 and look_fixture.shown(pieces) == 2 and near(look_fixture.put_at(pieces[0]), (0.0, 0.0, 0.0))
      and near(look_fixture.put_at(pieces[1]), (50.0, 0.0, 0.0)) and abs(pitch + 90.0) < 1e-9 and abs(yaw) < 1e-9
      and near((size.X, size.Y, size.Z), (1.2, 1.2, 50.0 / 45.6), 1e-6))

hanging = rope_motion.shape((0.0, 0.0, 0.0), (240.0, 0.0, 0.0), "H", 1.0, 0.3)
expected = rope_motion.laid(hanging, look_rope.piece_cm("A", "L"))
rope.lay(hanging)
check("hanging, each piece starts where the formula puts it",
      look_fixture.shown(pieces) == len(expected)
      and all(near(look_fixture.put_at(made), start) for made, (start, _) in zip(pieces, expected)))

long = [(0.0, 0.0, 0.0), (1000.0, 0.0, 0.0)]
check("a curve longer than its pieces stretches them rather than stopping short",
      rope.lay(long) == 5 and near(look_fixture.put_at(pieces[4]), (800.0, 0.0, 0.0))
      and abs(pieces[4].called("SetWorldScale3D")[-1][0].Z - 200.0 / 45.6) < 1e-5)
rope.show(0)
check("hidden again, every piece", look_fixture.shown(pieces) == 0)

glowing = look_rope.Rope(character, "C", "L", 3, objects, "GREEN")
rope_c, glow = glowing.strands[0][0], glowing.strands[1][0]
check("C: its pieces, and as many of its glow in the game's effect material with its image",
      len(glowing.strands) == 2 and len(glow) == 3
      and all(look_fixture.mesh_of(made) == PIECES["rope_halo"]["mesh"] for made in glow)
      and record["materials"][-1].parent.path == ROPE["halo"]["material"]
      and [args[1].path for args in record["materials"][-1].called("SetTextureParameterValueByInfo")]
      == [image["texture"] for image in PIECES["rope_halo"]["textures"]] + [ROPE["halo"]["images"]["GREEN"]]
      and record["materials"][-1].called("SetTextureParameterValueByInfo")[-1][0].Name == "Diffuse")
glowing.light(5.0, "GREEN", "E")
check("the light is the rope's, not the glow's", glowing.material is record["materials"][-2]
      and not record["materials"][-1].called("SetScalarParameterValueByInfo"))
check("C's face lights at its share of the strength: light a quarter, off none",
      [args[1] for args in glowing.material.called("SetScalarParameterValueByInfo")] == [1.25] * 3
      and (glowing.light(5.0, "GREEN", "D") or True)
      and [args[1] for args in glowing.material.called("SetScalarParameterValueByInfo")][3:] == [0.0] * 3)
glowing.lay([(0.0, 0.0, 0.0), (100.0, 0.0, 0.0)])
check("the glow laid on the rope's own places, as wide as the rope there",
      all(near(look_fixture.put_at(a), look_fixture.put_at(b)) for a, b in zip(rope_c[:2], glow[:2]))
      and glow[0].called("SetWorldScale3D")[-1][0].X == rope_c[0].called("SetWorldScale3D")[-1][0].X)

refusing = pieces[2]
refusing.answers["K2_DestroyComponent"] = lambda owner: (_ for _ in ()).throw(RuntimeError("refused"))
try:
    rope.destroy()
    raised = None
except RuntimeError as error:
    raised = error
check("removing: every piece is asked, one refusing does not keep the others, and the refusal is raised after",
      all(made.called("K2_DestroyComponent") for made in pieces) and raised is not None and rope.strands == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
