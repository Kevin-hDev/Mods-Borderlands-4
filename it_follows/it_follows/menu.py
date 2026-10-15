"""It Follows' window: its pages HORDE MODE (the RUN page of decisions 53 to 63, renamed by decision 80), NORMAL MODE,
HISTORY and OPTIONS. HORDE MODE holds a run's settings, NORMAL MODE the normal mode's, OPTIONS the bar's; HISTORY holds
no setting, its page is the last runs (panel_history.py). The window draws each page through panel_follows.py. The
Horde's page keeps its identifier, run_menu, so that the window's last page and its drawing stay as they were."""

from mods_base import NestedOption

from . import options
from .normal import options as normal_options

run = NestedOption("run_menu", options.RUN, display_name="Horde mode", description="")
normal = NestedOption("normal_menu", normal_options.PAGE, display_name="Normal mode", description="")
history = NestedOption("history_menu", [], display_name="History", description="")
display = NestedOption("options_menu", options.DISPLAY, display_name="Options", description="")
ALL = MENU = [run, normal, history, display]
# Ten choices would not hold on one line as buttons: the row shows two arrows around the one chosen (panel_choices.py).
ARROWS = ("max_enemies",)
