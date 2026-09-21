"""Read console shortcuts only at a completed UI choice, without retaining engine objects."""

MAX_CONSOLE_KEYS = 16


def console_keys():
    import unrealsdk
    from . import input_list

    configured = unrealsdk.find_class("InputSettings").ClassDefaultObject.ConsoleKeys
    if len(configured) > MAX_CONSOLE_KEYS:
        raise ValueError("Too many console shortcuts")
    found = set()
    for entry in configured:
        name = str(entry.KeyName)
        # Native ConsoleKeys includes literal layout characters (² on Kevin's keyboard).
        # Preserve them as reserved keys without relaxing assignable key/action names.
        character = len(name) == 1 and name.isprintable() and not name.isspace()
        if not 0 < len(name) <= input_list.MAX_NAME_LENGTH:
            raise ValueError("Invalid console shortcut")
        if not character and not input_list.NAME_PATTERN.fullmatch(name):
            raise ValueError("Invalid console shortcut")
        found.add(name)
    return frozenset(found)
