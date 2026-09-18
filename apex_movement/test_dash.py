"""Tests the longer dash: only the full-speed part lengthened, from the game's timing, checked, put back on stop."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import dash, game, ownership, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9


def times(asset: object) -> list[float]:
    return [round(key.time, 6) for key in asset._keys]


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


player = sdk_stubs.FakeCharacter()
asset = sdk_stubs.dash_asset(state)
game_timing = dash.read(asset)
check("the game's timing is read from the duration and every curve point",
      near(game_timing.duration, 0.33) and game_timing.times == (0.0, 0.15, 0.17, 0.33))
check("the game's curve starts at full speed", dash.has_full_speed_start(asset))

longer = dash.lengthened(game_timing, 0.2)
check("lengthening moves the duration and every point after the first",
      near(longer.duration, 0.53) and [round(t, 6) for t in longer.times] == [0.0, 0.35, 0.37, 0.53])
check("so the drop and the pick-up after full speed keep their own length",
      near(longer.times[2] - longer.times[1], 0.02) and near(longer.times[3] - longer.times[2], 0.16))
check("a timing is close to itself and not to a longer one", dash.close(game_timing, game_timing) and not dash.close(game_timing, longer))

dash.update(player, 0)
extra = 1.0 * 508.0 / 2500.0
check("200 % by default adds full-speed time for the game's 508 once more", near(asset.Duration.constant, 0.33 + extra))
check("the curve points after full speed move by the same time", times(asset) == [0.0, round(0.15 + extra, 6),
      round(0.17 + extra, 6), round(0.33 + extra, 6)])
check("the curve's speeds and tangents are left as they are", [key.Value for key in asset._keys] == [1.0, 1.0, 0.181, 0.48]
      and [key.LeaveTangent for key in asset._keys] == [0.0, -2.0, 1.5, 0.0])
check("the game's timing is kept to put back", dash.close(ownership.original(dash.TIMING_KEY), game_timing))
check("the change is logged", notes("dash distance 200% lasting 533 ms (game 330 ms)") == 1)

written = asset._duration
dash.update(player, 1)
check("an unchanged setting writes and logs nothing", asset._duration is written and notes("dash distance") == 1)

asset.Duration = type(asset.Duration)(constant=0.33)
for key, time in zip(asset._keys, game_timing.times):
    key.time = time
dash.update(player, 1)
check("a dash the game put back to its own timing, same character, is lengthened again",
      near(asset.Duration.constant, 0.33 + extra) and near(asset._keys[1].time, 0.15 + extra))

settings.dash_distance.value = 300
dash.update(player, 2)
check("a new setting is computed from the game's timing, not the written one",
      near(asset.Duration.constant, 0.33 + 2.0 * 508.0 / 2500.0) and near(asset._keys[1].time, 0.15 + 2.0 * 508.0 / 2500.0))
settings.dash_distance.value = 100
dash.update(player, 3)
check("100 % gives the game's own timing", dash.close(dash.read(asset), game_timing))
settings.dash_distance.value = 200
dash.update(player, 4)

dash.stop(player)
check("stop puts the game's timing back", dash.close(dash.read(asset), game_timing) and not ownership.is_owned(dash.TIMING_KEY))
check("the restore is logged", notes("dash distance off, game dash restored") == 1)
dash.stop(player)
check("a stop with nothing written logs nothing", notes("dash distance off") == 1)

reshaped = sdk_stubs.FakeDashAsset()
reshaped._keys[1].Value = 0.9
state["objects"][("OakControlledMove", sdk_stubs.DASH_PATH)] = reshaped
game.forget()
dash.reset()
dash.update(player, 5)
check("a curve without a full-speed start is left alone and reported", reshaped.Duration.constant == 0.33
      and any("changed shape" in line for line in state["errors"]))
dash.update(player, 6)
check("and reported once", sum("changed shape" in line for line in state["errors"]) == 1
      and reshaped.Duration.constant == 0.33)

copying = sdk_stubs.FakeDashAsset(copy_keys=True)
state["objects"][("OakControlledMove", sdk_stubs.DASH_PATH)] = copying
game.forget()
dash.reset()
failed = False
try:
    dash.update(player, 7)
except RuntimeError:
    failed = True
check("a curve write that did not reach the game raises, so the movement is switched off", failed)
ownership.restore_all()
check("the duration written before the failure is put back", near(copying.Duration.constant, 0.33))

del state["objects"][("OakControlledMove", sdk_stubs.DASH_PATH)]
game.forget()
dash.reset()
errors = len(state["errors"])
dash.update(player, 8)
check("a dash asset not loaded yet is reported once and skipped", len(state["errors"]) == errors + 1)
dash.update(player, 9)
check("and not reported again", len(state["errors"]) == errors + 1)
state["objects"][("OakControlledMove", sdk_stubs.DASH_PATH)] = asset

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
