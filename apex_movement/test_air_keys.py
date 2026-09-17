"""Tests the air crouch decisions: ground passes, air blocks, tap asks a dash, hold stays held, crouch then jump slams."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import air_keys  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


MS = 1_000_000
pad = "Gamepad_FaceButton_Right"

check("a crouch on the ground passes", not air_keys.crouch_event(pad, "IE_Pressed", 0, False))
check("a crouch pressed on the ground counts as held, for a slide jump's landing", air_keys.is_held())
check("its repeats in the air still pass", not air_keys.crouch_event(pad, "IE_Repeat", 30 * MS, True))
check("its release passes too", not air_keys.crouch_event(pad, "IE_Released", 50 * MS, False))
check("and ends the hold", not air_keys.is_held())
air_keys.crouch_event(pad, "IE_Pressed", 60 * MS, False)
check("released in the air, it passes and ends the hold", not air_keys.crouch_event(pad, "IE_Released", 70 * MS, True)
      and not air_keys.is_held())
check("a ground press and a short hold are not logged", state["misc"] == [])
air_keys.crouch_event(pad, "IE_Pressed", 100 * MS, False)
air_keys.crouch_event(pad, "IE_Released", 700 * MS, True)
check("a hold released after 500 ms or more is logged, where it was released",
      state["misc"] == ["[Apex Movement] crouch released key=Gamepad_FaceButton_Right after_ms=600 in_air=True"])
state["misc"].clear()

check("a crouch in the air is blocked", air_keys.crouch_event(pad, "IE_Pressed", 1000 * MS, True))
check("the blocked press is logged", any("air crouch blocked" in line for line in state["misc"]))
check("a blocked crouch counts as held", air_keys.is_held())
check("its repeats are blocked", air_keys.crouch_event(pad, "IE_Repeat", 1050 * MS, True))
check("a release after 120 ms in the air is blocked", air_keys.crouch_event(pad, "IE_Released", 1120 * MS, True))
check("that tap asks for a dash", air_keys.due_requests(1120 * MS) == ["dash"])
check("a request is handed out once", air_keys.due_requests(1200 * MS) == [])
check("nothing is held after the release", not air_keys.is_held())

air_keys.crouch_event(pad, "IE_Pressed", 2000 * MS, True)
air_keys.crouch_event(pad, "IE_Released", 2300 * MS, True)
check("a release after 300 ms asks for nothing", air_keys.due_requests(2300 * MS) == [])

air_keys.crouch_event(pad, "IE_Pressed", 3000 * MS, True)
check("a press held into the landing stays held", air_keys.is_held())
check("its release on the ground is still blocked", air_keys.crouch_event(pad, "IE_Released", 3100 * MS, False))
check("a short blocked hold is not logged at release", not any("crouch released" in line for line in state["misc"]))
check("a quick release on the ground asks no dash", air_keys.due_requests(3100 * MS) == [])

air_keys.jump_event("IE_Pressed", 4000 * MS)
check("a crouch 50 ms after a jump passes, the game slams itself", not air_keys.crouch_event(pad, "IE_Pressed", 4050 * MS, True))
check("that pass is logged", any("jump 50 ms before" in line for line in state["misc"]))
check("the slam's crouch does not count as held, so a slam does not slide at landing", not air_keys.is_held())
check("its release passes too", not air_keys.crouch_event(pad, "IE_Released", 4100 * MS, True))
check("a crouch 150 ms after a jump is blocked", air_keys.crouch_event(pad, "IE_Pressed", 4150 * MS, True))
air_keys.crouch_event(pad, "IE_Released", 4400 * MS, True)
air_keys.due_requests(4400 * MS)

air_keys.crouch_event(pad, "IE_Pressed", 5000 * MS, True)
air_keys.jump_event("IE_Released", 5010 * MS)
check("a jump release changes nothing", air_keys.is_held())
air_keys.jump_event("IE_Pressed", 5030 * MS)
check("a jump right after a blocked crouch is a combination, not a hold", not air_keys.is_held())
check("the slam is not due before 200 ms", air_keys.due_requests(5100 * MS) == [])
check("the slam is due 200 ms after the jump", air_keys.due_requests(5230 * MS) == ["slam"])
check("the combination is logged", any("jump 30 ms later: slam asked" in line for line in state["misc"]))
air_keys.crouch_event(pad, "IE_Released", 5100 * MS, True)
check("releasing a combination quickly asks no dash", air_keys.due_requests(5300 * MS) == [])

air_keys.crouch_event(pad, "IE_Pressed", 6000 * MS, True)
air_keys.jump_event("IE_Pressed", 6200 * MS)
check("a jump long after a blocked crouch leaves it held", air_keys.is_held())
check("and asks no slam", air_keys.due_requests(6500 * MS) == [])
air_keys.crouch_event(pad, "IE_Released", 6300 * MS, True)

for index in range(air_keys.MAX_REQUESTS + 5):
    air_keys.crouch_event(pad, "IE_Pressed", (7000 + index) * MS, True)
    air_keys.crouch_event(pad, "IE_Released", (7000 + index) * MS + 1, True)
check("requests are bounded", len(air_keys.due_requests(8000 * MS)) == air_keys.MAX_REQUESTS)

air_keys.crouch_event(pad, "IE_Pressed", 9000 * MS, True)
air_keys.jump_event("IE_Pressed", 9500 * MS)
air_keys.crouch_event("LeftControl", "IE_Pressed", 9400 * MS, False)
air_keys.reset()
check("reset forgets held presses, ground ones too", not air_keys.is_held())
check("reset forgets the last jump", air_keys.crouch_event(pad, "IE_Pressed", 9520 * MS, True))
air_keys.reset()
check("a release after reset passes to the game", not air_keys.crouch_event(pad, "IE_Released", 9600 * MS, True))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
