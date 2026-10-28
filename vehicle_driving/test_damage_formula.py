"""Tests the guns' damage formula: how it is asked of the game, the Scalar it gives, the game's own value kept for the
whole game, and each refusal, said once and never asked again."""

import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = sdk_stubs.install()
library = state["formula"]

from vehicle_driving import damage_formula, report  # noqa: E402


def fresh() -> None:
    """A new game: the module forgets what it learnt, the library its calls."""
    importlib.reload(damage_formula)
    report.reset()
    library.calls.clear()
    state["errors"].clear()


driver = sdk_stubs.Driver()
fresh()
check("without a driver nothing is asked of the game", damage_formula.find(None) is None and library.calls == [])

scalar = damage_formula.find(driver)
check("it asks the game for calc_vehicle_weapon_damage by a PostAdd modifier of 0 on the driver, typed with the "
      "parameter's own definition type, and removes the modifier at once",
      library.calls == [("add", "calc_vehicle_weapon_damage", "GbxAttributeDef", driver, "PostAdd", 0.0),
                        ("remove", 1)] and library.modifiers == {})
check("the Scalar it gives reads the definition's", scalar is not None and scalar.constant == 1.0)
scalar.constant = 3.0
check("and writes where the game reads it", library.definition.Value.Scalar.constant == 3.0)
check("the game's own value is the first one read in the game", damage_formula.game_value() == 1.0)
again = damage_formula.find(driver)
check("a value left raised is never taken for the game's own",
      again is not None and again.constant == 3.0 and damage_formula.game_value() == 1.0)
library.definition.Value.Scalar.constant = 1.0

fresh()
library.typed = False
check("an attribute parameter without its definition type is never called: such a pointer crashed the game",
      damage_formula.find(driver) is None and library.calls == [] and len(state["errors"]) == 1
      and "no definition type" in state["errors"][0])
library.typed = True
check("refused once, it is not asked again in the same game, and said once",
      damage_formula.find(driver) is None and library.calls == [] and len(state["errors"]) == 1)

fresh()
library.resolves = False
check("an answer without the definition resolved gives nothing, the modifier removed, said once",
      damage_formula.find(driver) is None and library.modifiers == {} and len(state["errors"]) == 1
      and "left to the game" in state["errors"][0])
calls = len(library.calls)
check("and the game is not asked again", damage_formula.find(driver) is None and len(library.calls) == calls)
library.resolves = True

fresh()
real_add = library.AddModifierToGbxAttribute
library.AddModifierToGbxAttribute = lambda *args: (_ for _ in ()).throw(RuntimeError("refused"))
check("an error of the game gives nothing, said once with its text",
      damage_formula.find(driver) is None and "RuntimeError('refused')" in state["errors"][0])
library.AddModifierToGbxAttribute = real_add
check("and the game is not asked again", damage_formula.find(driver) is None and library.calls == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
