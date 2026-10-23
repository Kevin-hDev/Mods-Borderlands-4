"""Tests the companions' bars service (companions/bars_service.py, through the real bars_wire.py on a free loopback
port, with It Follows' own constants, assets/companion_bars.json; the trials' test, moved with it): nothing to
show yet, a refusal; the companions published, read back as JSON, names cut and parts kept from 0 to 1, each dead
or not, at most `most`, with whether the bars are shown and the hunter aimed at, its name cut too; another path
refused in its own words; an answer too long refused; the first request said once, from the game's thread; a port
held, said and refused; stopped, the port closed."""

import json
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows.companions import bars_service as service_module, bars_wire as wire  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


CONSTANTS = json.loads((HERE / "it_follows" / "assets" / "companion_bars.json").read_text(encoding="utf-8"))
said: list[str] = []
service = service_module.CompanionBars(wire, CONSTANTS, said.append)
check("started on a free port", service.start(0) is True and service.start(0) is True)
port = service.port()


def get(path: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2) as answer:
            return answer.status, answer.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


check("nothing published yet: refused with 503, our words", get(CONSTANTS["path"]) == (503,
      b'{"error":"request_failed"}'))
check("another path: 404, our words", get("/other") == (404, b'{"error":"request_failed"}'))
service.publish([("Crankus", 0.5, 1.0, False), ("Lemmy", 1.2, None, False),
                 ("Châssis vétuste", -1, float("nan"), True), (None, True, "1", 1), ("x" * 50, 0.12345, 0.0, False),
                 (" \n ", 1, 1, False)], True, "Vex")
status, body = get(CONSTANTS["path"])
answer = json.loads(body)
check("version 2: the bars' script and the aimed bar's read the same answer", CONSTANTS["version"] == 2)
check("published: 200, the version, an age, shown, the hunter aimed at, each companion", status == 200
      and answer["version"] == 2 and 0 <= answer["age"] < 1 and answer["shown"] is True and answer["aimed"] == "Vex"
      and answer["companions"][:2] == [{"name": "Crankus", "health": 0.5, "shield": 1.0, "dead": False},
                                       {"name": "Lemmy", "health": 1.0, "shield": None, "dead": False}])
check("a French name kept, a part below 0 kept at 0, no number unknown, dead only when True", answer["companions"][2]
      == {"name": "Châssis vétuste", "health": 0.0, "shield": None, "dead": True} and answer["companions"][3] == {
      "name": "?", "health": None, "shield": None, "dead": False})
check("a long name cut to nameMost, a part rounded", answer["companions"][4] == {
      "name": "x" * CONSTANTS["nameMost"], "health": 0.123, "shield": 0.0, "dead": False})
service.publish([], 1, "y" * 50)
other = json.loads(get(CONSTANTS["path"])[1])
check("shown only when True; the hunter aimed at cut to nameMost", other["shown"] is False
      and other["aimed"] == "y" * CONSTANTS["nameMost"])
service.publish([])
other = json.loads(get(CONSTANTS["path"])[1])
check("by default: shown, no one aimed at", other["shown"] is True and other["aimed"] is None)
check("a name of nothing printable: '?'", answer["companions"][5]["name"] == "?")
check("the game's no-break space and a tab shown as plain spaces, a control left out, any script kept", [
      service_module.name(text, 32) for text in ("Saumure type M", "a\tb", "a\x00b", "ブライン・タイプ M")]
      == ["Saumure type M", "a b", "ab", "ブライン・タイプ M"])
check("the first request, refused, said at the next publish from the game's thread, once", said == [
      service_module.HEARD] and get(CONSTANTS["path"])[0] == 200 and (service.publish([]), said)[1] == [
      service_module.HEARD])
service._note("a sentence")
service._note("a sentence")
service.publish([])
check("a sentence of the server's thread said once, however often", said.count("a sentence") == 1)
service.publish([(f"C{number}", 1, 1, False) for number in range(12)])
check("at most `most` companions", len(json.loads(get(CONSTANTS["path"])[1])["companions"]) == CONSTANTS["most"])
check("the requests on its path counted, refused ones too, not the others", service.asked == 6)
service._constants = dict(CONSTANTS, maxResponseBytes=40)
service.publish([("Crankus", 1, 1, False)])
check("an answer too long: refused, 503", get(CONSTANTS["path"])[0] == 503)
service._constants = CONSTANTS

held = service_module.CompanionBars(wire, CONSTANTS, said.append)
check("a port held: refused, said", held.start(port) is False and "could not open its port" in said[-1])
check("stopped: True", service.stop() is True and service.stop() is True)
probe = socket.socket()
probe.settimeout(1)
check("stopped: the port closed", probe.connect_ex(("127.0.0.1", port)) != 0)
probe.close()
try:
    service.port()
    asked = True
except RuntimeError:
    asked = False
check("stopped: no port to give", asked is False)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
