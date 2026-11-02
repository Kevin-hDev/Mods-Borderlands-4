# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of server.py: the real loopback service on a free port, with a fake Windows. python test_server.py"""

import http.client
import io
import socket
import sys
import tempfile
import time
from pathlib import Path

import package_path  # noqa: F401
from logs_conflicts import conflicts, log_file, masking, protocol, routes, server
from fixture_windows import FakeApi, FakeWindows

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


C = protocol.load_constants()
BASE = C["http"]["basePath"]


def service(folder: Path):
    log = folder / "unrealsdk.log"
    log.write_bytes(b"line\n")
    lines = []
    windows = FakeWindows()
    parts = {"log_file": log_file, "masking": masking, "conflicts": conflicts, "windows": windows, "api": FakeApi(),
             "log_path": log, "folder": folder, "mask_patterns": (), "mods": lambda: [], "version": "1.0.0"}
    made = server.Service(C, lambda service_log: routes.Routes(C, protocol, parts, service_log), lines.append, port=0)
    made.start()
    return made, windows, lines


def call(port, method, path, body=None, origin=None, length=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    extra = {"Origin": origin} if origin else {}
    if length is not None:
        extra["Content-Length"] = str(length)
    connection.request(method, path, body=body, headers=extra)
    response = connection.getresponse()
    result = (response.status, dict(response.getheaders()), response.read())
    connection.close()
    return result


def test_answers(folder: Path):
    made, windows, lines = service(folder)
    status, headers, _ = call(made.port, "GET", BASE + "hello")
    expect(status == 200 and headers.get("X-Content-Type-Options") == "nosniff", "hello answered, nosniff set")
    status, headers, _ = call(made.port, "GET", BASE + "log", origin="coui://uiresources")
    expect(status == 200 and headers.get("Access-Control-Allow-Origin") == "coui://uiresources",
           "the game's origin may read the log")
    status, headers, _ = call(made.port, "GET", BASE + "log", origin="https://example.com")
    expect(status == 403 and "Access-Control-Allow-Origin" not in headers, "a web page refused, may not read")
    status, _, _ = call(made.port, "POST", BASE + "copy", body=b"", length=0)
    expect(status == 200 and len(windows.copied) == 1, "copy with an empty body")
    # The size alone is announced, no body sent: the answer can only come before the body is read. A body sent
    # unread made Windows reset the connection now and then, and the client lost the answer (fourth review).
    status, _, _ = call(made.port, "POST", BASE + "copy", length=2000)
    expect(status == 413 and len(windows.copied) == 1, "a body too long refused before it is read")
    expect(made.stop(), "stops on request")
    expect(lines[0].startswith("[LogsConflicts] STARTED port=") and "STOPPED reason=stop_command" in lines[-1],
           "start and stop logged")


def test_silent_client(folder: Path):
    made, _, lines = service(folder)
    # Another cause's budget spent first: the timeout's line then shows it is counted on its own.
    for _ in range(C["http"]["maxFailedLogs"]):
        try:
            raise ValueError("another cause")
        except ValueError:
            made.server.handle_error(None, None)
    # A refused request goes through the same trace function with a status number: it is no timeout.
    refused = socket.create_connection(("127.0.0.1", made.port), timeout=3)
    refused.sendall(b"BREW / HTTP/1.1\r\n\r\n")
    answer = refused.recv(4096)
    refused.close()
    expect(answer.startswith(b"HTTP/1.1 501") and not any("TimeoutError" in line for line in lines),
           "a request with an unknown method writes no timeout line")
    quiet = socket.create_connection(("127.0.0.1", made.port))
    start = time.monotonic()
    status, _, _ = call(made.port, "GET", BASE + "hello")
    expect(status == 200 and time.monotonic() - start < C["http"]["clientTimeoutS"] + 1.5,
           "a client that sends nothing holds the thread no longer than its delay")
    quiet.close()
    made.stop()
    expect(sum("REQUEST_FAILED error=TimeoutError" in line for line in lines) == 1,
           "a request cut at its deadline writes one line, counted apart from other causes")


def test_slow_client(folder: Path):
    """A client sending a byte now and then is cut at the request's deadline, not kept alive by each byte."""
    made, _, _ = service(folder)
    slow = socket.create_connection(("127.0.0.1", made.port))
    budget = C["http"]["clientTimeoutS"]
    # Under the old rule, a delay per read, each byte sent within the delay kept the connection open.
    slow.settimeout(budget / 4)
    start = time.monotonic()
    closed = False
    while time.monotonic() - start < budget + 2:
        try:
            slow.sendall(b"G")
            if slow.recv(1, socket.MSG_PEEK) == b"":
                closed = True
                break
        except socket.timeout:
            pass
        except OSError:
            closed = True
            break
    elapsed = time.monotonic() - start
    slow.close()
    expect(closed and elapsed < budget + 1, f"a dripping client cut near its deadline ({elapsed:.1f} s)")
    status, _, _ = call(made.port, "GET", BASE + "hello")
    expect(status == 200, "the service answers again afterwards")
    made.stop()


def test_answer_budget(folder: Path):
    """The answer gets a budget of its own: a request read slowly must not leave it the moments left (review)."""
    made, _, _ = service(folder)
    seen = []
    handler = made.server.RequestHandlerClass
    original = handler.send_response

    def spy(self, *args):
        seen.append(self.connection.gettimeout())
        return original(self, *args)

    handler.send_response = spy
    slow = socket.create_connection(("127.0.0.1", made.port), timeout=3)
    slow.sendall(f"GET {BASE}hello HTTP/1.1\r\nHost: 127.0.0.1:{made.port}\r\n".encode("ascii"))
    time.sleep(0.5)
    slow.sendall(b"\r\n")
    slow.recv(4096)
    slow.close()
    made.stop()
    expect(seen == [C["http"]["clientTimeoutS"]], f"the answer's budget is whole ({seen})")


def test_failure_line(folder: Path):
    made, _, lines = service(folder)
    for _ in range(C["http"]["maxFailedLogs"] + 2):
        try:
            raise ValueError("inside the standard library")
        except ValueError:
            made.server.handle_error(None, None)
    expect(sum("REQUEST_FAILED error=ValueError" in line for line in lines) == C["http"]["maxFailedLogs"],
           "a failing request writes one bounded line, never a traceback")
    try:
        raise ConnectionAbortedError("the page gave up")
    except ConnectionAbortedError:
        made.server.handle_error(None, None)
    expect(any("REQUEST_FAILED error=ConnectionAbortedError" in line for line in lines),
           "a failure of another cause still shows")
    made.stop()


def test_stop_when_ended(folder: Path):
    made, _, _ = service(folder)
    made.stop()
    again = server.Service(C, lambda _log: made.routes, lambda _line: None, port=0)
    # As a thread ended by a socket error leaves it: the socket closed. A connection to it would take a second.
    again.server.server_close()
    start = time.monotonic()
    again.request_stop("disabled")
    expect(time.monotonic() - start < 0.2 and again.stop_requested,
           "a thread already ended: the stop waits for nothing")


def test_reader_limit():
    class Connection:
        def __init__(self, chunks):
            self.chunks = list(chunks)

        def settimeout(self, _seconds):
            pass

        def recv(self, _size):
            return self.chunks.pop(0) if self.chunks else b""

    reader = server.RequestReader(Connection([b"abcdef\nrest"]), 2, io.BytesIO())
    expect(reader.readline(3) == b"abc" and reader.readline() == b"def\n" and reader.read(4) == b"rest",
           "a line longer than its limit is cut at the limit, the rest kept for the next read")


def test_body_rule():
    expect(server.request_body("", io.BytesIO(b""), 10) == b"", "no length: empty body")
    expect(server.request_body("0", io.BytesIO(b""), 10) == b"", "zero: empty body")
    expect(server.request_body("3", io.BytesIO(b"abc"), 10) == b"abc", "body within the limit read")
    for length in ("11", "-1", "x", "1e3", "\u00b2", "\u0663", "9" * 10, " 3"):
        expect(server.request_body(length, io.BytesIO(b"x" * 20), 10) is None, f"length {length!r} refused")


with tempfile.TemporaryDirectory() as temporary:
    test_answers(Path(temporary))
    test_silent_client(Path(temporary))
    test_slow_client(Path(temporary))
    test_answer_budget(Path(temporary))
    test_failure_line(Path(temporary))
    test_stop_when_ended(Path(temporary))
test_reader_limit()
test_body_rule()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
