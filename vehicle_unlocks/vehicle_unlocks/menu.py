"""The same SDK page declaration for both independent owner mods."""
from .text import EN


def option(nested_option):
    return nested_option('vehicles_menu', [], display_name=EN['vehicles'], description=EN['vehicles:description'])
