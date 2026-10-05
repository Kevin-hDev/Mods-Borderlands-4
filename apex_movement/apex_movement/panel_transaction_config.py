"""One bounded compensation policy for every generated settings window."""

from .control_window_config import (
    ROLLBACK_ATTEMPTS, ROLLBACK_TIMEOUT_NS, TRANSACTION_TIMEOUT_NS, TRANSACTION_TOTAL_TIMEOUT_NS,
)

NATIVE_FAILURE = "Camera settings update refused; restoration pending."
SAVE_FAILURE = "Settings save failed; restoration pending."
RESTORE_FAILURE = "Settings could not be restored. Please retry."
MAX_SETTINGS_BYTES = 1_048_576
