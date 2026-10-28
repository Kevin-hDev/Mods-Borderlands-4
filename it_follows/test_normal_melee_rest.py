"""Tests the armed bandits' rest after a blow (normal/melee_rest.py) on a fake memory: without a level's rest nothing is
opened; a tree holding the game's rest gets the level's, announced before, only its two numbers written, read back; a
tree not loaded is passed over without a word; a tree already at the level's is kept; one whose nodes are not found
or whose rest is another is left, said once; a rest already as short as the level's never lengthened; a write refused
said; a tree whose rest the game wrote again gets the level's at the next pass; the field's size not the expected,
nothing opened, said once; a refusal counted once, not at every pass; a write read back other said and not tried
again; a name the SDK cannot make said once. At the end the game's rest given back where the level's lies, a tree
changed since left, one unloaded said gone; a tree found at the level's given back too; nothing written, "none". The
seven trees' blow timers and rests as trial 66 read them."""

import pathlib
import struct
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import brain_fixture as fx  # noqa: E402
from it_follows import gbx_param  # noqa: E402
from it_follows.normal import melee_rest, melee_trees  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


memory = fx.Memory()
melee_rest.process_memory.ProcessMemory = lambda: memory
melee_rest.brain_trees.tokens = lambda mem, names: {name: fx.token(name) for name in names}
loaded: dict[str, object] = {}


def find_object(cls: str, path: str) -> object:
    if cls == "ScriptStruct":
        return types.SimpleNamespace(_find_prop=lambda name: types.SimpleNamespace(ElementSize=size[0],
                                                                                   Offset_Internal=448))
    if path not in loaded:
        raise ValueError(path)
    return loaded[path]


size = [56]
sys.modules["unrealsdk"].find_object = find_object
sys.modules["unrealsdk"].unreal.WeakPointer = lambda target: (lambda: target if target in loaded.values() else None)
SMG, PISTOL, HEAVY = (melee_trees.TREES[name] for name in ("AITree_GunToterSMG", "AITree_GunToterPistol",
                                                         "AITree_GunToterHeavy"))


def rest_of(tree: object, fake: object) -> object:
    return gbx_param.decode(memory.read(fake.nodes[tree.timer] + 448, 56))[1]


def lay(tree: object, value: bytes) -> object:
    fake = fx.tree(memory, tree.nodes, tree.timer, value)
    loaded[tree.path] = fake
    return fake


try:
    notes: list[tuple[str, dict]] = []
    calls: list[tuple[str, dict]] = []
    bandit = melee_rest.MeleeRest(None, lambda event, **f: notes.append((event, f)),
                                  lambda call, **f: calls.append((call, f)))
    check("without a level's rest nothing is opened", bandit.keep() == {} and bandit.at is None
          and bandit.put_back() == "none")

    check("the seven trees' blow timers and rests as trial 66 read them",
          {name: (tree.timer, tree.rest) for name, tree in melee_trees.TREES.items()}
          == {"AITree_GunToterSMG": (7, (6.0, 2.0)), "AITree_GunToterAssault": (6, (6.0, 2.0)),
              "AITree_GunToterBadass": (6, (6.0, 2.0)), "AITree_GunToterHeavy": (6, (6.0, 2.0)),
              "AITree_GunToterShotgun": (4, (6.0, 2.0)), "AITree_GunToterSmall": (3, (6.0, 2.0)),
              "AITree_GunToterPistol": (6, (8.0, 2.0))})
    predator = melee_rest.MeleeRest((2.5, 0.5), lambda event, **f: notes.append((event, f)),
                                    lambda call, **f: calls.append((call, f, len(memory.writes))))
    smg = lay(SMG, fx.rest(6.0, 2.0))
    pistol = lay(PISTOL, fx.rest(8.0, 2.0))
    tally = predator.keep()
    check("the game's rest gets the level's, read back; the trees not loaded passed over without a word",
          tally == {"written": 2} and rest_of(SMG, smg) == [2.5, 0.5] and rest_of(PISTOL, pistol) == [2.5, 0.5]
          and notes == [])
    check("announced before, with the game's and the level's",
          calls[0] == ("MeleeRest", {"tree": "AITree_GunToterSMG", "game": [6.0, 2.0], "wanted": [2.5, 0.5]}, 0)
          and calls[1][2] == 1)
    check("only the two numbers written", all(len(data) == 8 for _, data in memory.writes)
          and memory.writes[0][0] == smg.nodes[SMG.timer] + 448 + 8)
    check("a tree already at the level's is kept, nothing more written", predator.keep() == {}
          and len(memory.writes) == 2)
    memory.put(smg.nodes[SMG.timer] + 448, fx.rest(6.0, 2.0))
    check("a rest the game wrote again gets the level's at the next pass", predator.keep() == {"written": 1}
          and rest_of(SMG, smg) == [2.5, 0.5])

    heavy = lay(HEAVY, fx.rest(7.0, 1.0))
    check("a tree whose rest is another is left, said and counted once", predator.keep() == {"unexpected": 1}
          and predator.keep() == {} and rest_of(HEAVY, heavy) == [7.0, 1.0]
          and [f["what"] for e, f in notes if e == "normal_melee_rest_left"] == ["value:AITree_GunToterHeavy"])
    memory.put(heavy.nodes[0] + 0x10, struct.pack("<Q", fx.token("Other")))
    predator.keep()
    check("a tree whose nodes are not found is left, said once with why",
          notes[-1] == ("normal_melee_rest_left", {"what": "nodes:AITree_GunToterHeavy", "reason": "node:0"}))
    del loaded[HEAVY.path]

    senior = melee_rest.MeleeRest((9.0, 1.0), lambda event, **f: None, lambda call, **f: None)
    other = lay(PISTOL, fx.rest(8.0, 2.0))
    loaded.pop(SMG.path)
    check("a rest already as short as the level's never lengthened", senior.keep() == {}
          and rest_of(PISTOL, other) == [8.0, 2.0])
    loaded[PISTOL.path] = pistol
    loaded[SMG.path] = smg

    memory.put(pistol.nodes[PISTOL.timer] + 448, fx.rest(3.0, 1.0))
    given = predator.put_back()
    check("the end: the game's rest where the level's lies, a tree changed since left",
          given == {"given_back": 1, "different": 1} and rest_of(SMG, smg) == [6.0, 2.0]
          and rest_of(PISTOL, pistol) == [3.0, 1.0] and predator.held == {})

    gone = melee_rest.MeleeRest((2.5, 0.5), lambda event, **f: None, lambda call, **f: None)
    gone.keep()
    loaded.pop(SMG.path)
    check("a tree unloaded since said gone", gone.put_back() == {"gone": 1})

    refused = melee_rest.MeleeRest((2.5, 0.5), lambda event, **f: notes.append((event, f)), lambda call, **f: None)
    lay(SMG, fx.rest(6.0, 2.0))
    loaded.pop(PISTOL.path)
    memory.refuse_writes = True
    written_before = len(memory.writes)
    check("a write refused said", refused.keep() == {"write_failed": 1})
    memory.refuse_writes = False
    check("and not tried again in this game", refused.keep() == {} and len(memory.writes) == written_before)

    loaded.pop(SMG.path)
    other_back = melee_rest.MeleeRest((2.5, 0.5), lambda event, **f: None, lambda call, **f: None)
    lay(SMG, fx.rest(6.0, 2.0))
    plain_write = memory.write
    memory.write = lambda address, data: plain_write(address, struct.pack("<ff", 1.0, 1.0))
    check("a write read back other is said", other_back.keep() == {"write_failed": 1})
    memory.write = plain_write

    loaded.pop(SMG.path)
    leftover = melee_rest.MeleeRest((2.5, 0.5), lambda event, **f: None, lambda call, **f: None)
    missed = lay(SMG, fx.rest(2.5, 0.5))
    check("a tree found at the level's is held, and given back at the end", leftover.keep() == {}
          and leftover.put_back() == {"given_back": 1} and rest_of(SMG, missed) == [6.0, 2.0])

    unmade = melee_rest.MeleeRest((2.5, 0.5), lambda event, **f: notes.append((event, f)), lambda call, **f: None)
    made = melee_rest.brain_trees.tokens
    melee_rest.brain_trees.tokens = lambda mem, names: {name: fx.token(name) for name in names if name != "Ticket"}
    notes.clear()
    unmade.keep()
    unmade.keep()
    check("a name the SDK cannot make said once, with its name",
          [f for e, f in notes if f.get("what") == "tokens"] == [{"what": "tokens", "missing": ["Ticket"]}])
    melee_rest.brain_trees.tokens = made

    size[0] = 48
    notes.clear()
    wrong = melee_rest.MeleeRest((2.5, 0.5), lambda event, **f: notes.append((event, f)), lambda call, **f: None)
    check("the field's size not the expected: nothing opened, said once", wrong.keep() == {} and wrong.keep() == {}
          and notes == [("normal_melee_rest_left", {"what": "layout", "size": 48})])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
