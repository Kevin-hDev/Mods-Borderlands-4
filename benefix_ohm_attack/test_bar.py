"""Tests the mod's side of the energy bar: the service starts and stops with the mod, each frame tells it the
energy and the element, and a bar that fails never takes the beam down. Always on a port of its own."""

import http.client
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import attack, bar, energy_service, keys, reserve, settings  # noqa: E402

fails: list[str] = []
PRESSED, RELEASED = "EInputEvent.IE_Pressed", "EInputEvent.IE_Released"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def ask(port: int):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", energy_service.CONSTANTS["path"])
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def answers(port: int) -> bool:
    try:
        ask(port)
        return True
    except OSError:
        return False


mod = state["mods"][0]
check("the bar's script and the service share one file of constants, shipped with the mod's other files",
      (HERE / "benefix_ohm_attack" / "assets" / "bar.constants.json").is_file() and bar.PORT is None
      and energy_service.CONSTANTS["port"] == 38751)

sdk_stubs.player(state, level=1)
attack.on_frame(0.0)
check("before the mod is switched on, a frame tells nothing and fails nothing", state["errors"] == [])

# Port 0: the system picks a free one, so the test never takes the port Kevin's game uses.
bar.PORT = 0
mod.on_enable()
port = bar._service.port()
check("switching the mod on starts the service, and the log says where it answers",
      state["log"][-1].endswith(f"energy bar: the service answers on port {port}") and ask(port)[0] == 503)

attack.energy.left = 100.0
attack.on_frame(1.0)
answer = json.loads(ask(port)[1])
check("a frame tells the energy, its maximum and the element of the menu",
      answer["energy"] == 100.0 and answer["max"] == reserve.MAXIMUM and answer["element"] == "Fire")

keys.keyboard_bind.callback(PRESSED)
attack.on_frame(1.1)
attack.on_frame(1.2)
answer = json.loads(ask(port)[1])
check("while the beam fires, the energy told is the one left, and the maximum does not move",
      0.0 < answer["energy"] < 100.0 and abs(answer["energy"] - attack.energy.left) < 0.01
      and answer["max"] == reserve.MAXIMUM)
keys.keyboard_bind.callback(RELEASED)

settings.element.value = "Cryo"
attack.on_frame(1.3)
check("the element told follows the menu", json.loads(ask(port)[1])["element"] == "Cryo")
settings.element.value = "Plasma"
attack.on_frame(1.31)
check("a saved element the menu no longer offers is told as the default one, like the beam fired",
      json.loads(ask(port)[1])["element"] == "Fire")
settings.element.value = "Fire"

settings.show_bar.value = False
attack.on_frame(1.32)
check("the bar's switch off: the screen is told nothing, so the bar's script hides the bar", ask(port)[0] == 503)
attack.on_frame(1.34)
check("... at every frame", ask(port)[0] == 503 and state["errors"] == [])
settings.show_bar.value = True
attack.on_frame(1.36)
check("the switch on again: the energy is told again", json.loads(ask(port)[1])["element"] == "Fire")

state["trace"] = None
attack.energy.left = 42.0
keys.keyboard_bind.callback(PRESSED)
attack.on_frame(1.4)
check("a frame that fails still tells the energy",
      json.loads(ask(port)[1])["energy"] == 42.0 and len(state["errors"]) == 1)
sdk_stubs.aim_at(state, "Char_Psycho_7")

mod.on_enable()
check("switching on twice leaves one service, on a port that answers",
      answers(bar._service.port()) and (bar._service.port() == port or not answers(port)))
port = bar._service.port()

mod.on_disable()
check("switching the mod off stops the service", bar._service is None and not answers(port))
errors = len(state["errors"])
attack.on_frame(2.0)
check("and a frame after that fails nothing", len(state["errors"]) == errors)
bar.stop()
check("stopping twice is fine", len(state["errors"]) == errors)

taken = energy_service.EnergyService(lambda sentence: None)
taken.start(port=0)
bar.PORT = taken.port()
mod.on_enable()
check("a port already taken: the bar stays hidden, said, and the mod is on all the same",
      bar._service is None and any("stays hidden" in line for line in state["log"][-2:]))
attack.energy.left = 100.0
spawns = len(state["spawns"])
attack.on_frame(2.95)
keys.keyboard_bind.callback(PRESSED)
attack.on_frame(3.0)
check("and the beam still fires", len(state["spawns"]) == spawns + 1)
keys.keyboard_bind.callback(RELEASED)
attack.on_frame(3.1)
mod.on_disable()
taken.stop()


def unusable(report):
    raise RuntimeError("no network in this game")


real_service, energy_service.EnergyService = energy_service.EnergyService, unusable
errors = len(state["errors"])
bar.PORT = 0
mod.on_enable()
check("a service that cannot even be made: the bar stays hidden, said as an error, and the mod is on all the same",
      bar._service is None and len(state["errors"]) == errors + 1 and "stays hidden" in state["errors"][-1])
mod.on_disable()
energy_service.EnergyService = real_service


class Broken:
    def publish(self, *values):
        raise RuntimeError("no socket")

    def clear(self):
        raise RuntimeError("no socket")

    def stop(self):
        raise RuntimeError("no socket")


bar._service = Broken()
errors = len(state["errors"])
attack.on_frame(4.0)
attack.on_frame(4.1)
check("a service that fails while told: said once, the frame goes on", len(state["errors"]) == errors + 1)
settings.show_bar.value = False
attack.on_frame(4.2)
attack.on_frame(4.3)
check("a service that fails while the bar is hidden: said once, the frame goes on", len(state["errors"]) == errors + 2)
settings.show_bar.value = True
bar.stop()
check("a service that fails while stopped: said, and let go", len(state["errors"]) == errors + 3 and bar._service is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
