"""Tests look_gun.py: which pieces show in each view and moment; the four pieces built on Vex, her own holster, the
arms' pistol drawn as her arms are, each dressed and hung on its bone with no move; shown or hidden only when that
changes; destroyed. Amon wears his own holster, C4SH none, and nothing of one shows on him."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import look_assets, look_gun, look_load, look_pieces, look_view  # noqa: E402
import look_fixture  # noqa: E402
import vex_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


G = look_gun
check("through the eyes, only the arms' pistol, while the arm holds it",
      G.shown(look_view.FIRST, True, True, True) == {G.ARMS_PISTOL}
      and G.shown(look_view.FIRST, False, True, True) == set())
check("from behind, the pistol in her hand during a shot, in its holster otherwise, the holster always",
      G.shown(look_view.THIRD, False, True, True) == {G.BODY_PISTOL, G.HOLSTER}
      and G.shown(look_view.THIRD, True, False, True) == {G.HOLSTERED, G.HOLSTER})
check("without the holster: the pistol in her hand during a shot, nothing otherwise",
      G.shown(look_view.THIRD, False, True, False) == {G.BODY_PISTOL} and G.shown(look_view.THIRD, False, False, False)
      == set())

record = look_fixture.install(state)
character = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
arms, body = vex_fixture.dress(state, character)
ROLES = (G.ARMS_PISTOL, G.BODY_PISTOL, G.HOLSTERED, G.HOLSTER)
gun = G.Gun(character, arms.Outer, look_load.fetch(G.wanted("DarkSiren")), "DarkSiren")
pieces = gun.pieces
VEX_KEYS = ["pistol_arms", "pistol_body", "pistol_holstered_darksiren", "holster_darksiren"]
check("four pieces built, each its own mesh, her own holster",
      list(pieces) == list(ROLES) and list(G.keys("DarkSiren").values()) == VEX_KEYS
      and [look_fixture.mesh_of(pieces[role]) for role in ROLES]
      == [look_assets.PIECES[key]["mesh"] for key in VEX_KEYS])
check("the arms' pistol drawn as the arms are, the others as the game draws the character",
      all(getattr(pieces[G.ARMS_PISTOL], flag) == f"arms {flag}" for flag in look_pieces.DRAW_FLAGS)
      and "bGbxForeground" not in vars(pieces[G.BODY_PISTOL]))
check("each hung on its bone with no move: the arms' pistol on the arms, the others on her body",
      pieces[G.ARMS_PISTOL].called("K2_AttachToComponent") == [(arms.Outer, "L_Hand_Object", 0, 0, 0, False)]
      and pieces[G.BODY_PISTOL].called("K2_AttachToComponent") == [(body.Outer, "L_Hand_Object", 0, 0, 0, False)]
      and pieces[G.HOLSTER].called("K2_AttachToComponent") == [(body.Outer, "Hips", 0, 0, 0, False)]
      and pieces[G.HOLSTERED].called("K2_AttachToComponent") == [(body.Outer, "Hips", 0, 0, 0, False)])
check("each dressed in the character material with its images",
      len(record["materials"]) == 4 and all(made.parent.path == look_assets.MATERIAL for made in record["materials"]))
before = {key: len(made.called("SetVisibility")) for key, made in pieces.items()}
gun.show({G.HOLSTER, G.HOLSTERED})
gun.show({G.HOLSTER, G.HOLSTERED})
gun.show({G.HOLSTER, G.BODY_PISTOL})
check("shown or hidden only when that changes",
      [len(pieces[role].called("SetVisibility")) - before[role] for role in ROLES] == [0, 1, 2, 1]
      and pieces[G.BODY_PISTOL].called("SetVisibility")[-1] == (True, False)
      and pieces[G.HOLSTERED].called("SetVisibility")[-1] == (False, False))
gun.destroy()
check("destroyed, all four", all(made.called("K2_DestroyComponent") for made in pieces.values()))

check("Amon wears his own holster and the pistol in it, the held pistols as Vex's",
      G.keys("Paladin") == {G.ARMS_PISTOL: "pistol_arms", G.BODY_PISTOL: "pistol_body",
                            G.HOLSTERED: "pistol_holstered_paladin", G.HOLSTER: "holster_paladin"})
robot = look_fixture.dress(sdk_stubs.FakeCharacter(), record)
robot_arms, _ = vex_fixture.dress(state, robot, definition="Char_RoboDealer")
c4sh = G.Gun(robot, robot_arms.Outer, look_load.fetch(G.wanted("RoboDealer")), "RoboDealer")
c4sh.show({G.HOLSTER, G.HOLSTERED})
check("C4SH: the held pistols only, nothing asked of a holster, nothing of one shown",
      list(c4sh.pieces) == [G.ARMS_PISTOL, G.BODY_PISTOL]
      and [path for _, path in G.wanted("RoboDealer") if "Holster" in path] == [] and c4sh.seen == set()
      and all(made.called("SetVisibility") == [(False, False)] for made in c4sh.pieces.values()))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
