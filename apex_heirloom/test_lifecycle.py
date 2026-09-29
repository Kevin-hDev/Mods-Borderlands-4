"""Tests the heirloom's life in the mod: its frame watch, enabled at a fresh install and left as saved otherwise; on,
the knife goes on the player's hands at their first frame, once, never on another character's, and again on a new
character's; the menu's mode given at once; off, by the mod's switch or the heirloom's own, it leaves with our
animations and comes back when on again; a knife that cannot be put in the hand is tried again every few seconds,
given up after a few tries, said, and tried again on a new character or when switched on."""

import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import heirloom_stubs  # noqa: E402

state = heirloom_stubs.install()
import fake_world  # noqa: E402

world = fake_world.World(state)
state["settings_exists"] = False
import apex_heirloom  # noqa: E402
from apex_heirloom import heirloom, heirloom_settings, lifecycle  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def arms_frame(instance) -> None:
    """A frame of these arms, as the mod's own hook gets it, while the mod is on."""
    if lifecycle.arms_frame.enabled:
        lifecycle.arms_frame.fn(instance, None, None, None)


def said_times(text: str) -> int:
    return sum(text in line for line in state["info"])


mod = state["mods"][-1]
check("the mod watches the arms' frames for the knife", lifecycle.arms_frame in mod.kwargs["hooks"])
check("a fresh install, without a settings file, is switched on, and no knife comes before the arms' first frame",
      mod.is_enabled and not world.meshes)
arms_frame(world.instance)
check("at the arms' first frame the knife goes in the player's hand", len(world.meshes) == 1
      and heirloom.holds_for(world.character) and world.meshes[0].shown is True)
arms_frame(world.instance)
check("and only once", len(world.meshes) == 1)
# Another character with arms of its own, which the game lists beside the player's.
_stranger, _arms, stranger_arms = world.new_character()
state["all"]["/Script/Engine.AnimInstance"] = [world.instance, stranger_arms]
arms_frame(stranger_arms)
check("another character's arms get none", len(world.meshes) == 1)

heirloom_settings.mode.value = "Borderlands"
check("the menu's mode is given to empty hands at once, while on",
      world.unarmed.AnimSets == [world.game_list, world.borderlands_list])
heirloom_settings.mode.value = "Apex"

mod.disable()
check("off: our list taken back, the knife still in the hand, the watch of new hands stopped",
      world.unarmed.AnimSets == [world.game_list] and not world.meshes[0].destroyed
      and not lifecycle.arms_frame.enabled)
world.rest[0] = "Unarmed"
world.frame()
check("the game's animations back, the knife leaves", world.meshes[0].destroyed and heirloom.held() is None)
world.rest[0] = "HeirApx"
arms_frame(world.instance)
check("while off, no knife comes back", len(world.meshes) == 1)
mod.enable()
arms_frame(world.instance)
check("on again, it comes back at the next frame", len(world.meshes) == 2 and heirloom.holds_for(world.character))

heirloom_settings.heirloom.value = False
check("the heirloom's own switch off, the mod on: our list taken back, the knife still in the hand",
      world.unarmed.AnimSets == [world.game_list] and not world.meshes[1].destroyed)
world.rest[0] = "Unarmed"
world.frame()
world.rest[0] = "HeirApx"
arms_frame(world.instance)
check("the game's animations back, the knife leaves and none comes back",
      world.meshes[1].destroyed and len(world.meshes) == 2)
heirloom_settings.heirloom.value = True
arms_frame(world.instance)
check("its switch on again, it comes back at the next frame", len(world.meshes) == 3
      and heirloom.holds_for(world.character))

old = world.meshes[-1]
world.character, world.arms, world.instance = world.new_character()
state["pc"].OakCharacter = world.character
arms_frame(world.instance)
check("a new character after a death or a new map: the knife goes on its hands, the old one leaves",
      len(world.meshes) == 4 and old.destroyed and heirloom.holds_for(world.character))

heirloom.remove()
state["info"].clear()
world.loaded.clear()
heirloom_stubs.sdk_stubs.asset_registry(state, lambda _data: (_ for _ in ()).throw(RuntimeError("no such package")))
missing = "our jakobs_knife animations are not in the game"
lifecycle.keep(world.character, 100.0)
lifecycle.keep(world.character, 100.0 + lifecycle.RETRY_S / 2)
check("a knife that cannot be put in the hand is not tried again at once", said_times(missing) == 1)
for number in range(1, lifecycle.MAX_TRIES + 3):
    lifecycle.keep(world.character, 100.0 + number * lifecycle.RETRY_S)
check("it is tried again every few seconds, then given up, said once",
      said_times(missing) == lifecycle.MAX_TRIES and said_times("no knife after") == 1)
world.character, world.arms, world.instance = world.new_character()
state["pc"].OakCharacter = world.character
lifecycle.keep(world.character, 1000.0)
check("tried again on a new character", said_times(missing) == lifecycle.MAX_TRIES + 1)
mod.disable()
mod.enable()
lifecycle.keep(world.character, 1000.0)
check("and when switched on again", said_times(missing) == lifecycle.MAX_TRIES + 2)

state["settings_exists"] = True
heirloom_stubs.fresh_package()
import apex_heirloom as again  # noqa: E402

check("with a settings file, the mod is left as saved", not again.mod.is_enabled)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
