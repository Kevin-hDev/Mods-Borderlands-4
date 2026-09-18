"""Tests the frame loop: player only, switches, a failing movement isolated, level change, stop."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import frame, game, ownership  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Movement:
    def __init__(self, broken: bool = False) -> None:
        self.updates, self.stops, self.resets, self.broken = 0, 0, 0, broken

    def update(self, character: object, now_ns: int) -> None:
        if self.broken:
            raise ValueError("boom")
        self.updates += 1

    def stop(self, character: object) -> None:
        self.stops += 1

    def reset(self) -> None:
        self.resets += 1


S = 1_000_000_000
player = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, player)
good, bad, always, both = Movement(), Movement(broken=True), Movement(), Movement()
good_switch, bad_switch = types.SimpleNamespace(value=True), types.SimpleNamespace(value=True)
# A module of a movement that also has an option of its own runs behind both (2026-09-18).
own_switch = types.SimpleNamespace(value=True)
frame.register("good", good, good_switch)
frame.register("bad", bad, bad_switch)
frame.register("always", always)
frame.register("both", both, good_switch, own_switch)

frame.on_frame(player.anim, S)
check("a switched-on movement runs on the player's frame", good.updates == 1)
check("a movement without a switch runs", always.updates == 1)
check("a failing movement is reported once", len(state["errors"]) == 1 and "bad switched off" in state["errors"][0])
check("a failing movement is stopped", bad.stops == 1)
frame.on_frame(player.anim, S + 1)
check("the other movements keep running", good.updates == 2)
check("a failed movement stays off", len(state["errors"]) == 1 and bad.stops == 1)

frame.on_frame(object(), S + 2)
check("another character's frame runs nothing", good.updates == 2)

good_switch.value = False
frame.on_frame(player.anim, S + 3)
check("a switch turned off stops its movement once", good.stops == 1 and good.updates == 2)
frame.on_frame(player.anim, S + 4)
check("a stopped movement is not stopped again", good.stops == 1)
check("a movement behind two switches stops when the first goes off", both.stops == 1)
good_switch.value = True

frame.on_frame(player.anim, S + 5)
check("it runs again once both switches are on", both.updates == 3)
own_switch.value = False
frame.on_frame(player.anim, S + 6)
check("its own option turns it off without touching the movement it belongs to",
      both.stops == 2 and good.updates == 4)
own_switch.value = True

ownership.write("floor", ownership.CHARACTER, lambda: 0.0, lambda value: None, 672.0)
other = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, other)
frame.on_frame(other.anim, 3 * S)
# The first look at the player also counts as a change, hence two resets.
check("a level change resets every movement", good.resets == 2 and bad.resets == 2)
check("a level change forgets the old character's values", not ownership.is_owned("floor"))
check("the new character's frame runs the movements", good.updates == 5)

asset = types.SimpleNamespace(constant=720.0)
ownership.write("slide", ownership.ASSET, lambda: asset.constant, lambda value: setattr(asset, "constant", value), 850.0)
failures = frame.stop_all()
check("stop_all stops the running movements", good.stops == 2 and always.stops == 1)
check("stop_all puts the game's values back", asset.constant == 720.0 and failures == [])
check("stop_all forgets the player", game.character() is None)

frame.on_frame(other.anim, 3 * S + 1)
check("after stop_all a failed movement gets another chance", bad.stops == 2)

# A switch turned off while there is no character — at the main menu, between two games — must still stop its
# movement once a character is back: what a movement writes outlives the character (review, 2026-09-18).
sdk_stubs.use_character(state, None)
frame.on_frame(other.anim, 5 * S)
stops = good.stops
good_switch.value = False
third = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, third)
frame.on_frame(third.anim, 6 * S)
check("a switch turned off with no character stops its movement once one is back", good.stops == stops + 1)
good_switch.value = True
frame.on_frame(third.anim, 6 * S + 1)

sdk_stubs.use_character(state, None)
frame.on_frame(third.anim, 7 * S)
stops = good.stops
frame.stop_all()
check("disabling the mod with no character still stops what was running", good.stops == stops + 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
