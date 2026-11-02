# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the Logs & Conflicts page may send, and what the mod answers. Pure: no socket, no SDK. Rewritten from Mod
Settings' protocol.py (a mod never shares a file with another): the request guard proven in game by Mod Settings and
the HUD Editor, the event checks, the bounded answers and log lines."""

import json
import re
from pathlib import Path

# The one authority on the values of the page and of the mod; pak_recipe.py builds the page's copy from it.
CONSTANTS_NAME = "assets/logs_conflicts.constants.json"
CONSTANTS = Path(__file__).resolve().parent / CONSTANTS_NAME
VERSION = 1
ROUTE_NAME = re.compile(r"^[a-z-]{1,16}$")


def parse_constants(raw: bytes) -> dict:
    constants = json.loads(raw.decode("utf-8"))
    if constants.get("version") != VERSION:
        raise ValueError("Unknown constants version.")
    return constants


def load_constants(path: Path = CONSTANTS) -> dict:
    """Tests and tools, from the source folder. In game the file is inside the .sdkmod: __init__.py reads it with
    pkgutil, as our other mods read their assets."""
    return parse_constants(path.read_bytes())


def trusted_request(headers, port: int, constants: dict) -> bool:
    """Only the game's own UI on this machine: refuses DNS rebinding (Host), other origins, and any browser request
    made from another site. A browser names that site in Sec-Fetch-Site, even from a sandboxed frame whose Origin is
    "null" like the game's; the game's UI engine sends no Sec-Fetch-Site."""
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


def route_of(path: str, constants: dict):
    """(route key, revision or None), or None for any path not exactly expected. Only the log route takes a query,
    the revision the page already holds: rev=<size>-<modification time>."""
    http = constants["http"]
    if not isinstance(path, str) or len(path) > http["maxPathLength"] or not path.startswith(http["basePath"]):
        return None
    name, _, query = path[len(http["basePath"]):].partition("?")
    if not ROUTE_NAME.match(name):
        return None
    key = next((key for key, value in http["routes"].items() if value == name), None)
    if key is None:
        return None
    if not query:
        return key, None
    revision = query[len("rev="):] if query.startswith("rev=") else ""
    if key != "log" or not re.fullmatch(http["revisionPattern"], revision):
        return None
    return key, revision


def read_json(raw: bytes, constants: dict):
    if not raw or len(raw) > constants["http"]["maxRequestBytes"]:
        return None
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        return None
    return body if isinstance(body, dict) and body.get("marker") == constants["marker"] else None


def parse_event(raw: bytes, constants: dict):
    """A diagnostic event as a dict of short codes, or None for anything not exactly expected."""
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
    """Every kind of log line has a ceiling for the game's session: a repeated error or a page opened again and again
    would repeat its line. The log keeps the first ones and says once when it stops (OPTI.md, rule 22). A failure
    repeats the same line: it is written once (optimisation.md, section 9, rule 1). A failure's kind names its cause,
    from a few codes: a later failure of another cause still shows (second review)."""

    def __init__(self, constants: dict):
        http = constants["http"]
        self.default = http["maxEventLogs"]
        self.failed = http["maxFailedLogs"]
        self.limits = {"rejected": http["maxRejectedLogs"], "error": http["maxRejectedLogs"]}
        # Keys are the page's events (constants) and the kinds routes.py and server.py write: a finite set.
        self.counts = {}

    def admit(self, kind: str) -> str:
        """'log', 'last' (log, then say the budget is reached) or 'skip'."""
        count = self.counts.get(kind, 0) + 1
        self.counts[kind] = count
        limit = self.limits.get(kind, self.failed if "_failed" in kind else self.default)
        if count < limit:
            return "log"
        return "last" if count == limit else "skip"
