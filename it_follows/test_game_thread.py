"""Tests the game's thread guard: a hook called on the thread it was set from makes that the game's thread; a call
from another thread does not pass, is counted, and only the first is said, with both threads in hexadecimal. A hook
set from another thread than the game's (the mod's load, trial 207) takes the game's thread once known, or the
thread of its first call until then, said."""

import pathlib
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import game_thread  # noqa: E402

fails: list[str] = []
MAIN = threading.get_native_id()


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def on_worker(work) -> tuple:
    """work() run on another thread: what it answered, and that thread's number."""
    out: list = []
    ident: list[int] = []

    def run() -> None:
        ident.append(threading.get_native_id())
        out.append(work())

    worker = threading.Thread(target=run)
    worker.start()
    worker.join(5)
    return (out[0] if out else None), (ident[0] if ident else 0)


said: list[tuple] = []


def say(event: str, **fields) -> None:
    said.append((event, fields))


guard = game_thread.Guard("team", say)
check("before any call the game's thread is not known", game_thread._game[0] is None)
check("on the thread the hook was set from: passes", guard.here() is True)
check("that call makes it the game's thread, nothing counted nor said", game_thread._game[0] == MAIN
      and guard.away == 0 and said == [])
answers, worker_id = on_worker(lambda: [guard.here(), guard.here(), guard.here()])
check("from another thread: refused at each call", answers == [False, False, False])
check("from another thread: each call counted", guard.away == 3)
check("from another thread: only the first said", len(said) == 1 and said[0][0] == "hook_off_thread")
fields = said[0][1] if said else {}
check("the hook named", fields.get("what") == "team")
check("the game's thread in hexadecimal", fields.get("game") == f"{MAIN:x}")
check("the other thread in hexadecimal, another", fields.get("thread") == f"{worker_id:x}" and worker_id != MAIN)
check("back on the game's thread: passes again", guard.here() is True and guard.away == 3)

said.clear()
known, _ = on_worker(lambda: game_thread.Guard("lost_loot", say))
check("set from another thread, the game's known: its first call on the game's passes",
      known.here() is True and known.away == 0 and said == [])
answer, _ = on_worker(known.here)
check("and a call from the thread it was set from is refused", answer is False and known.away == 1)
also, _ = on_worker(lambda: game_thread.Guard("colours", say))
first, _ = on_worker(also.here)
check("set elsewhere, its first call elsewhere: refused, the game's thread taken", first is False
      and also.thread == MAIN and also.away == 1)

said.clear()
game_thread._game[0] = None
early, loader = on_worker(lambda: game_thread.Guard("lost_loot", say))
check("set at the load, the game's thread unknown: its first call passes", early.here() is True)
check("that thread taken, said with the thread it was set from", early.thread == MAIN and len(said) == 1
      and said[0][0] == "hook_thread_taken" and said[0][1].get("thread") == f"{MAIN:x}"
      and said[0][1].get("set_from") == f"{loader:x}")
check("a thread only taken does not make the game's thread known", game_thread._game[0] is None)
answer, _ = on_worker(early.here)
check("then a call from another thread refused", answer is False and early.away == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
