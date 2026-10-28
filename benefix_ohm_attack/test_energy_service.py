"""Tests the energy service on a port of its own: what it answers, what it tells the log and from which thread, and
that it stops and frees its port. Its wire's own refusals and deadline are test_energy_wire.py's."""

import json
import pathlib
import socket
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402
import wire_fixture  # noqa: E402

sdk_stubs.install()
from benefix_ohm_attack import energy_service, energy_wire  # noqa: E402

fails: list[str] = []


class Said(list):
    """What the service reported, and the threads it reported from."""

    threads: set[str] = set()

    def append(self, sentence: str) -> None:
        self.threads.add(threading.current_thread().name)
        super().append(sentence)


said = Said()
# Three requests instead of a hundred: the rhythm's line is the same, the test is not slowed.
energy_service.RATE_SAMPLE = 3


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def ask(port: int, path: str = energy_service.CONSTANTS["path"], method: str = "GET"):
    return wire_fixture.ask(port, path, method)


service =energy_service.EnergyService(said.append)
# Port 0: the system picks a free one, so the test never takes the port Kevin's game uses.
check("the service starts", service.start(port=0) is True and service.port() > 0)
check("starting twice keeps the one server", service.start(port=0) is True)
port = service.port()

status, headers, body = ask(port)
check("before the mod publishes anything: no value, a plain refusal", status == 503 and body == energy_wire.FAILED)
check("the server's thread reports nothing by itself", said == [])

service.publish(63.257, 100.0, "Fire")
check("the first request is told at the next publish: the proof that the bar's script runs",
      said == [energy_service.HEARD])
status, headers, body = ask(port)
answer = json.loads(body)
check("the published energy is answered", status == 200 and answer["energy"] == 63.26 and answer["max"] == 100.0
      and answer["element"] == "Fire" and answer["version"] == energy_service.CONSTANTS["version"])
check("the first publish has no rate yet", answer["rate"] == 0.0)
check("the answer says how old it is", 0.0 <= answer["age"] < 1.0)
check("any origin may read it, and nothing keeps a copy",
      headers.get("Access-Control-Allow-Origin") == "*" and headers.get("Cache-Control") == "no-store"
      and headers.get("Content-Type") == "application/json" and headers.get("Connection") == "close")
check("the server does not say what it runs on", headers.get("Server") == "BenefixOhmAttack")
check("the answer fits the bound the script reads", len(body) <= energy_service.CONSTANTS["maxResponseBytes"])

time.sleep(0.1)
service.publish(61.0, 100.0, "Fire")
check("the second request is not told again", said == [energy_service.HEARD])
rate = json.loads(ask(port)[2])["rate"]
check("two publishes give the rate between them, per second", -30.0 < rate < -15.0)
ask(port, "/beam-attack/v1/other")
service.publish(61.0, 100.0, "Fire")
check("a request for another path is not counted", said == [energy_service.HEARD])
ask(port)
service.publish(61.0, 100.0, "Fire")
check("once the sample of requests is reached, the time it took is told",
      len(said) == 2 and said[1].startswith("the bar's script asked 3 times in ") and said[1].endswith(" s"))
for _ in range(4):
    ask(port)
service.publish(61.0, 100.0, "Fire")
check("further requests tell nothing more", len(said) == 2)
service._server.handle_error(None, None)
service._server.handle_error(None, None)
service.publish(61.0, 100.0, "Fire")
check("requests that fail are told once, however many fail", said[2:] == [energy_wire.DROPPED])
time.sleep(0.15)
check("an answer asked later is older", json.loads(ask(port)[2])["age"] >= 0.15)
time.sleep(energy_service.RATE_WINDOW_S)
service.publish(40.0, 100.0, "Fire")
check("publishes too far apart are not one movement: no rate", json.loads(ask(port)[2])["rate"] == 0.0)

service.publish(500.0, 100.0, "Fire")
check("more than the maximum is the maximum", json.loads(ask(port)[2])["energy"] == 100.0)
service.publish(-5.0, 100.0, "Fire")
check("less than nothing is nothing", json.loads(ask(port)[2])["energy"] == 0.0)
service.publish(50.0, 100.0, "Fire")
for label, values in (("an energy that is not a number", (float("nan"), 100.0, "Fire")),
                      ("an endless maximum", (10.0, float("inf"), "Fire")),
                      ("a maximum of zero", (10.0, 0.0, "Fire"))):
    service.publish(*values)
    check(f"{label}: the last good value stays", json.loads(ask(port)[2])["energy"] == 50.0)
service.publish(50.0, 100.0, 'Fire"; <b>')
check("an element's name the script would refuse is replaced", json.loads(ask(port)[2])["element"] == "Unknown")
service.publish(50.0, 100.0, None)
check("so is a name that is not text", json.loads(ask(port)[2])["element"] == "Unknown")

service.clear()
check("cleared, the service refuses plainly, as before any value: the bar's script hides the bar",
      ask(port)[0] == 503 and ask(port)[2] == energy_wire.FAILED)
service.publish(50.0, 100.0, "Fire")
check("a value published after that is answered again, with no rate from before the gap",
      json.loads(ask(port)[2])["energy"] == 50.0 and json.loads(ask(port)[2])["rate"] == 0.0)

check("another path: not found, nothing told", ask(port, "/beam-attack/v1/other")[0] == 404
      and ask(port, "/")[2] == energy_wire.FAILED)
check("a path that only starts the same: not found", ask(port, energy_service.CONSTANTS["path"] + "/x")[0] == 404)
check("writing is not offered", ask(port, method="POST")[0] == 501 and ask(port, method="PUT")[0] == 501)
check("the value survived all that", json.loads(ask(port)[2])["energy"] == 50.0)
bound = energy_service.CONSTANTS["maxResponseBytes"]
energy_service.CONSTANTS["maxResponseBytes"] = 10
check("an answer longer than the bound the script reads is not sent", ask(port)[0] == 503)
energy_service.CONSTANTS["maxResponseBytes"] = bound

check("the service listens on this PC only",
      service._server.server_address[0] == "127.0.0.1" == energy_service.CONSTANTS["host"])
other =energy_service.EnergyService(said.append)
check("a second service on the same port is refused, and says why and that the bar stays hidden",
      other.start(port=port) is False and "stays hidden" in said[-1] and "(error " in said[-1]
      and "(error None)" not in said[-1])
check("stopping a service that never started is fine", other.stop() is True)

slow = wire_fixture.dripping(port, 3.0)
held = service._server
started = time.perf_counter()
check("the service stops, a slow connection in hand or not", service.stop() is True
      and time.perf_counter() - started <= energy_service.STOP_S + 0.5)
check("and closes its port's socket itself", held.socket.fileno() == -1)
slow.join(4.0)
check("and stopping twice is fine", service.stop() is True)
try:
    ask(port)
    check("its port no longer answers", False)
except OSError:
    check("its port no longer answers", True)
check("the port is free for a new start", service.start(port=port) is True)
told = len(said)
check("a new start begins with no value", ask(port)[0] == 503)
service.stop()
check("what was left to say is told at the stop, a new start having forgotten what the last one said",
      said[told:] == [energy_service.HEARD])
service.start(port=port)
told = len(said)
ask(port)
service.clear()
check("what the server's thread has to say is told when the bar is hidden too", said[told:] == [energy_service.HEARD])
service.stop()

service.start(port=port)
told = len(said)
idle = socket.create_connection(("127.0.0.1", port), timeout=2)
time.sleep(energy_wire.CONNECTION_S + 0.3)
idle.close()
service.clear()
check("a request given up on is told once", said[told:] == [energy_wire.DROPPED])
stuck = service._server
stuck.shutdown = lambda: time.sleep(energy_service.STOP_S * 3)
check("a server that will not stop is left behind, and said", service.stop() is False
      and said[-1] == "the energy service did not stop in time")
check("every line was reported by the thread that publishes, none by the server's", said.threads == {"MainThread"})

try:
    energy_service.EnergyService(said.append).port()
    check("asking the port of a stopped service is an error", False)
except RuntimeError:
    check("asking the port of a stopped service is an error", True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
