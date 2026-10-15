# Generated: the window Kevin's mods share, taken from Hunter Change's plain window, under It Follows'
# names. Its comments may speak of other mods. Never edited by hand: docs/RUN/outils/menu_window.py
# writes this file.
"""One timing authority for settings transactions and deferred window closure."""
TRANSACTION_TIMEOUT_NS = 2_000_000_000
ROLLBACK_ATTEMPTS = 3
ROLLBACK_TIMEOUT_NS = TRANSACTION_TIMEOUT_NS * 6
TRANSACTION_TOTAL_TIMEOUT_NS = TRANSACTION_TIMEOUT_NS + ROLLBACK_TIMEOUT_NS
