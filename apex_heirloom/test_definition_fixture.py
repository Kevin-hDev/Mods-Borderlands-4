"""Tests where the tests find the knife's definition: in the workshop, its own heirloom.json, so that no check comparing
the mod with it is skipped there (a path one folder short skipped seven, 2026-09-27); in the public copy, none."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import definition_fixture  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


# cosmetics/heirloom/mod/source, the workshop's layout (CLAUDE.md); the public copy puts these tests in apex_heirloom/.
if HERE.name == "source" and HERE.parent.name == "mod" and HERE.parents[1].name == "heirloom":
    check("in the workshop, the tests read the Jakobs knife's own heirloom.json",
          definition_fixture.PATH == HERE.parents[1] / "jakobs_knife" / "heirloom.json"
          and isinstance(definition_fixture.load(), dict))
else:
    check("in the public copy there is no definition, and its checks are skipped", definition_fixture.load() is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
