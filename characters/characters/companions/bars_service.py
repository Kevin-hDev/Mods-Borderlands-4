"""The companions' health and shield, told to the game's screen through a loopback HTTP answer the bars' script asks
for (decision 36 of docs/renforts/README.md; the script: docs/renforts/sondes/companion_bars/), with whether the
bars are shown and the Vault Hunter aimed at, which the aimed bar's page asks for (decision 53; its script:
docs/renforts/sondes/nameplate_trial/). Benefix Ohm Attack's
energy_service.py, the way verified in game (its bar, 1 October 2026), taken over; then the trials' copy
(docs/renforts/sondes, trials 178 to 182, the bars validated by Kevin at trial 179), moved here.

Python must never touch the game's screen itself (docs/candidats/HUD/ERREURS.md, 9: both tries crashed the game).
One owner: this class holds the server (bars_wire.py) and its one thread from start to stop. Nothing can be written
through it, and the game's thread only publishes: nothing asked of the service can stall it. Only the game's thread
calls `report`: what the server's thread has to say waits in a short queue until the next publish.
"""

import collections
import json
import math
import threading
import time
from typing import Any, Callable

# More than a connection may last: a stop waits for the request in hand, no longer.
STOP_FACTOR = 2
# The log says once how long this many requests took: the proof of the script's rhythm in game.
RATE_SAMPLE = 100
# More than the server's thread ever has to say between two publishes.
PENDING = 8
HEARD = "the game's screen asks for the companions: the bars' script runs"


def share(value: Any) -> float | None:
    """A part from 0 to 1, rounded; None for anything else."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return round(min(max(float(value), 0.0), 1.0), 3)


def name(value: Any, most: int) -> str:
    """A name the screen can show: printable, any space a plain one (the game's French writes a no-break space in
    « Saumure type M », not printable to Python), at most `most` characters; '?' for anything else."""
    if not isinstance(value, str):
        return "?"
    shown = "".join(" " if letter.isspace() else letter for letter in value if letter.isprintable()
                    or letter.isspace()).strip()[:most]
    return shown or "?"


class CompanionBars:
    """Owns the local server from start to stop. wire: bars_wire.py; constants: assets/companion_bars.json;
    report receives one sentence per event, each kind once."""

    def __init__(self, wire: Any, constants: dict, report: Callable[[str], None]) -> None:
        self._wire, self._constants, self._report = wire, constants, report
        self._server: Any = None
        self._thread: threading.Thread | None = None
        # (what is shown, when published): replaced whole, read whole.
        self._state: tuple[dict, float] | None = None
        self._pending: collections.deque[str] = collections.deque(maxlen=PENDING)
        self._noted: set[str] = set()
        self.asked = 0
        self._first_asked_s = 0.0

    def start(self, port: int | None = None) -> bool:
        """Opens the port and serves in a background thread; False, and said, when the port cannot be had."""
        if self._server is not None:
            return True
        try:
            server = self._wire.Server((self._constants["host"], self._constants["port"] if port is None else port),
                                       self._wire.Handler)
        except OSError as error:
            code = getattr(error, "winerror", None) or error.errno
            self._report(f"the companions' bars service could not open its port (error {code}): no bars")
            return False
        server.path, server.note, server.asked, server.answer = (self._constants["path"], self._note, self._count,
                                                                 self._answer)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05},
                                  name="characters-bars", daemon=True)
        thread.start()
        self._server, self._thread = server, thread
        return True

    def port(self) -> int:
        if self._server is None:
            raise RuntimeError("the companions' bars service is not running")
        return int(self._server.server_address[1])

    def _note(self, sentence: str) -> None:
        if sentence not in self._noted:
            self._noted.add(sentence)
            self._pending.append(sentence)

    def _count(self) -> None:
        """Called by the server's thread for each request on the path."""
        self.asked += 1
        if self.asked == 1:
            self._first_asked_s = time.perf_counter()
            self._note(HEARD)
        elif self.asked == RATE_SAMPLE + 1:
            self._note(f"the bars' script asked {RATE_SAMPLE} times in "
                       f"{time.perf_counter() - self._first_asked_s:.1f} s")

    def _tell(self) -> None:
        while self._pending:
            self._report(self._pending.popleft())

    def publish(self, rows: list, shown: bool = True, aimed: str | None = None) -> None:
        """What the screen must show now: (name, health, shield, dead) each, at most `most`; whether the bars are
        shown; the name of the hunter aimed at, or None. Called by the game's thread."""
        self._tell()
        most, longest = self._constants["most"], self._constants["nameMost"]
        kept = [{"name": name(row[0], longest), "health": share(row[1]), "shield": share(row[2]),
                 "dead": row[3] is True} for row in list(rows)[:most]]
        self._state = ({"shown": shown is True, "aimed": None if aimed is None else name(aimed, longest),
                        "companions": kept}, time.perf_counter())

    def _answer(self) -> bytes | None:
        state = self._state
        if state is None:
            return None
        shown, published = state
        payload = json.dumps({"version": self._constants["version"], "age": round(time.perf_counter() - published, 3),
                              **shown}, separators=(",", ":")).encode("ascii")
        return payload if len(payload) <= self._constants["maxResponseBytes"] else None

    def stop(self) -> bool:
        """Closes the port. The wait is bounded: a server that will not stop is left to its daemon thread, said."""
        server, thread = self._server, self._thread
        if server is None:
            return True
        self._server, self._thread, self._state = None, None, None

        def close() -> None:
            server.shutdown()
            server.server_close()

        closer = threading.Thread(target=close, name="characters-bars-stop", daemon=True)
        closer.start()
        wait = STOP_FACTOR * self._wire.CONNECTION_S
        closer.join(wait)
        thread.join(max(0.0, wait / 2))
        self._tell()
        if closer.is_alive() or thread.is_alive():
            self._report("the companions' bars service did not stop in time")
            return False
        return True
