# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the Mod Settings page may send, and what the mod answers. Pure: no socket, no SDK.
Everything the page sends is checked here for its shape; a change's value is then checked against its row
(catalog.clean_change), once, before it leaves the service's thread."""

import json
import re
from pathlib import Path

# The one authority on the values of the page and of the mod; pak_recipe.py builds the page's copy from it.
CONSTANTS_NAME = "assets/mod_settings.constants.json"
CONSTANTS = Path(__file__).resolve().parent / CONSTANTS_NAME
VERSION = 1
CHANGE_ACTIONS = ("value", "press")


def parse_constants(raw: bytes) -> dict:
    constants = json.loads(raw.decode("utf-8"))
    if constants.get("version") != VERSION:
        raise ValueError("Unknown constants version.")
    return constants


def load_constants(path: Path = CONSTANTS) -> dict:
    """Tests and tools, from the source folder. In game the file is inside the .sdkmod: __init__.py reads it
    with pkgutil, as our other mods read their assets."""
    return parse_constants(path.read_bytes())


def trusted_request(headers, port: int, constants: dict) -> bool:
    """Only the game's own UI on this machine: refuses DNS rebinding (Host), other origins, and any browser request
    made from another site. A browser names that site in Sec-Fetch-Site, even from a sandboxed frame whose Origin is
    "null" like the game's; the game's UI engine sends no Sec-Fetch-Site (HUD Editor's guard, proven in game)."""
    http = constants["http"]
    for name in ("Host", "Origin", "Sec-Fetch-Site"):
        values = headers.get_all(name) or []
        if len(values) > 1 or any(len(value) > http["maxHeaderLength"] for value in values):
            return False
    if headers.get("Host") != f"{http['host']}:{port}":
        return False
    site = headers.get("Sec-Fetch-Site")
    if site is not None and site not in http["fetchSites"]:
        return False
    origin = headers.get("Origin")
    return origin is None or origin in http["nativeOrigins"]


def read_json(raw: bytes, constants: dict):
    if not raw or len(raw) > constants["http"]["maxRequestBytes"]:
        return None
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        return None
    return body if isinstance(body, dict) and body.get("marker") == constants["marker"] else None


def is_id(value, constants: dict) -> bool:
    return isinstance(value, str) and re.fullmatch(constants["catalog"]["idPattern"], value) is not None


def parse_event(raw: bytes, constants: dict):
    """A diagnostic event as a dict, or None for anything not exactly expected."""
    body = read_json(raw, constants)
    if body is None or body.get("event") not in constants["events"]:
        return None
    if body["event"] == "timings":
        return parse_timings(body, constants)
    clean = {"event": body["event"]}
    for key, value in body.items():
        if key in ("marker", "event"):
            continue
        if key not in constants["eventFields"] or not isinstance(value, str) \
                or not re.fullmatch(constants["codePattern"], value):
            return None
        clean[key] = value
    return clean


def parse_timings(body: dict, constants: dict):
    clean = {"event": "timings"}
    for key, value in body.items():
        if key in ("marker", "event"):
            continue
        # The bounds first: they refuse NaN and infinities too, and math.isfinite raises on an int too big for a float.
        if key not in constants["timingNames"] or isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not 0 <= value <= constants["http"]["maxTimingMs"]:
            return None
        clean[key] = round(value)
    return clean if len(clean) > 1 else None


def parse_change(raw: bytes, constants: dict):
    """{'action', 'id', 'revision', 'value'?} with its shape checked, or None. The value is checked against its row
    by the caller, which holds the rows."""
    body = read_json(raw, constants)
    if body is None or body.get("action") not in CHANGE_ACTIONS:
        return None
    expected = {"marker", "action", "id", "revision"} | ({"value"} if body["action"] == "value" else set())
    revision = body.get("revision")
    if set(body) != expected or not is_id(body.get("id"), constants) or not is_revision(revision):
        return None
    clean = {"action": body["action"], "id": body["id"], "revision": revision}
    if body["action"] == "value":
        clean["value"] = body["value"]
    return clean


def is_revision(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def parse_capture(raw: bytes, constants: dict):
    """('start', id, revision) or ('cancel', None, None), or None. Whether the id is a writable key row of that
    revision is the caller's to check."""
    body = read_json(raw, constants)
    if body is None:
        return None
    if body.get("action") == "cancel" and set(body) == {"marker", "action"}:
        return "cancel", None, None
    if body.get("action") == "start" and set(body) == {"marker", "action", "id", "revision"} \
            and is_id(body["id"], constants) and is_revision(body["revision"]):
        return "start", body["id"], body["revision"]
    return None


def payload(body: dict, constants: dict, limit: int = None) -> bytes:
    encoded = json.dumps({"marker": constants["marker"], "version": constants["version"], **body},
                         separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if len(encoded) > (constants["http"]["maxResponseBytes"] if limit is None else limit):
        raise ValueError("Response exceeds its bound.")
    return encoded


def log_line(event: dict, constants: dict) -> str:
    fields = " ".join(f"{key}={value}" for key, value in event.items())
    return f"{constants['logPrefix']} {fields}"


class LogBudget:
    """Every kind of log line has a ceiling for the game's session: dragging a slider sends many values, a repeated
    error would repeat its line. The log keeps the first ones and says once when it stops (OPTI.md, rule 22)."""

    def __init__(self, constants: dict):
        http = constants["http"]
        self.default = http["maxEventLogs"]
        self.limits = {"change": http["maxChangeLogs"], "sound": http["maxSoundLogs"],
                       "js_input": http["maxInputLogs"], "gamepad": http["maxValueLogs"],
                       "input_action": http["maxInputLogs"],
                       # A tab switch builds that tab's rows: one line each, as many as the player switches.
                       "screen_opened": http["maxValueLogs"], "tab": http["maxValueLogs"],
                       "rebuild": http["maxValueLogs"], "rejected": http["maxRejectedLogs"],
                       "error": http["maxRejectedLogs"]}
        # Keys come from the events of the constants and the names above: a finite set.
        self.counts = {}

    def admit(self, event_name: str) -> str:
        """'log', 'last' (log, then say the budget is reached) or 'skip'."""
        count = self.counts.get(event_name, 0) + 1
        self.counts[event_name] = count
        limit = self.limits.get(event_name, self.default)
        if count < limit:
            return "log"
        return "last" if count == limit else "skip"
