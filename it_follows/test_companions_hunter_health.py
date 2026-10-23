"""Tests trial 172's hunter's health (hunter_health.py): his most health read by the game's attribute reader, with the
attribute's name, his character and the default, in that order; a reading of nothing, of the default, or not a number
said; no character, no reader, a refusing reader said."""

import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
fails: list[str] = []
asked: list[tuple] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("hunter_health_under_test", HERE / "it_follows" / "companions" / "hunter_health.py")
module = util.module_from_spec(spec)
spec.loader.exec_module(module)
answer = [10874.0]


def reader(name: str, actor: object, default: float) -> object:
    asked.append((name, actor, default))
    if isinstance(answer[0], Exception):
        raise answer[0]
    return answer[0]


state["classes"]["GbxAttributeBlueprintLibrary"] = types.SimpleNamespace(
    ClassDefaultObject=types.SimpleNamespace(GetValueOfAttribute=reader))
hunter = object()
pc = types.SimpleNamespace(OakCharacter=hunter)
check("his most health read", module.most(pc) == 10874.0)
check("the attribute, his character and the default, in that order",
      asked == [("health_resource_max_value", hunter, -1.0)])
for value, said in ((-1.0, "unread:-1.0"), (0.0, "unread:0.0"), (float("nan"), "unread:nan"),
                    (float("inf"), "unread:inf")):
    answer[0] = value
    check(f"a reading of {value}: said", module.most(pc) == said)
answer[0] = "x"
check("not a number: said", module.most(pc) == "unread:ValueError")
answer[0] = RuntimeError("refused")
check("a refusing reader: said", module.most(pc) == "unread:RuntimeError")
answer[0] = 10874.0
check("no character: said", module.most(None) == "unread:AttributeError")
del state["classes"]["GbxAttributeBlueprintLibrary"]
check("no reader: said", module.most(pc) == "unread:KeyError")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
