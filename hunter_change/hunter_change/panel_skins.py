"""The body and head rows of the APPEARANCE page, under the hunter cards (sketch C1, Kevin, 2026-10-07): for the look
worn, a row for its body and a row for its head, each with a button per skin, the one worn in gold. A click wears that
skin at once (wardrobe.wear_skin).

Only the skins the player owns have a button (skins.py). The rows show only on another hunter's look and when more
than the game's own skin is owned: on the own look the game's customisation chooses, and a row of one button would
change nothing (the menus' rule of 2026-09-21, working or invisible).
"""

from typing import Any

from . import hunters, panel_buttons as b, panel_i18n as i18n, panel_pages as p, panel_text as tx
from . import panel_theme as t, panel_widgets as w

# Each row: the part it chooses, and the name of its widgets and texts.
ROWS = ((hunters.BODY, "body"), (hunters.HEAD, "head"))
VISIBLE, COLLAPSED = "Visible", "Collapsed"


def _button(key: str, skin: str) -> str:
    return f"skin:{key}:{skin}"


def _show(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", VISIBLE if shown else COLLAPSED))


def rows(owner: Any, widgets: dict, template: Any) -> Any:
    """The two rows, laid out as a setting's, added to `owner` and kept as `skins`."""
    block = w.new("VerticalBox", owner)
    for _, key in ROWS:
        widgets[f"label:skin_{key}"] = tx.text(block, "", "label", wrap=True)
        choice = w.new("HorizontalBox", block)
        for skin in hunters.SKINS:
            name = _button(key, skin)
            widgets[f"{name}_box"] = b.button(choice, widgets, name, "switch", template, "off")
            w.row(choice, widgets[f"{name}_box"], padding=w.pad(0, t.SPACE_3, 0, 0), valign="Center")
        p._row(block, widgets[f"label:skin_{key}"], choice)
        widgets[f"description:skin_{key}"] = tx.text(block, "", "hint", wrap=True)
        w.column(block, widgets[f"description:skin_{key}"], padding=w.pad(t.SPACE_2, 0, t.SPACE_3))
    w.column(owner, block)
    widgets["skins"] = block
    return block


def taken(take: Any, widgets: dict) -> tuple[str, str] | None:
    """The part and skin of the first button clicked since the last poll, if any; every other one clicked meanwhile
    is dropped, as the cards' are."""
    clicked = [(part, skin) for part, key in ROWS for skin in hunters.SKINS if take(widgets[_button(key, skin)])]
    return clicked[0] if clicked else None


def paint(widgets: dict, status: Any, language: str) -> None:
    """The rows for `status` (wardrobe.Status), hidden outside a game, on the own look or with one skin owned."""
    shown = status is not None and status.worn.hunter != status.played and len(status.owned) > 1
    _show(widgets["skins"], shown)
    if not shown:
        return
    worn = status.worn
    for part, key in ROWS:
        widgets[f"label:skin_{key}"].SetText(i18n.text(f"skin_{key}", language))
        widgets[f"description:skin_{key}"].SetText(i18n.text(f"skin_{key}_hint", language).format(
            worn=worn.hunter.name))
        current = worn.body if part == hunters.BODY else worn.head
        for skin in hunters.SKINS:
            name = _button(key, skin)
            _show(widgets[f"{name}_box"], skin in status.owned)
            widgets[f"{name}_label"].SetText(i18n.text(f"skin:{skin}", language))
            b.paint(widgets, name, "on" if skin == current else "off")
