# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of protocol.py: the request guard, the routes, the events, the bounds. python test_protocol.py"""

import json
import sys
from email.message import Message

import package_path  # noqa: F401
from logs_conflicts import protocol as p

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


C = p.load_constants()
PORT = C["http"]["port"]
BASE = C["http"]["basePath"]


def headers(**values):
    message = Message()
    message["Host"] = values.pop("host", f"127.0.0.1:{PORT}")
    for name, value in values.items():
        for item in value if isinstance(value, list) else [value]:
            message[name.replace("_", "-").title()] = item
    return message


def test_guard():
    expect(p.trusted_request(headers(), PORT, C), "the game's request, no origin")
    expect(p.trusted_request(headers(origin="coui://uiresources"), PORT, C), "the game's origin")
    expect(p.trusted_request(headers(origin="null"), PORT, C), "the game's null origin")
    expect(not p.trusted_request(headers(origin="https://example.com"), PORT, C), "a web page refused")
    expect(not p.trusted_request(headers(origin="null", sec_fetch_site="cross-site"), PORT, C),
           "a sandboxed frame of another site refused")
    expect(not p.trusted_request(headers(host="evil.example:38792"), PORT, C), "a wrong Host refused")
    expect(not p.trusted_request(headers(origin=["null", "null"]), PORT, C), "a header twice refused")
    expect(not p.trusted_request(headers(origin="x" * 300), PORT, C), "a header too long refused")


def test_routes():
    expect(p.route_of(BASE + "hello", C) == ("hello", None), "hello")
    expect(p.route_of(BASE + "open-folder", C) == ("openFolder", None), "open-folder")
    expect(p.route_of(BASE + "log?rev=1234-5678", C) == ("log", "1234-5678"), "log with its revision")
    for bad in (BASE + "log?rev=../x", BASE + "hello?rev=1-2", BASE + "log?x=1", "/elsewhere/hello", BASE + "Log",
                BASE + "unknown", BASE + "hello/", BASE + "log?rev=" + "1" * 200, None):
        expect(p.route_of(bad, C) is None, f"refused path {bad!r}"[:60])


def event(**fields):
    return json.dumps({"marker": C["marker"], **fields}).encode()


def test_events():
    expect(p.parse_event(event(event="page_opened", host="pause"), C) == {"event": "page_opened", "host": "pause"},
           "event accepted")
    for raw, label in ((event(event="nope"), "unknown event"), (event(event="error", code="A B"), "bad code"),
                       (event(event="error", path="x"), "unknown field"), (b"{", "not JSON"),
                       (json.dumps({"event": "error"}).encode(), "no marker"),
                       (event(event="error", code="x" * 2000), "too long")):
        expect(p.parse_event(raw, C) is None, f"refused: {label}")
    expect(p.parse_event(event(event="timings", request=12.6, render=3), C) == {"event": "timings", "request": 13,
                                                                               "render": 3}, "timings rounded")
    for value in (-1, 10 ** 9, True, "5", float("nan")):
        expect(p.parse_event(event(event="timings", request=value), C) is None, f"timing refused: {value!r}")


def test_payload_and_budget():
    encoded = p.payload({"state": "ok", "text": "é"}, C)
    expect(encoded.isascii() and json.loads(encoded)["text"] == "é", "answers are ASCII JSON")
    try:
        p.payload({"text": "x" * 5000}, C)
        expect(False, "an answer over its bound is refused")
    except ValueError:
        pass
    budget = p.LogBudget(C)
    verdicts = [budget.admit("page_opened") for _ in range(C["http"]["maxEventLogs"] + 2)]
    expect(verdicts.count("log") == C["http"]["maxEventLogs"] - 1 and verdicts.count("last") == 1
           and verdicts[-1] == "skip", "each kind of line has its ceiling")
    failed = [budget.admit("copy_failed") for _ in range(C["http"]["maxFailedLogs"] + 1)]
    expect(failed.count("log") == C["http"]["maxFailedLogs"] - 1 and failed[-1] == "skip",
           "a repeated failure has a smaller ceiling")
    refused = [budget.admit("rejected") for _ in range(C["http"]["maxRejectedLogs"] + 1)]
    expect(refused.count("log") == C["http"]["maxRejectedLogs"] - 1 and refused[-1] == "skip",
           "refusals have their own ceiling")


for test in (test_guard, test_routes, test_events, test_payload_and_budget):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
