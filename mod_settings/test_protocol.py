# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of protocol.py. python test_protocol.py"""

import json
import sys
from email.message import Message

import package_path  # noqa: F401  (before the package's modules)
import protocol as p

C = p.load_constants()
FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


def raw(**fields):
    return json.dumps({"marker": C["marker"], **fields}).encode()


def headers(**values):
    message = Message()
    for name, value in values.items():
        message[name] = value
    return message


# Origin and Host: the game's UI on this machine only
port = C["http"]["port"]
host = f"127.0.0.1:{port}"
check("game origin", p.trusted_request(headers(Host=host, Origin="coui://uiresources"), port, C))
check("null origin", p.trusted_request(headers(Host=host, Origin="null"), port, C))
check("no origin", p.trusted_request(headers(Host=host), port, C))
check("web origin refused", not p.trusted_request(headers(Host=host, Origin="http://evil.test"), port, C))
check("other host refused", not p.trusted_request(headers(Host="evil.test"), port, C))
twice = headers(Host=host)
twice["Host"] = host
check("doubled host refused", not p.trusted_request(twice, port, C))
check("long origin refused", not p.trusted_request(headers(Host=host, Origin="x" * 300), port, C))
# A web page's sandboxed frame also says Origin "null"; its browser names the other site (review, 26 October 2026).
check("null origin from another site refused",
      not p.trusted_request(headers(Host=host, Origin="null", **{"Sec-Fetch-Site": "cross-site"}), port, C))
check("a page's image or plain request from another site refused",
      not p.trusted_request(headers(Host=host, **{"Sec-Fetch-Site": "same-site"}), port, C))
check("a request typed by the user still passes",
      p.trusted_request(headers(Host=host, **{"Sec-Fetch-Site": "none"}), port, C))
doubled_site = headers(Host=host, **{"Sec-Fetch-Site": "none"})
doubled_site["Sec-Fetch-Site"] = "cross-site"
check("doubled Sec-Fetch-Site refused", not p.trusted_request(doubled_site, port, C))

# Ids: a mod, one of its rows, or its enabled row
check("mod id", p.is_id("m12", C))
check("row id", p.is_id("m3_145", C) and p.is_id("m3_on", C))
check("odd ids refused", not any(p.is_id(value, C) for value in ("m", "m123", "m3_", "m3_x", "M3", "m3_on_1", 3, None)))

# Changes: shape only; the value is checked against its row by the caller
check("value change", p.parse_change(raw(action="value", id="m0_3", revision=4, value=True), C) ==
      {"action": "value", "id": "m0_3", "revision": 4, "value": True})
check("cleared key passes as null", p.parse_change(raw(action="value", id="m0_6", revision=1, value=None), C)["value"]
      is None)
check("press", p.parse_change(raw(action="press", id="m0_7", revision=1), C) ==
      {"action": "press", "id": "m0_7", "revision": 1})
check("press with a value refused", p.parse_change(raw(action="press", id="m0_7", revision=1, value=1), C) is None)
check("value without value refused", p.parse_change(raw(action="value", id="m0_7", revision=1), C) is None)
check("no revision refused", p.parse_change(raw(action="value", id="m0_7", value=1), C) is None)
check("bool revision refused", p.parse_change(raw(action="value", id="m0_7", revision=True, value=1), C) is None)
check("negative revision refused", p.parse_change(raw(action="value", id="m0_7", revision=-1, value=1), C) is None)
check("bad id refused", p.parse_change(raw(action="value", id="../x", revision=1, value=1), C) is None)
check("unknown action refused", p.parse_change(raw(action="delete", id="m0_7", revision=1), C) is None)
check("extra field refused", p.parse_change(raw(action="press", id="m0_7", revision=1, x=1), C) is None)
check("too long refused", p.parse_change(b"x" * (C["http"]["maxRequestBytes"] + 1), C) is None)

# Diagnostic events: short codes only
check("diagnostic event", p.parse_event(raw(event="screen_opened", screen="mod", code="rows_12"), C) ==
      {"event": "screen_opened", "screen": "mod", "code": "rows_12"})
check("code with capitals refused", p.parse_event(raw(event="gamepad", name="Up"), C) is None)
check("unknown field refused", p.parse_event(raw(event="gamepad", other="x"), C) is None)
check("unknown event refused", p.parse_event(raw(event="bogus"), C) is None)
check("old change event refused", p.parse_event(raw(event="value_changed", ident="m0_1", value=1), C) is None)
check("wrong marker refused", p.parse_event(json.dumps({"marker": "x", "event": "gamepad"}).encode(), C) is None)
check("not json refused", p.parse_event(b"{oops", C) is None)

# Durations, all in one message
check("timings", p.parse_event(raw(event="timings", template=3.4, screen=0), C) ==
      {"event": "timings", "template": 3, "screen": 0})
check("unknown timing refused", p.parse_event(raw(event="timings", other=3), C) is None)
check("negative timing refused", p.parse_event(raw(event="timings", shown=-1), C) is None)
check("huge timing refused", p.parse_event(raw(event="timings", shown=C["http"]["maxTimingMs"] + 1), C) is None)
check("empty timings refused", p.parse_event(raw(event="timings"), C) is None)
# An int too big for a float made math.isfinite raise: no answer and a whole stack in the log (review).
check("int too big for a float refused, no error", p.parse_event(raw(event="timings", shown=10 ** 400), C) is None)

# Capture requests
check("capture start", p.parse_capture(raw(action="start", id="m0_6", revision=3), C) == ("start", "m0_6", 3))
check("capture start without its revision refused", p.parse_capture(raw(action="start", id="m0_6"), C) is None)
check("capture start with a bool revision refused",
      p.parse_capture(raw(action="start", id="m0_6", revision=True), C) is None)
check("capture cancel", p.parse_capture(raw(action="cancel"), C) == ("cancel", None, None))
check("capture with a bad id refused", p.parse_capture(raw(action="start", id="sample_key", revision=1), C) is None)
check("capture with extra field refused", p.parse_capture(raw(action="cancel", id="m0_6"), C) is None)
check("unknown capture action refused", p.parse_capture(raw(action="stop"), C) is None)

# Answers stay within their bound
answer = json.loads(p.payload({"state": "idle"}, C))
check("answer carries marker and version", answer["marker"] == C["marker"] and answer["version"] == p.VERSION)
try:
    p.payload({"text": "x" * C["http"]["maxResponseBytes"]}, C)
    check("oversized answer refused", False)
except ValueError:
    check("oversized answer refused", True)
check("a model has its own bound", len(p.payload({"text": "x" * 5000}, C, C["http"]["maxModelBytes"])) > 5000)

# Log budget
budget = p.LogBudget(dict(C, http=dict(C["http"], maxChangeLogs=2, maxEventLogs=3)))
check("budget logs then stops", [budget.admit("change") for _ in range(4)] == ["log", "last", "skip", "skip"])
check("every other event has the default ceiling",
      [budget.admit("timings") for _ in range(4)] == ["log", "log", "last", "skip"])
check("each event counted on its own", budget.admit("page_opened") == "log")
check("log line", p.log_line({"event": "gamepad", "name": "up"}, C) == "[ModSettings] event=gamepad name=up")

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
