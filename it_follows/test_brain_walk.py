"""Tests the brain's walk and its abort: the walk's parameter block is built with every parameter, the out one too, and
the latent settings the game took (no function called back, a fresh number, the controller called back); it is kept
for the game session, in a module that outlives a reload, then handed to the SDK's process_event with the library's
and the function's addresses; the block's Exec tells what the game wrote, and that the walk has ended once it holds an
int other than Start (unreadable counts as running). A block whose walk has ended is taken over by the next walk,
every field written anew before the call, Exec last; a block whose walk may still run, or whose Exec cannot be read,
never is; a walk whose block was taken over still reads ended, with what the game wrote for it; a new block is made
only when none has ended, and past KEPT_MAX of those no walk is given and nothing is freed. A walk read ended by its
own chaser offers its block, taken first once read again; else the search goes on from where it stopped. process_event
comes from the unrealsdk.dll already loaded, or OSError, found once; a failing call raises, its block kept; the gauge
counts the walks, the Execs read and the calls' time; the abort is immediate."""

import ctypes
import importlib
import pathlib
import secrets
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import chaser_fixture  # noqa: E402

game = chaser_fixture.Game(state)

from it_follows import brain_walk  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def raised(act: object, error: type) -> bool:
    try:
        act()
    except error:
        return True
    return False


def holder() -> types.ModuleType:
    return sys.modules[brain_walk.KEPT_MODULE]


class FakeFunction:
    def __init__(self, body: object) -> None:
        self.body, self.argtypes, self.restype = body, None, None

    def __call__(self, *args: object) -> object:
        return self.body(*args)


class Kernel:
    def __init__(self, handle: int) -> None:
        self.GetModuleHandleW = FakeFunction(lambda name: handle if name == "unrealsdk.dll" else 0)


loaded: dict = {}


def fake_ctypes(handle: int) -> types.SimpleNamespace:
    def cdll(name: str, handle: int | None = None) -> object:
        loaded.update(name=name, handle=handle)
        return types.SimpleNamespace(_unrealsdk_export__process_event=FakeFunction(lambda *args: None))
    return types.SimpleNamespace(WinDLL=lambda name, use_last_error=False: Kernel(handle), CDLL=cdll,
                                 c_wchar_p="wchar", c_void_p="void")


real_process_event = brain_walk.process_event
brain_walk.process_event = lambda: game.process_event

try:
    enemy, hunter, pc = object(), object(), object()

    first = brain_walk.walk(enemy, hunter, pc)
    block = first.block
    check("the block carries every parameter, its Exec output passed as Start, for the walk function",
          block.function is game.function and block.AIActor is enemy and block.GoalActor is hunter
          and game.walks[0]["Exec"] == brain_walk.START == 0)
    latent = block.LatentInfo
    check("the latent settings the game took: no function called back, a fresh number, the controller called back",
          latent.struct_name == "LatentActionInfo" and latent.Linkage == -1 and 1 <= latent.UUID < 2**31
          and latent.CallbackTarget is pc)
    check("process_event gets the library's, the function's and the block's addresses",
          [(call["object"], call["function"], call["block"]) for call in game.walks]
          == [(chaser_fixture.LIBRARY_ADDRESS, chaser_fixture.FUNCTION_ADDRESS, block)])
    check("the block is kept, in a module of its own that outlives a reload of this one",
          brain_walk.kept() == [block] and holder().blocks == [block]
          and brain_walk.KEPT_MODULE == "it_follows_brain_walk_kept")
    check("the walk is given back with its block", isinstance(first, brain_walk.Walk) and first.block is block)
    check("Start in its Exec, the walk still runs", not brain_walk.ended(first) and brain_walk.outcome(first) == "0")
    block.Exec = 2
    check("the walk tells what the game wrote", brain_walk.outcome(first) == "2")
    check("another value than Start: the walk has ended", brain_walk.ended(first))
    block.Exec = 1
    check("Succeeded is an end too", brain_walk.ended(first) and brain_walk.outcome(first) == "1")
    check("an unreadable walk says so", brain_walk.outcome(object()) == "unreadable:AttributeError")
    check("an unreadable Exec counts as still running", not brain_walk.ended(object())
          and not brain_walk.ended(types.SimpleNamespace(Exec="EGbxBrainExec.Start")))
    check("a long Exec is cut to MAX_TEXT", brain_walk.outcome(types.SimpleNamespace(Exec="x" * 100)) == "x" * 40)

    block.Exec = 2
    other_enemy, other_hunter, other_pc = object(), object(), object()
    uuids = iter((0, 2**31 - 2))
    bounds: list[int] = []

    def randbelow(bound: int) -> int:
        bounds.append(bound)
        return next(uuids)

    brain_walk.secrets = types.SimpleNamespace(randbelow=randbelow)
    second = brain_walk.walk(other_enemy, other_hunter, other_pc)
    call = game.walks[-1]
    check("a block whose walk has ended is taken over by the next walk, no new block made",
          second.block is block and brain_walk.kept() == [block] and call["block"] is block)
    check("every field is written anew before the call: actor, goal, Exec back to Start",
          call["AIActor"] is other_enemy and call["GoalActor"] is other_hunter and call["Exec"] == brain_walk.START)
    check("with fresh latent settings for the new controller",
          call["LatentInfo"] is not latent and call["LatentInfo"].CallbackTarget is other_pc
          and call["LatentInfo"].Linkage == -1 and call["LatentInfo"].UUID == 1)
    check("the walk taken over still reads ended, with what the game wrote for it",
          second is not first and brain_walk.ended(first) and brain_walk.outcome(first) == "2"
          and first.block is block)
    check("the new walk runs", not brain_walk.ended(second) and brain_walk.outcome(second) == "0")
    third = brain_walk.walk(enemy, hunter, pc)
    check("a fresh number is drawn below 2**31, never 0",
          bounds == [2**31 - 1, 2**31 - 1] and third.block.LatentInfo.UUID == 2**31 - 1)
    brain_walk.secrets = secrets
    check("a block whose walk may still run is never taken: a new block is made",
          third.block is not block and brain_walk.kept() == [block, third.block] and block.AIActor is other_enemy
          and not brain_walk.ended(second))

    block.Exec = 2
    second_block = third.block
    second_block.Exec = 2
    fourth = brain_walk.walk(enemy, hunter, pc)
    check("the first ended block is taken, the other left as it was",
          fourth.block is block and second_block.Exec == 2 and second_block.AIActor is enemy
          and brain_walk.ended(second) and brain_walk.ended(third) is True and len(brain_walk.kept()) == 2)

    block.Exec = "EGbxBrainExec.Failed"
    second_block.Exec = "EGbxBrainExec.Failed"
    fifth = brain_walk.walk(enemy, hunter, pc)
    check("a block whose Exec cannot be read as an int is never taken",
          fifth.block not in (block, second_block) and block.Exec == second_block.Exec == "EGbxBrainExec.Failed"
          and len(brain_walk.kept()) == 3)

    class Unreadable:
        """A block whose Exec the SDK cannot read."""

        @property
        def Exec(self) -> int:
            raise RuntimeError("unreadable")

    del brain_walk.kept()[:]
    holder().latest.clear()
    brain_walk.kept().append(Unreadable())
    sixth = brain_walk.walk(enemy, hunter, pc)
    check("nor a block whose Exec raises when read", sixth.block is brain_walk.kept()[1]
          and len(brain_walk.kept()) == 2)

    sixth.block.Exec = 2
    game.refused.add("GoalActor")
    count = len(game.walks)
    check("a field the SDK refuses on a block taken over raises, nothing called",
          raised(lambda: brain_walk.walk(enemy, hunter, pc), TypeError) and len(game.walks) == count)
    check("the block still reads ended, its walk too, and is taken by the next walk",
          sixth.block.Exec == 2 and brain_walk.ended(sixth))
    game.refused.clear()
    seventh = brain_walk.walk(enemy, hunter, pc)
    check("then written in full", seventh.block is sixth.block and sixth.block.GoalActor is hunter
          and game.walks[-1]["Exec"] == brain_walk.START and len(brain_walk.kept()) == 2)

    seventh.block.Exec = 2
    game.walk_fails = OSError("refused")
    check("a failing call raises, its block still kept and given to that walk",
          raised(lambda: brain_walk.walk(enemy, hunter, pc), OSError) and len(brain_walk.kept()) == 2
          and seventh.block.Exec == brain_walk.START and brain_walk.ended(seventh))
    check("a block whose call failed reads as running: never taken again", not any(
        brain_walk.ended(walk) for walk in holder().latest.values()))
    game.walk_fails = None
    count = len(brain_walk.kept())
    eighth = brain_walk.walk(enemy, hunter, pc)
    check("a new block is made instead", len(brain_walk.kept()) == count + 1 and eighth.block is brain_walk.kept()[-1])
    game.walk_fails = OSError("refused")
    count = len(brain_walk.kept())
    check("a failing call on a new block raises, the block kept all the same",
          raised(lambda: brain_walk.walk(enemy, hunter, pc), OSError) and len(brain_walk.kept()) == count + 1
          and game.walks[-1]["block"] is brain_walk.kept()[-1])
    game.walk_fails = None

    del brain_walk.kept()[:]
    holder().latest.clear()
    running = [brain_walk.walk(enemy, hunter, pc) for _ in range(2)]
    brain_walk.kept().extend(game.make_block(game.function, Exec=brain_walk.START)
                             for _ in range(brain_walk.KEPT_MAX - 2))
    count = len(game.walks)
    check("past KEPT_MAX blocks, none ended, no walk is given and nothing is freed",
          raised(lambda: brain_walk.walk(enemy, hunter, pc), RuntimeError) and len(game.walks) == count
          and len(brain_walk.kept()) == brain_walk.KEPT_MAX)
    brain_walk.kept()[-1].Exec = 2
    at_cap = brain_walk.walk(enemy, hunter, pc)
    check("at KEPT_MAX a block whose walk has ended is still taken over",
          at_cap.block is brain_walk.kept()[-1] and len(brain_walk.kept()) == brain_walk.KEPT_MAX
          and len(game.walks) == count + 1)
    del brain_walk.kept()[brain_walk.KEPT_MAX - 1:]
    below = brain_walk.walk(enemy, hunter, pc)
    check("one below KEPT_MAX a new block is made", len(brain_walk.kept()) == brain_walk.KEPT_MAX
          and below.block is brain_walk.kept()[-1])

    reloaded = importlib.reload(brain_walk)
    check("a reloaded walk module keeps the same blocks and walks",
          reloaded.kept() is holder().blocks and len(reloaded.kept()) == brain_walk.KEPT_MAX
          and holder().latest[id(running[0].block)] is running[0])
    brain_walk.process_event = lambda: game.process_event
    running[0].block.Exec = 2
    after_reload = brain_walk.walk(enemy, hunter, pc)
    check("and takes over their ended blocks, the walk given before the reload reading ended",
          after_reload.block is running[0].block and brain_walk.ended(running[0])
          and brain_walk.outcome(running[0]) == "2")

    del brain_walk.kept()[:]
    holder().latest.clear()
    holder().free.clear()
    holder().cursor = 0
    blocks = [brain_walk.walk(enemy, hunter, pc) for _ in range(4)]
    for given in blocks:
        given.block.Exec = 2
    check("a walk read ended by its own chaser offers its block", brain_walk.ended(blocks[2])
          and list(holder().free.values()) == [blocks[2].block])
    brain_walk.gauge()
    offered = brain_walk.walk(enemy, hunter, pc)
    check("the next walk takes the block offered, before the ended blocks ahead of it, one Exec read",
          offered.block is blocks[2].block and brain_walk.gauge()["exec_reads"] == 1 and not holder().free)
    check("a walk whose block was taken over offers nothing", brain_walk.ended(blocks[2]) and not holder().free)
    blocks[3].block.Exec = 2
    brain_walk.ended(blocks[3])
    blocks[3].block.Exec = brain_walk.START
    check("an offered block running again is read, then left: the search goes on among the others",
          brain_walk.walk(enemy, hunter, pc).block is blocks[0].block and not holder().free
          and brain_walk.gauge()["exec_reads"] == 2)
    check("the search goes on from where it stopped: the next ended block, the first one not read again",
          brain_walk.walk(enemy, hunter, pc).block is blocks[1].block and brain_walk.gauge()["exec_reads"] == 1)
    check("none ended: every block read once, a new one made", brain_walk.walk(enemy, hunter, pc).block
          is brain_walk.kept()[-1] and len(brain_walk.kept()) == 5 and brain_walk.gauge()["exec_reads"] == 4)

    found: list[int] = []
    brain_walk.process_event = lambda: found.append(1) or game.process_event
    brain_walk._held["call"] = None
    count = len(game.walks)
    for _ in range(3):
        brain_walk.walk(enemy, hunter, pc)
    said = brain_walk.gauge()
    check("process_event is found once for every walk after it", found == [1] and len(game.walks) == count + 3)
    check("the gauge counts the walks and the time of their calls, then afresh",
          said["walks"] == 3 and said["walk_ms"] >= 0.0 and brain_walk.gauge() == {"walks": 0, "exec_reads": 0,
                                                                                     "walk_ms": 0.0})
    game.walk_fails = OSError("refused")
    raised(lambda: brain_walk.walk(enemy, hunter, pc), OSError)
    game.walk_fails = None
    check("a failing call is counted too", brain_walk.gauge()["walks"] == 1)
    brain_walk.process_event = lambda: game.process_event

    brain_walk.abort(enemy)
    check("the abort is immediate, on the enemy", game.log[-1] == ("abort", enemy, True))

    brain_walk.ctypes = fake_ctypes(0x7000)
    call = real_process_event()
    check("process_event is the export of the unrealsdk.dll already loaded, three addresses in, nothing out",
          loaded == {"name": "unrealsdk.dll", "handle": 0x7000} and call.argtypes == ["void", "void", "void"]
          and call.restype is None)
    brain_walk.ctypes = fake_ctypes(0)
    check("without unrealsdk.dll loaded, OSError", raised(real_process_event, OSError))
    brain_walk.ctypes = ctypes
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
