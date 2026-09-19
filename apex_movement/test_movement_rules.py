"""Checks Kevin's rule in the code itself: one mod is one movement, and every exception is written down.

Kevin, 2026-09-18: "un mods c'est un moovement". The rule was broken twice without anyone noticing — the ground
speeds rode on the auto sprint's switch, and the slides and the dash had no switch at all. Both were found by
accident. This test fails on its own the next time, so nobody has to notice.
"""

import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

import apex_movement  # noqa: E402, registers every movement with the frame loop
from apex_movement import frame, menu, movements  # noqa: E402

fails: list[str] = []
PACKAGE = HERE / "apex_movement"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def tree(module: str) -> ast.Module:
    """Parsed, not searched by hand: a comment mentioning settings.py is not a read (found the first time this ran)."""
    return ast.parse((PACKAGE / f"{module}.py").read_text(encoding="utf-8"))


def settings_read(module: str) -> set[str]:
    return {node.attr for node in ast.walk(tree(module))
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "settings"}


def package_imports(module: str) -> set[str]:
    """The sibling modules a module imports, whether by 'from . import x' or 'from .x import Name'."""
    found = set()
    for node in ast.walk(tree(module)):
        if not isinstance(node, ast.ImportFrom) or node.level != 1:
            continue
        found |= {node.module} if node.module else {alias.name for alias in node.names}
    return found


def switches_of(module_name: str) -> set[str] | None:
    """The identifiers of the switches a registered module runs behind, or None when it is not registered."""
    for name, switches, module in frame._movements:
        if module.__name__.rsplit(".", 1)[-1] == module_name:
            return {switch.identifier for switch in switches}
    return None


# 1. Every file of the package belongs somewhere: shared, or to exactly one movement.
on_disk = {path.stem for path in PACKAGE.glob("*.py")}
placed = [module for movement in movements.MOVEMENTS for module in movement.modules]
check("every module is either shared or in a movement",
      on_disk == set(movements.SHARED) | set(placed))
check("no module is claimed by two movements", len(placed) == len(set(placed)))
check("no movement claims a file that does not exist", set(placed) <= on_disk)

# 2. Every movement can be turned off on its own, or says in writing why it cannot.
for movement in movements.MOVEMENTS:
    registered = [switches_of(module) for module in movement.modules]
    running = [switches for switches in registered if switches is not None]
    check(f"{movement.name}: at least one of its modules runs in the frame loop", bool(running))
    shared_switch = set.intersection(*running) if running else set()
    if movement.always_on_because:
        check(f"{movement.name}: has no switch, and says why", not shared_switch)
    else:
        check(f"{movement.name}: one switch turns all of it off, or a reason is written",
              len(shared_switch) == 1)

# 3. A module never rides on a neighbour's switch: its switches belong to its own movement's menu lines.
def options_under(option) -> list:
    children = getattr(option, "children", None)
    if not children:
        return [option]
    return [found for child in children for found in options_under(child)]


for movement in movements.MOVEMENTS:
    own_groups = [group for group in menu.MENU if group.identifier in movement.menu_groups]
    own_settings = {option.identifier for group in own_groups for option in options_under(group)}
    for module in movement.modules:
        switches = switches_of(module)
        if switches is None:
            continue
        check(f"{module}: runs behind switches of its own movement only", switches <= own_settings)
    # And it never reads another movement's setting in its code either.
    for module in movement.modules:
        stray = settings_read(module) - own_settings - set(movements.SHARED_SETTINGS)
        check(f"{module}: reads no setting of another movement" + (f" (found {sorted(stray)})" if stray else ""),
              not stray)

# 4. A movement never imports another movement's module: it must be shippable without it.
for movement in movements.MOVEMENTS:
    for module in movement.modules:
        foreign = package_imports(module) - set(movements.SHARED) - set(movement.modules)
        check(f"{module}: imports no module of another movement" + (f" (found {sorted(foreign)})" if foreign else ""),
              not foreign)

# 5. Every menu line belongs to a movement, and a movement takes one line unless it says why not.
lined = [group for movement in movements.MOVEMENTS for group in movement.menu_groups]
check("every menu line belongs to a movement", {group.identifier for group in menu.MENU} == set(lined))
check("no menu line is claimed twice", len(lined) == len(set(lined)))
for movement in movements.MOVEMENTS:
    if len(movement.menu_groups) > 1:
        check(f"{movement.name}: takes more than one menu line, and says why", bool(movement.two_lines_because))

# 6. Two movements never write the same game value. Separate files can be installed side by side (Kevin, 2026-09-18),
# and each carries its own copy of ownership: two of them writing one field would each believe they own it, and the
# second to stop would put back what the first had already written.
# What this sees: the keys named by a *_KEY constant. It does not see keys built at run time (heavier_fall's jump
# fields, written by that movement alone today) nor the velocity, which the slide and the climb both write every
# frame they run but never keep or put back: they cannot run in the same frame, one on the ground, one in the air.
written_by: dict[str, str] = {}
for movement in movements.MOVEMENTS:
    for module in movement.modules:
        for node in ast.walk(tree(module)):
            if not (isinstance(node, ast.Assign) and isinstance(node.value, (ast.Constant, ast.JoinedStr))):
                continue
            for target in node.targets:
                if not (isinstance(target, ast.Name) and target.id.endswith("_KEY")):
                    continue
                key = node.value.value if isinstance(node.value, ast.Constant) else f"{module}:{target.id}"
                other = written_by.setdefault(key, movement.name)
                check(f"{movement.name}: no other movement writes {key}", other == movement.name)

# 7. Nothing outside a movement may be registered with a switch: a switch belongs to a movement, never to the shared
# modules, or turning it off would take part of every movement with it.
for name, switches, module in frame._movements:
    short = module.__name__.rsplit(".", 1)[-1]
    if short in movements.SHARED:
        check(f"{short}: shared, so it runs behind no switch", not switches)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
