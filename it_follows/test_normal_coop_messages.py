"""Tests the Hardcore's co-op messages (normal/coop_messages.py) on fake controllers: a host's text read only with the
mark, a known word and a whole number in bounds; a guest's place read only at MARK_X with a whole percent in bounds;
the host's door keeps a guest's marked place from the game and lets the rest through; the guest's door keeps the
host's marked texts; at most MAX_PENDING kept, the others counted; each taken once; the stop unhooks; what each side
sends."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows.normal import coop_messages  # noqa: E402

fails: list[str] = []
Block = sys.modules["unrealsdk.hooks"].Block
sys.modules["unrealsdk"].unreal.WeakPointer = lambda target: (lambda: target)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def place(x: float, y: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(NewLoc=types.SimpleNamespace(X=x, Y=y, Z=0.0))


try:
    read = coop_messages.read_text
    check("a host's text read with the mark, a known word and a number in bounds",
          read("ItFollows:ask") == ("ask", 0) and read("ItFollows:kills 3") == ("kills", 3)
          and read("ItFollows:run 1400") == ("run", 1400) and read("ItFollows:run 1000") == ("run", 1000))
    check("anything else not read", all(read(text) is None for text in (
        "kills 3", "ItFollows:kills", "ItFollows:kills 0", "ItFollows:kills -2", "ItFollows:kills 1001",
        "ItFollows:kills 2.5", "ItFollows:ask 1", "ItFollows:spawn 3", "ItFollows:run 999", "ItFollows:run 2001",
        "ItFollows:run", "ItFollows:kills " + "9" * 40)))
    percent = coop_messages.read_percent
    check("a guest's place read at MARK_X with a whole percent in bounds", percent(coop_messages.MARK_X, 7.0) == 7
          and percent(coop_messages.MARK_X, 0.0) == 0)
    check("anything else not read", all(percent(x, y) is None for x, y in (
        (100.0, 7.0), (coop_messages.MARK_X, -1.0), (coop_messages.MARK_X, 7.5), (coop_messages.MARK_X, 10001.0))))

    host = coop_messages.Link(host=True)
    host.start()
    heard = state["hooks"][coop_messages.IDENTIFIER].fn
    guest_pc = object()
    check("the host keeps a guest's marked place from the game, lets the rest through",
          heard(guest_pc, place(coop_messages.MARK_X, 4.0), None, None) is Block
          and heard(guest_pc, place(5.0, 4.0), None, None) is None
          and heard(guest_pc, types.SimpleNamespace(), None, None) is None)
    taken = host.take()
    check("each heard taken once, with its controller", len(taken) == 1 and taken[0][0]() is guest_pc
          and taken[0][1] == 4 and host.take() == [])
    for _ in range(coop_messages.MAX_PENDING + 2):
        heard(guest_pc, place(coop_messages.MARK_X, 1.0), None, None)
    check("at most MAX_PENDING kept, the others counted", len(host.take()) == coop_messages.MAX_PENDING
          and host.dropped == 2)
    check("the stop unhooks", host.stop() == "removed" and coop_messages.IDENTIFIER not in state["hooks"]
          and host.stop() == "inactive")

    guest = coop_messages.Link(host=False)
    guest.start()
    heard = state["hooks"][coop_messages.IDENTIFIER].fn
    check("the guest keeps the host's marked texts from the game, lets the rest through",
          heard(None, types.SimpleNamespace(S="ItFollows:kills 2"), None, None) is Block
          and heard(None, types.SimpleNamespace(S="Hello"), None, None) is None
          and guest.take() == [(None, ("kills", 2))])
    guest.stop()

    sent: list = []
    controller = types.SimpleNamespace(ClientMessage=lambda *args: sent.append(args),
                                       ServerSetSpectatorLocation=lambda *args: sent.append(args))
    coop_messages.tell_guest(controller, coop_messages.KILLS, 3)
    coop_messages.tell_guest(controller, coop_messages.ASK)
    coop_messages.tell_host(controller, 12)
    coop_messages.tell_guest(controller, coop_messages.RUN, 1400)
    check("what each side sends", sent[0] == ("ItFollows:kills 3", "None", 0.0) and sent[1][0] == "ItFollows:ask"
          and sent[2][0].X == coop_messages.MARK_X and sent[2][0].Y == 12.0
          and coop_messages.read_percent(sent[2][0].X, sent[2][0].Y) == 12 and sent[3][0] == "ItFollows:run 1400")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
