"""Tests the crouch dash: which press gets the game's limit back (Kevin: walking always, sprinting as chosen), the
crouch keys bound only while the sprint is asked open and following the game's list, the limit reopened every frame
when due, a press never blocked and an unreadable one said once."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import crouch_dash  # noqa: E402
from apex_camera_runtime.crouch_dash import LOWER_NS, CrouchDash, run_gap, wants_dash  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


# The rule.
check("a run to the right reads +90, a slow one nothing", round(run_gap(0.0, 600.0, 0.0)) == 90
      and run_gap(0.0, 50.0, 0.0) is None)
check("walking beyond the game's angle: the dash, whatever the choice",
      wants_dash(1, False, 90.0, True) and wants_dash(1, False, -170.0, False))
check("sprinting beyond it: the dash when chosen, the slide otherwise",
      wants_dash(1, True, 90.0, True) and not wants_dash(1, True, 90.0, False))
check("within the game's angle, in the air or standing: the game's own press",
      not wants_dash(1, False, 45.0, True) and not wants_dash(3, False, 90.0, True)
      and not wants_dash(1, False, None, True))


class Binding:
    def __init__(self, identifier: str, key: str, callback) -> None:
        self.identifier, self.key, self.callback, self.enabled = identifier, key, callback, True

    def disable(self) -> None:
        self.enabled = False


class Keeper:
    def __init__(self) -> None:
        self.lowered: list[tuple] = []
        self.reopened: list[int] = []
        self.accept = True

    def lower(self, now_ns: int, duration_ns: int) -> bool:
        self.lowered.append((now_ns, duration_ns))
        return self.accept

    def reopen_if_due(self, now_ns: int) -> None:
        self.reopened.append(now_ns)


def mapping(action: str, key: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(Action=types.SimpleNamespace(Name=action), Key=types.SimpleNamespace(KeyName=key))


bindings: list[Binding] = []
lines: list[str] = []
keeper = Keeper()
movement = types.SimpleNamespace(Velocity=types.SimpleNamespace(X=0.0, Y=621.0), bIsSprinting=False, MovementMode=1)
view = types.SimpleNamespace(Yaw=0.0)
character = types.SimpleNamespace(CharacterMovement=movement,
                                  Controller=types.SimpleNamespace(GetControlRotation=lambda: view))
mappings = [mapping("Action_CrouchOrDash", "Gamepad_FaceButton_Right"), mapping("Action_Crouch", "LeftControl"),
            mapping("Action_Fire", "LeftMouseButton")]
pc = types.SimpleNamespace(OakCharacter=character, PlayerInput=types.SimpleNamespace(EnhancedActionMappings=mappings))
players = [pc]
clock = [5_000]


def bind(identifier, key, callback) -> Binding:
    bindings.append(Binding(identifier, key, callback))
    return bindings[-1]


unit = CrouchDash(bind, keeper, lambda: players[0], lambda: clock[0], lines.append, "runtime:omni")
pressed, released = types.SimpleNamespace(name="IE_Pressed"), types.SimpleNamespace(name="IE_Released")

loading = types.SimpleNamespace()
unit.update(loading, True, True, 0)
check("a controller without its input list yet: nothing bound, nothing raised", bindings == [])
unit.next_keys_ns = 0
unit.update(pc, False, True, 1)
check("not asked open: nothing bound, the limit's reopening checked all the same", bindings == []
      and keeper.reopened == [0, 1])
unit.update(pc, True, True, 2)
check("asked open: the crouch keys only, under the unit's name, and said",
      [(b.identifier, b.key) for b in bindings] == [("runtime:omni:crouch:Gamepad_FaceButton_Right",
                                                     "Gamepad_FaceButton_Right"),
                                                    ("runtime:omni:crouch:LeftControl", "LeftControl")]
      and lines[-1] == "crouch keys Gamepad_FaceButton_Right LeftControl")
unit.update(pc, True, True, 3)
unit.update(pc, True, True, 2 + crouch_dash.KEYS_CHECK_NS)
check("the same keys read again: nothing bound twice", len(bindings) == 2 and keeper.reopened[-1] > 3)
mappings[1] = mapping("Action_Crouch", "C")
unit.update(pc, True, True, 3 + 2 * crouch_dash.KEYS_CHECK_NS)
check("a key changed by the player: the old ones let go, the new ones bound",
      not bindings[0].enabled and not bindings[1].enabled and [b.key for b in bindings[2:]] ==
      ["C", "Gamepad_FaceButton_Right"] and all(b.enabled for b in bindings[2:]))

press = bindings[-1].callback
check("a release does nothing", press(released) is None and keeper.lowered == [])
check("a press walking to the right: never blocked, the game's limit back for the dash",
      press(pressed) is None and keeper.lowered == [(5_000, LOWER_NS)]
      and lines[-1] == "crouch walking at +90: game sprint limit back for the dash")
movement.bIsSprinting = True
unit.update(pc, True, False, 4 + 2 * crouch_dash.KEYS_CHECK_NS)
press(pressed)
check("sprinting with the slide chosen: the limit stays open", len(keeper.lowered) == 1)
unit.update(pc, True, True, 5 + 2 * crouch_dash.KEYS_CHECK_NS)
press(pressed)
check("sprinting with the dash chosen: the limit back, said as sprinting",
      len(keeper.lowered) == 2 and lines[-1] == "crouch sprinting at +90: game sprint limit back for the dash")
keeper.accept = False
said = len(lines)
press(pressed)
check("a lowering refused (already lowered, no limit held): nothing said", len(lines) == said)
players[0] = None
press(pressed)
press(pressed)
check("an unreadable press is left to the game, said once",
      lines[-1] == "crouch press not read, left to the game: AttributeError" and len(lines) == said + 1)

unit.update(pc, False, True, 6 + 2 * crouch_dash.KEYS_CHECK_NS)
check("no longer asked open: every key let go", not any(b.enabled for b in bindings) and unit.bound == {})
unit.update(pc, True, True, 7 + 2 * crouch_dash.KEYS_CHECK_NS)
check("asked again: bound again at once", len(bindings) == 6 and bindings[-1].enabled)
mappings[:] = []
unit.update(pc, True, True, 8 + 3 * crouch_dash.KEYS_CHECK_NS)
check("no crouch key in the game's list: said", lines[-1].startswith("crouch keys none"))
mappings[:] = [mapping("Action_Crouch", "C")]
unit.update(pc, True, True, 9 + 4 * crouch_dash.KEYS_CHECK_NS)
unit.stop()
check("stopping lets every key go", not any(b.enabled for b in bindings) and unit.bound == {})

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
