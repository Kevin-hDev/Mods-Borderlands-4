"""The skins owned: the game's own always; the prison's and the premium one when the game's facts say so, read on the
controller as in game on 2026-10-07; outside a game the game's own alone; a fact unreadable or answered otherwise not
offered and said once; a fact reader with other parameters refused for the session, before any read."""

import sys
import types

import sdk_stubs

state = sdk_stubs.install()

from hunter_change import hunters, skins  # noqa: E402

fails: list[str] = []
sdk = sys.modules["unrealsdk"]


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def prop(name, kind, offset, size, out):
    return types.SimpleNamespace(Name=name, Class=types.SimpleNamespace(Name=kind), Offset_Internal=offset,
                                 ElementSize=size, PropertyFlags=0x100 if out else 0x80)


SIGNATURE = [prop(*parameter) for parameter in skins.PARAMETERS]
facts: dict = {}
read: list[tuple] = []


def read_fact(context, fact, *outputs):
    read.append((context, fact, outputs))
    answer = facts.get(fact, False)
    if isinstance(answer, Exception):
        raise answer
    if isinstance(answer, tuple):
        return answer
    return (Ellipsis, "TRUE" if answer else "None", int(answer), answer)


def game(signature=SIGNATURE, **owned):
    skins._reader = None
    facts.clear()
    facts.update(owned)
    read.clear()
    functions = {skins.FUNCTION: types.SimpleNamespace(_properties=lambda: iter(signature))}
    sdk.find_object = lambda kind, path: functions[path]
    sdk.find_class = lambda name: types.SimpleNamespace(
        ClassDefaultObject=types.SimpleNamespace(ReadFact=read_fact)) if name == skins.LIBRARY else None
    state["pc"] = types.SimpleNamespace(PlayerState=object())


PROLOGUE, PREMIUM = "transient.prologue_completed", "entitlement.premium.enabled"

game(**{PROLOGUE: True, PREMIUM: True})
check("the three skins of a player who finished the prologue and owns the pack, in the window's order",
      skins.owned() == ("default", "prison", "premium"))
check("both facts read on the controller, with ReadFact's empty outputs",
      read == [(state["pc"], PROLOGUE, ("None", 0, False)), (state["pc"], PREMIUM, ("None", 0, False))])

game(**{PROLOGUE: True})
check("without the pack, no premium skin", skins.owned() == ("default", "prison"))
game(**{PREMIUM: True})
check("still in the prologue, no prison skin", skins.owned() == ("default", "premium"))
game()
check("neither, the game's own alone", skins.owned() == (hunters.DEFAULT,))

game(**{PROLOGUE: True, PREMIUM: True})
state["pc"] = None
check("outside a game the game's own alone, nothing read", skins.owned() == (hunters.DEFAULT,) and not read)

game(**{PROLOGUE: (Ellipsis, "TRUE", 1, 1), PREMIUM: (True,)})
check("an answer that is not ReadFact's true bool read as not owned", skins.owned() == (hunters.DEFAULT,))

game(**{PROLOGUE: RuntimeError("no"), PREMIUM: True})
errors = len(state["errors"])
check("a fact unreadable not offered, the other still read", skins.owned() == ("default", "premium")
      and len(state["errors"]) == errors + 1 and "prison" in state["errors"][-1])
skins.owned()
check("and said once", len(state["errors"]) == errors + 1)

game(signature=SIGNATURE[:4], **{PROLOGUE: True, PREMIUM: True})
check("a reader with other parameters never called, the game's own alone",
      skins.owned() == (hunters.DEFAULT,) and not read and "reader" in state["errors"][-1])
skins.owned()
check("refused for the session, not checked again", not read)

kinds = list(SIGNATURE)
kinds[2] = prop("AsName", "StrProperty", 24, 8, True)
game(signature=kinds, **{PROLOGUE: True})
check("a parameter of another kind refused too", skins.owned() == (hunters.DEFAULT,) and not read)

game(**{PROLOGUE: True})
del sdk.find_object
check("a game without the reader offers the game's own alone", skins.owned() == (hunters.DEFAULT,) and not read)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
