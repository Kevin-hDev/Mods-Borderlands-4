"""The game's rope in the player's colour, with the classic look (docs/apex_grapple/pistolet-grappin/decisions.md,
14 October): its two colours, by the names the effect lists (docs/apex_grapple/spec-apex-grapple.md, both the game's
blue), written through the effect's own SetVariableLinearColor, which it offers (verified in game on 2026-09-21). The
game's own blue leaves the effect untouched. A refusal costs the colour alone, never the rope.
"""

from typing import Any

import unrealsdk

from . import look_assets, look_settings, report

NAMES = ("User.Color", "User.BeamColor")


def paint(component: Any) -> None:
    chosen = look_settings.game_rope_colour.value
    if chosen == look_assets.GAME_COLOUR_AT_FIRST:
        return
    red, green, blue = look_assets.COLOURS[chosen]
    colour = unrealsdk.make_struct("LinearColor", R=red, G=green, B=blue, A=1.0)
    for name in NAMES:
        try:
            component.SetVariableLinearColor(name, colour)
        except Exception as exc:
            report.error_once(f"beam:colour:{name}", f"the grapple beam would not take its colour {name}: {exc!r}")
