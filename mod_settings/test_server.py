# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of server.py on a temporary port, never the mod's own. python test_server.py"""

import copy
import http.client
import json
import socket
import sys
import threading
import time

import package_path  # noqa: F401  (before the package's modules)
import fixture_world
import protocol
import server

BASE = protocol.load_constants()
PATHS = BASE["http"]
FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


class Capture:
    def __init__(self, on_end):
        self.cancelled = threading.Event()

    def start(self, ident):
        return True

    def cancel(self):
        self.cancelled.set()

    def status(self):
        return "idle", None


def start(**http):
    constants = copy.deepcopy(BASE)
    constants["http"].update(http)
    logs = []

    stopped = threading.Event()

    def make_routes(log):
        return fixture_world.World(constants, log, Capture).routes

    service = server.Service(constants, make_routes, logs.append, port=0, on_stopped=stopped.set)
    service.stopped = stopped
    # Each turn of the service's loop is counted: idle, the loop must not turn at all.
    service.turns = 0
    handle = service.server.handle_request

    def counted():
        service.turns += 1
        handle()

    service.server.handle_request = counted
    service.start()
    return service, logs


def request(service, method, path, body=None, origin=None, site=None):
    connection = http.client.HTTPConnection("127.0.0.1", service.port, timeout=5)
    connection.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
    connection.putheader("Host", f"127.0.0.1:{service.port}")
    if origin:
        connection.putheader("Origin", origin)
    if site:
        connection.putheader("Sec-Fetch-Site", site)
    if body is not None:
        connection.putheader("Content-Length", str(len(body)))
    connection.endheaders(body)
    response = connection.getresponse()
    result = response.status, response.read(), response.getheader("Access-Control-Allow-Origin")
    connection.close()
    return result


service, logs = start()
check("started line", logs and logs[0].startswith("[ModSettings] STARTED port="))
status, payload, cors = request(service, "GET", PATHS["modelPath"], origin="coui://uiresources")
check("model answered", status == 200 and json.loads(payload)["revision"] == 1)
check("cors echoes the game origin", cors == "coui://uiresources")
status, _payload, cors = request(service, "GET", PATHS["modelPath"], origin="null", site="cross-site")
check("a web page's frame gets neither the model nor the right to read it", status == 403 and cors is None)
status, _payload, cors = request(service, "GET", PATHS["modelPath"], origin="http://evil.test")
check("nor does another origin", status == 403 and cors is None)
body = json.dumps({"marker": BASE["marker"], "event": "gamepad", "name": "up"})
check("event accepted", request(service, "POST", PATHS["eventPath"], body.encode())[0] == 200)
check("oversized body refused", request(service, "POST", PATHS["eventPath"], b"x" * (PATHS["maxRequestBytes"] + 1))[0]
      == 413)

# Idle, the thread sleeps on the socket: no wake-up of its own between requests (OPTI.md, rule 19). The client has
# its answer before the service's turn ends: counted at once, the service's next turn (waiting) read as a wake-up.
time.sleep(0.3)
before = service.turns
time.sleep(1.2)
check("idle service does not wake up", service.turns == before and service.thread.is_alive())

started = time.monotonic()
service.request_stop("stop_command")
check("stop request returns at once", time.monotonic() - started < 0.5)
service.thread.join(2)
check("stop wakes the sleeping thread", not service.thread.is_alive())
check("stopped line", logs[-1].startswith("[ModSettings] STOPPED reason=stop_command"))
check("stop cancels a running capture", service.routes.capture.cancelled.is_set())
check("on_stopped runs once the thread ends", service.stopped.is_set())

# The mod's service has no time nor request budget: it runs while the mod is on.
service, _ = start()
for _ in range(5):
    request(service, "GET", PATHS["modelPath"])
check("keeps serving", service.thread.is_alive())
service.stop()

# A second service cannot take a port already held.
first, _ = start()
try:
    server.Service(BASE, lambda log: None, lambda _m: None, port=first.port)
    check("second service refused on a held port", False)
except OSError:
    check("second service refused on a held port", True)
first.stop()

# A silent client does not hold the thread past a stop.
silent, _ = start()
idle = socket.create_connection(("127.0.0.1", silent.port))
time.sleep(0.2)
check("stop despite a silent client", silent.stop(timeout_s=4))
idle.close()

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
