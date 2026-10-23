# Generated: the window Kevin's mods share, taken from Hunter Change's plain window, under Companions'
# names. Its comments may speak of other mods. Never edited by hand: docs/renforts/outils/menu_window.py
# writes this file.
"""One bounded compensation policy for every generated settings window."""

from .control_window_config import (
    ROLLBACK_ATTEMPTS, ROLLBACK_TIMEOUT_NS, TRANSACTION_TIMEOUT_NS, TRANSACTION_TOTAL_TIMEOUT_NS,
)

SAVE_FAILURE = "Settings save failed; restoration pending."
RESTORE_FAILURE = "Settings could not be restored. Please retry."
MAX_SETTINGS_BYTES = 1_048_576
