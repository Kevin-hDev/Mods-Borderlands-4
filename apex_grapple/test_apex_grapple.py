"""Tests the mod itself: how it is built, what switching it on and off does, and a fresh install switching itself on."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
# No settings file yet, as on a fresh install: mods_base only switches on a mod whose file says so,
# so the mod switches itself on the first time and would otherwise sit there doing nothing.
state["settings_exists"] = False

import apex_grapple  # noqa: E402
from apex_grapple import frame, keys, menu  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


mod = apex_grapple.mod
check("the mod is built and registered", state["mods"] == [mod])
check("it carries the name players see", mod.name == "Apex Grapple")
check("it shows the menu", mod.kwargs["options"] is menu.MENU)
check("it holds the frame hook, and only that one", mod.kwargs["hooks"] == [frame.tick])
check("a fresh install switches itself on", mod.is_enabled)
check("its hook is live", frame.tick.enabled)
check("and it says which version is running", any(f"enabled, version {apex_grapple.__version__}" in line
                                                  for line in state["misc"]))
check("it writes the settings actually in use, the file having won over the defaults",
      any("settings in use" in line and "pull_strength" in line for line in state["misc"]))
check("the version reads as three numbers, so the log and the archives can be told apart",
      len(apex_grapple.__version__.split(".")) == 3
      and all(part.isdigit() for part in apex_grapple.__version__.split(".")))

player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
state["kismet"].hit = (1000.0, "StaticMeshActor")
frame.on_frame(player.anim, 1_000_000_000)
frame.rope.fire(player, 1_000_000_000)
check("a rope can be running when the player switches the mod off", frame.rope.busy and keys.is_bound())

mod.disable()
check("switching off takes the keys back", not keys.is_bound())
check("and lets the rope go", not frame.rope.busy)
check("and says so", any("disabled" in line for line in state["misc"]))
check("the hook is down", not frame.tick.enabled)

mod.enable()
check("switching back on works", mod.is_enabled and frame.tick.enabled)
mod.disable()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
