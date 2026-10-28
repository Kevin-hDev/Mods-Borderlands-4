"""Tests the heirloom's fit: each heirloom's hold as its definition sets it (the knife's, Wraith's, with its grip on
its own axis; the axe's off it), taken at a share of its size; applied as a scale that keeps the reversed Y, a rotator
of the hold's pitch, yaw and roll, and a location that brings the held point, mirrored with the model and turned by
the engine, back onto the anchor; a failure is said."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import definition_fixture  # noqa: E402
import heirloom_stubs  # noqa: E402
from heirloom_stubs import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()
turned: list[tuple] = []


def rotate(vector, rotator):
    turned.append((vector, rotator))
    return sdk_stubs.vector(1.0, 2.0, 3.0)


state["classes"]["KismetMathLibrary"] = types.SimpleNamespace(
    ClassDefaultObject=types.SimpleNamespace(GreaterGreater_VectorRotator=rotate))
from apex_heirloom import apex_fit as fit_module  # noqa: E402
from apex_heirloom.heirloom_catalog import HEIRLOOMS  # noqa: E402

knife = fit_module.Fit.of(HEIRLOOMS["jakobs_knife"]["hold"])
check("the knife's hold is the one Kevin kept: 62 %, the blade's turn, held at 6 cm on its axis",
      (knife.size, knife.roll, knife.pitch, knife.yaw, knife.grip) == (62.0, -41.1, -44.7, 73.8, (0.0, 0.0, 6.0)))
definition = definition_fixture.load()
if definition is None:
    definition_fixture.skip("the knife's hold is the one its heirloom.json sets")
else:
    kept = definition["hold"]
    check("the knife's hold is the one its heirloom.json sets",
          (knife.size, knife.roll, knife.pitch, knife.yaw, knife.grip[2])
          == (kept["size"], kept["roll"], kept["pitch"], kept["yaw"], kept["grip"]))
check("a hold is taken at a share of its size, the rest kept",
      fit_module.Fit.of(HEIRLOOMS["axe"]["hold"], 150.0).size == HEIRLOOMS["axe"]["hold"]["size"] * 1.5
      and fit_module.Fit.of(HEIRLOOMS["axe"]["hold"], 150.0).grip == tuple(HEIRLOOMS["axe"]["hold"]["grip"]))

applied: dict = {}
said: list[str] = []
component = types.SimpleNamespace(
    SetRelativeScale3D=lambda scale: applied.update(scale=scale),
    K2_SetRelativeRotation=lambda rotator, sweep, hit, teleport: applied.update(rotator=rotator, sweep=sweep),
    K2_SetRelativeLocation=lambda where, sweep, hit, teleport: applied.update(where=where))
fit = fit_module.Fit(size=80.0, pitch=5.0, yaw=73.8, roll=-12.5, grip=(0.0, 0.0, 8.0))
fit_module.apply(component, fit, said.append)
scale, rotator, where = applied["scale"], applied["rotator"], applied["where"]
check("the size is a scale that keeps the reversed Y", (scale.X, scale.Y, scale.Z) == (0.8, -0.8, 0.8))
check("the rotator is the hold's pitch, yaw and roll, without sweeping",
      (rotator.Roll, rotator.Pitch, rotator.Yaw) == (-12.5, 5.0, 73.8) and applied["sweep"] is False)
vector, by = turned[-1]
check("the engine turns the held point, scaled, by the same rotator",
      (vector.X, vector.Y, vector.Z) == (0.0, 0.0, 0.8 * 8.0) and by is rotator)
check("and the heirloom is moved back by that much, so the held point sits on the anchor",
      (where.X, where.Y, where.Z) == (-1.0, -2.0, -3.0))
check("the values in use are said",
      said == ["fit: size 80 %, turn pitch 5, yaw 73.8, roll -12.5 degrees, held at 0, 0, 8 cm"])
fit_module.apply(component, fit_module.Fit(size=100.0, pitch=0.0, yaw=0.0, roll=0.0, grip=(1.0, 2.0, 3.0)), said.append)
vector, _ = turned[-1]
check("a held point off the model's axis is mirrored with the model", (vector.X, vector.Y, vector.Z) == (1.0, -2.0, 3.0))

said.clear()
fit_module.apply(types.SimpleNamespace(), fit, said.append)
check("a failure is said", said[0].startswith("the fit could not be applied: AttributeError"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
