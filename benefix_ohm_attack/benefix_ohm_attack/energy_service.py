"""The beam's energy, told to the game's screen: a loopback HTTP answer the bar's script asks for.

Python must never touch the game's screen itself (docs/candidats/HUD/ERREURS.md, 9: both tries crashed the game).
The mod publishes its energy here at each frame; the script packed into the screen (docs/attaque-rayon/barre/ecran/)
asks for it and draws the bar. One owner: this class holds the server (energy_wire.py) and its one thread from
start to stop.

The answer is a number any program on this PC may read (the screen's origin is not a web one, so every origin is
allowed); nothing can be written, and the game's thread only publishes: nothing asked of the service can stall it.

Only the thread that starts, publishes and stops (the game's) calls `report`: what the server's thread has to say
waits in a short queue until the next publish.
"""

import collections
import json
import math
import re
import threading
import time
from typing import Callable

from .energy_wire import CONNECTION_S, CONSTANTS, Handler, Server

# More than a connection may last: a stop waits for the request in hand, no longer.
STOP_S = 2 * CONNECTION_S
# Two publishes further apart than this are not one movement: the rate between them is not told.
RATE_WINDOW_S = 0.5
# What the bar's script accepts as an element's name (barre/ecran/bar_state.js).
ELEMENT = re.compile(r"[A-Za-z]{1,16}")
UNNAMED = "Unknown"
# The log says once how long this many requests took: the proof of the script's rhythm in game.
RATE_SAMPLE = 100
# More than the server's thread ever has to say between two publishes.
PENDING = 8
HEARD = "the game's screen asks for the energy: the bar's script runs"


class EnergyService:
    """Owns the local server from start to stop; `report` receives one sentence per event, each kind once."""

    def __init__(self, report: Callable[[str], None]) -> None:
        self._report = report
        self._server: Server | None = None
        self._thread: threading.Thread | None = None
        # (energy, maximum, rate per second, element, when published): replaced whole, read whole.
        self._state: tuple[float, float, float, str, float] | None = None
        self._pending: collections.deque[str] = collections.deque(maxlen=PENDING)
        self._noted: set[str] = set()
        self._asked = 0
        self._first_asked_s = 0.0

    def start(self, port: int | None = None) -> bool:
        """Opens the port and serves in a background thread; False, and said, when the port cannot be had."""
        if self._server is not None:
            return True
        try:
            server = Server((CONSTANTS["host"], CONSTANTS["port"] if port is None else port), Handler)
        except OSError as error:
            # The code tells a port another program holds from one Windows forbids.
            code = getattr(error, "winerror", None) or error.errno
            self._report(f"the energy service could not open its port (error {code}): the energy bar stays hidden")
            return False
        self._pending.clear()
        self._noted.clear()
        self._asked = 0
        server.note = self._note
        server.asked = self._count
        server.answer = self._answer
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05},
                                  name="beam-attack-energy", daemon=True)
        thread.start()
        self._server, self._thread = server, thread
        return True

    def port(self) -> int:
        if self._server is None:
            raise RuntimeError("the energy service is not running")
        return int(self._server.server_address[1])

    def _note(self, sentence: str) -> None:
        """What the server's thread has to say, each sentence once, kept for the game's thread to report."""
        if sentence not in self._noted:
            self._noted.add(sentence)
            self._pending.append(sentence)

    def _count(self) -> None:
        """Called by the server's thread for each request on the energy's path."""
        self._asked += 1
        if self._asked == 1:
            self._first_asked_s = time.perf_counter()
            self._note(HEARD)
        elif self._asked == RATE_SAMPLE + 1:
            self._note(f"the bar's script asked {RATE_SAMPLE} times in {time.perf_counter() - self._first_asked_s:.1f} s")

    def _tell(self) -> None:
        while self._pending:
            self._report(self._pending.popleft())

    def publish(self, energy: float, maximum: float, element: str) -> None:
        """What the bar must show now; called by the game's thread at each frame."""
        self._tell()
        if not (math.isfinite(energy) and math.isfinite(maximum) and maximum > 0):
            return
        # perf_counter, not monotonic: on Windows the latter may tick every 16 ms, a whole frame.
        now = time.perf_counter()
        energy = min(max(float(energy), 0.0), float(maximum))
        rate = 0.0
        before = self._state
        if before is not None and before[1] == maximum and 0.0 < now - before[4] <= RATE_WINDOW_S:
            rate = (energy - before[0]) / (now - before[4])
        name = element if isinstance(element, str) and ELEMENT.fullmatch(element) else UNNAMED
        self._state = (energy, float(maximum), rate, name, now)

    def clear(self) -> None:
        """Nothing to show: the next answers are plain refusals, and the bar's script hides the bar within staleMs.
        Called by the game's thread in place of publish."""
        self._tell()
        self._state = None

    def _answer(self) -> bytes | None:
        state = self._state
        if state is None:
            return None
        energy, maximum, rate, element, published = state
        payload = json.dumps({
            "version": CONSTANTS["version"], "energy": round(energy, 2), "max": round(maximum, 2),
            "rate": round(rate, 2), "age": round(time.perf_counter() - published, 3), "element": element,
        }, separators=(",", ":")).encode("ascii")
        return payload if len(payload) <= CONSTANTS["maxResponseBytes"] else None

    def stop(self) -> bool:
        """Closes the port. The wait is bounded: a server that will not stop is left to its daemon thread, said."""
        server, thread = self._server, self._thread
        if server is None:
            return True
        self._server, self._thread, self._state = None, None, None

        def close() -> None:
            server.shutdown()
            server.server_close()

        closer = threading.Thread(target=close, name="beam-attack-energy-stop", daemon=True)
        closer.start()
        closer.join(STOP_S)
        thread.join(max(0.0, STOP_S / 2))
        self._tell()
        if closer.is_alive() or thread.is_alive():
            self._report("the energy service did not stop in time")
            return False
        return True
