"""The brain's walk that brings a far enemy of the horde to the hunter, and its abort once the enemy has arrived.

AIScriptedMove and AbortScriptedBrainTask of GbxBrainFunctionLibrary, every parameter as read in game
(docs/RUN/enquetes/2026-10-10-ordre-de-marche.md). AIScriptedMove is latent: the game fills its Exec output later, when
the walk ends or is aborted. Called the usual way, the SDK frees the parameters as soon as the call returns, and that
later write lands in memory the game has reused: five or six walks at once crashed the game twice in three launches
(trials 6b and 6c, docs/RUN/enquetes/2026-10-10-relance.md). So the walk is called through the SDK's own
process_event, exported by unrealsdk.dll, with a parameter block this module builds and never frees for the rest of
the game session: the game's later write lands in it (verified in game since trial 6d,
docs/RUN/enquetes/2026-10-10-marche-reparee.md). The block also tells what the game wrote (outcome), so whether the
walk still runs (ended).

A block whose walk has ended is given to the next walk: trials 8d and 8e gave 100 to 150 walks a minute, so 4096
blocks kept for life would run out after 30 to 40 minutes of a run. Once the game has written a walk's Exec, its
latent action is over and no longer writes to the block (not verified in game: It Follows' trial 10 checks it). Were
it wrong, the late write would still land in a block this module keeps, never in freed memory: the later walk would
only read as ended too early. Each walk is given back as a Walk, so that a chaser still holding a walk whose block a
later walk has taken over reads its own walk as ended, and not the later walk's Start. Without it, such a chaser is
walked again only once the later walk ends, and only if no other chaser takes the block first: with many chasers kept
far, more than half of the walks given again were lost and some chasers went without one for most of the run
(simulated with the trials' walk lengths, not verified in game).

An ended block is looked for first among those a chaser read ended on its own walk, each read again before it is
taken, then among all the others in turn from where the last search stopped. Searched from the first block each time,
a walk read up to 71 Execs, most of them still running, and the heaviest second of trial 33 gave 54 walks (audit of
16 October 2026). Which ended block is taken changes nothing: every block is the same to the game.
"""

import ctypes
import secrets
import sys
import time
import types
from typing import Any, Callable

import unrealsdk

BRAIN = "GbxBrainFunctionLibrary"
SDK_LIBRARY = "unrealsdk.dll"
# unrealsdk's C export: void process_event(UObject* object, UFunction* function, void* params) (unrealsdk_main.cpp).
PROCESS_EVENT = "_unrealsdk_export__process_event"
# Blocks kept for the whole game session, never freed: a walk's block may be written as long as the walk lives. Past
# this many, all with a walk that may still run, no walk is given, rather than free one that may still be written. A
# block is about fifty bytes.
KEPT_MAX = 4096
KEPT_MODULE = "it_follows_brain_walk_kept"
MAX_TEXT = 40
# Exec right after the call, read in game: EGbxBrainExec.Start, 0 (trials 2 quater and 6d). Trial 6d saw the game
# write 2 there once the walk was aborted or ended by itself (docs/RUN/enquetes/2026-10-10-marche-reparee.md): Failed,
# by the game's own table of the enum (docs/RUN/enquetes/2026-10-10-recherche-poursuite.md, P2); 1 is Succeeded.
START = 0
_held: dict[str, Any] = {"call": None}
_counts: dict[str, float] = {"walks": 0, "exec_reads": 0, "walk_ms": 0.0}


class Walk:
    """One walk given to the game, and the kept block it was given in. Its Exec is the block's until a later walk
    takes the block over, then the value the game had written for it, which is never Start."""

    __slots__ = ("block", "handed_on")

    def __init__(self, block: Any) -> None:
        self.block = block
        self.handed_on: Any = None

    @property
    def Exec(self) -> Any:
        return self.block.Exec if self.handed_on is None else self.handed_on


def brain() -> Any:
    return unrealsdk.find_class(BRAIN).ClassDefaultObject


def _holder() -> Any:
    """A module that outlives a reload of this one: the blocks given to the game, and the latest walk of each."""
    holder = sys.modules.setdefault(KEPT_MODULE, types.ModuleType(KEPT_MODULE))
    if not hasattr(holder, "blocks"):
        holder.blocks, holder.latest = [], {}
    if not hasattr(holder, "free"):
        # The blocks read ended by their own walk, by id, at most one entry a kept block; where the search goes on.
        holder.free, holder.cursor = {}, 0
    return holder


def kept() -> list:
    """The blocks given to the game, never freed."""
    return _holder().blocks


def process_event() -> Callable[[int, int, int], None]:
    """The SDK's process_event, from the unrealsdk.dll already loaded in the game; OSError if it is not."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    kernel.GetModuleHandleW.restype = ctypes.c_void_p
    handle = kernel.GetModuleHandleW(SDK_LIBRARY)
    if not handle:
        raise OSError(f"{SDK_LIBRARY} is not loaded")
    call = getattr(ctypes.CDLL(SDK_LIBRARY, handle=handle), PROCESS_EVENT)
    call.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    call.restype = None
    return call


def latent_info(pc: Any) -> Any:
    """No function called back, a fresh number, the player's controller as the object called back: the settings a
    latent function of the game took in game (docs/spawn-boss, 2026-10-05)."""
    return unrealsdk.make_struct("LatentActionInfo", Linkage=-1, UUID=secrets.randbelow(2**31 - 1) + 1,
                                 CallbackTarget=pc)


def _ended_value(block: Any) -> Any:
    """What the game wrote in the block once its walk has ended, else None. An Exec that cannot be read counts as
    running: that block is never taken."""
    _counts["exec_reads"] += 1
    try:
        value = block.Exec
        return value if int(value) != START else None
    except Exception:
        return None


def _ended_block(holder: Any) -> tuple[Any, Any] | None:
    """A kept block whose walk the game has ended, and what it wrote there: one offered by its own walk, read again,
    else the next ended one from where the last search stopped."""
    while holder.free:
        _key, block = holder.free.popitem()
        value = _ended_value(block)
        if value is not None:
            return block, value
    blocks = holder.blocks
    for step in range(len(blocks)):
        index = (holder.cursor + step) % len(blocks)
        value = _ended_value(blocks[index])
        if value is not None:
            holder.cursor = (index + 1) % len(blocks)
            return blocks[index], value
    return None


def walk(actor: Any, goal: Any, pc: Any) -> Walk:
    """Tells the brain to walk actor to goal; gives back the walk, whose block's Exec the game fills in. Only Exec is
    ever read again: the characters a block names may be gone. A kept block whose walk has ended is taken over, every
    field written anew before the call; a new block is made only when none has ended. A failing call raises, its
    block still kept; past KEPT_MAX blocks, none ended, RuntimeError."""
    holder = _holder()
    found = _ended_block(holder)
    if found is None and len(holder.blocks) >= KEPT_MAX:
        raise RuntimeError("no walk block left")
    library = brain()
    function = library.AIScriptedMove.func
    info = latent_info(pc)
    if found is None:
        block = unrealsdk.unreal.WrappedStruct(function, AIActor=actor, GoalActor=goal, Exec=START, LatentInfo=info)
        holder.blocks.append(block)
    else:
        block, value = found
        previous = holder.latest.get(id(block))
        if previous is not None:
            previous.handed_on = value
        # Exec last: a field the SDK refuses leaves the block read as ended, for a later walk.
        block.AIActor, block.GoalActor, block.LatentInfo = actor, goal, info
        block.Exec = START
    given = holder.latest[id(block)] = Walk(block)
    began = time.perf_counter()
    try:
        _sdk_call()(library._get_address(), function._get_address(), block._get_address())
    finally:
        _counts["walks"] += 1
        _counts["walk_ms"] += (time.perf_counter() - began) * 1000.0
    return given


def _sdk_call() -> Callable[[int, int, int], None]:
    """process_event, found once a load of this module: 22 µs a walk to find it again (audit of 16 October 2026)."""
    if _held["call"] is None:
        _held["call"] = process_event()
    return _held["call"]


def gauge() -> dict:
    """Since the last time asked: the walks given, the Execs read to find them a block, the time their calls took;
    then counted afresh."""
    said = {"walks": _counts["walks"], "exec_reads": _counts["exec_reads"], "walk_ms": round(_counts["walk_ms"], 1)}
    _counts.update(walks=0, exec_reads=0, walk_ms=0.0)
    return said


def outcome(given: Any) -> str:
    """What the game last wrote in a walk's Exec."""
    try:
        return str(given.Exec)[:MAX_TEXT]
    except Exception as error:
        return f"unreadable:{type(error).__name__}"


def ended(given: Any) -> bool:
    """Whether the game wrote another value than Start in the walk's Exec: the walk no longer runs. An unreadable
    Exec counts as still running, so that a doubt never gives walk after walk; outcome() writes it down. A walk read
    ended in its own block offers that block to the next walk."""
    try:
        done = int(given.Exec) != START
    except Exception:
        return False
    if done and isinstance(given, Walk) and given.handed_on is None:
        _holder().free[id(given.block)] = given.block
    return done


def abort(actor: Any) -> None:
    """Aborts the brain's scripted task at once. A failing call raises."""
    brain().AbortScriptedBrainTask(AIActor=actor, bStopImmediately=True)
