"""Tests the energy service's wire on a port of its own: the one path it answers, its own plain refusals, and the
one deadline a connection gets however slowly it is fed."""

import pathlib
import socket
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import sdk_stubs  # noqa: E402
import wire_fixture  # noqa: E402

sdk_stubs.install()
from benefix_ohm_attack import energy_wire  # noqa: E402

fails: list[str] = []
PATH = energy_wire.CONSTANTS["path"]


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def ask(path: str = PATH, method: str = "GET"):
    return wire_fixture.ask(port, path, method)


def raw(request: bytes) -> bytes:
    return wire_fixture.raw(port, request)


def sized(length: int) -> bytes:
    """A request for the one path, padded by a header to that many bytes exactly."""
    head, tail = b"GET " + PATH.encode("ascii") + b" HTTP/1.1\r\nX: ", b"\r\n\r\n"
    return head + b"x" * (length - len(head) - len(tail)) + tail


# Port 0: the system picks a free one, so the test never takes the port Kevin's game uses.
server = energy_wire.Server(("127.0.0.1", 0), energy_wire.Handler)
port = server.server_address[1]
asked, noted, payload = [], [], [b'{"energy":50}']
server.asked = lambda: asked.append(1)
server.note = noted.append
server.answer = lambda: payload[0]
thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
thread.start()

status, headers, body = ask()
check("the one path is answered with what the server's owner gives, counted",
      status == 200 and body == b'{"energy":50}' and asked == [1])
check("any origin may read it, nothing keeps a copy, and the connection ends there",
      headers.get("Access-Control-Allow-Origin") == "*" and headers.get("Cache-Control") == "no-store"
      and headers.get("Content-Type") == "application/json" and headers.get("Connection") == "close"
      and headers.get("Content-Length") == str(len(body)))
check("the server does not say what it runs on", headers.get("Server") == "BenefixOhmAttack")
payload[0] = None
check("nothing to give: a plain refusal", ask()[0] == 503 and ask()[2] == energy_wire.FAILED)
payload[0] = b'{"energy":50}'
count = len(asked)
check("another path, or one that only starts the same: not found, not counted",
      ask("/")[0] == 404 and ask(PATH + "/x")[0] == 404 and ask("/")[2] == energy_wire.FAILED and len(asked) == count)

for method in ("POST", "PUT", "DELETE", "HEAD"):
    status, headers, body = ask(method=method)
    check(f"{method} is not offered, refused in the server's own words: the library's page hands the request back",
          status == 501 and body in (energy_wire.FAILED, b"") and headers.get("Content-Type") == "application/json"
          and headers.get("Server") == "BenefixOhmAttack" and b"<" not in body)
check("a request that is not HTTP is refused the same way",
      raw(b"nonsense\r\n\r\n").endswith(energy_wire.FAILED) and b"<html" not in raw(b"nonsense\r\n\r\n").lower())

intruder = socket.socket()
intruder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    intruder.bind(("127.0.0.1", port))
    shared = True
except OSError:
    shared = False
finally:
    intruder.close()
check("no other program can take the same port beside it, even asking to share", not shared)

check("nothing was dropped so far", noted == [])
idle = socket.create_connection(("127.0.0.1", port), timeout=2)
started = time.perf_counter()
status = ask()[0]
waited = time.perf_counter() - started
idle.close()
check("a silent connection delays the next answer by the connection's bound at most",
      status == 200 and waited <= energy_wire.CONNECTION_S + 0.5)
check("and is told to the server's owner as a request dropped", noted == [energy_wire.DROPPED])

slow = wire_fixture.dripping(port, 3.0)
started = time.perf_counter()
status = ask()[0]
waited = time.perf_counter() - started
check("so does a connection fed a byte at a time: its bound is one deadline, not a wait renewed at each byte",
      status == 200 and waited <= energy_wire.CONNECTION_S + 0.5)
slow.join(4.0)
check("the slow client was cut off", not slow.is_alive())
started = time.perf_counter()
stalled = socket.create_connection(("127.0.0.1", port), timeout=2)
time.sleep(0.4)
stalled.sendall(b"G")
status = ask()[0]
waited = time.perf_counter() - started
stalled.close()
check("a connection that sends a byte late and then stalls is cut at its deadline, not a wait after that byte",
      status == 200 and waited <= energy_wire.CONNECTION_S + 0.25)
check("the bound on a request is 8192 bytes: one of exactly that many is answered",
      energy_wire.MAX_REQUEST_BYTES == 8192 and len(sized(8192)) == 8192 and raw(sized(8192)).startswith(b"HTTP/1.1 200"))
check("one byte more and it is dropped unanswered", raw(sized(8193)) == b"")
check("so is one far longer", raw(sized(2 * energy_wire.MAX_REQUEST_BYTES)) == b"")
late = sized(8300)
with socket.create_connection(("127.0.0.1", port), timeout=2) as parted:
    parted.sendall(late[:8000])
    time.sleep(0.1)
    try:
        parted.sendall(late[8000:])
        answer = parted.recv(4096)
    except OSError:
        answer = b""
check("the bound is exact however the bytes arrive: a request too long by its second part is dropped too", answer == b"")
check("after all that the server still answers", ask()[0] == 200)

server.shutdown()
server.server_close()
thread.join(2.0)
check("the server stops and closes its port", not thread.is_alive() and server.socket.fileno() == -1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
