"""Exercise the installed console menu's real dispatcher, including its extra Press page."""

import ast
from sdk_test_paths import console_menu_archive
import sys
from types import ModuleType, SimpleNamespace as NS
import zipfile

import control_fixture as f
from apex_grapple import control_console_menu, menu

sdk = console_menu_archive()
with zipfile.ZipFile(sdk) as archive:
    tree = ast.parse(archive.read("console_mod_menu/screens/mod.py").decode())
cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "OptionListScreen")
method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "handle_option_input")
pushed, opened = [], []
namespace = {"ButtonOption": type(f.control_menu.MENU), "NestedOption": type(f.control_menu.STORAGE),
             "push_screen": pushed.append, "ButtonOptionScreen": lambda mod, option: (mod, option),
             "logging": NS(dev_warning=lambda message: None)}
for name in ("BoolOption", "DropdownOption", "SpinnerOption", "SliderOption", "KeybindOption"):
    namespace[name] = type(name, (), {})
exec(compile(ast.Module(body=[method], type_ignores=[]), str(sdk), "exec"), namespace)


class ModScreen:
    handle_option_input = namespace["handle_option_input"]

    def __init__(self, mod):
        self.mod = mod
        self.drawn_options = [option for option in menu.MENU if not option.is_hidden]


screens = ModuleType("console_mod_menu.screens")
screens_mod = ModuleType("console_mod_menu.screens.mod")
screens_mod.ModScreen = ModScreen
sys.modules[screens.__name__] = screens
sys.modules[screens_mod.__name__] = screens_mod
sys.modules["console_mod_menu"].screens = screens
page = ModScreen(f.mod)
screens.screen_stack = [page]
f.control_menu.MENU.on_press = lambda button: opened.append(button)

# The real SDK adds a Press page before invoking ButtonOption.on_press.
assert page.handle_option_input("4") and len(pushed) == 1 and not opened
pushed.clear()
tuple(f.mod.iter_display_options())
assert page.handle_option_input("4") and opened == [f.control_menu.MENU] and not pushed
assert screens.screen_stack == [page]
handler = page.handle_option_input
tuple(f.mod.iter_display_options())
assert page.handle_option_input is handler
assert page.handle_option_input("5") and len(pushed) == 1  # Reset keeps its normal confirmation page.
assert not page.handle_option_input("unknown")

other = ModScreen(object())
screens.screen_stack = [other]
tuple(f.mod.iter_display_options())
assert other.handle_option_input.__func__ is ModScreen.handle_option_input
screens.screen_stack = []
tuple(f.mod.iter_display_options())
display = f.mod.iter_display_options
control_console_menu.install(f.mod, f.control_menu.MENU)
assert f.mod.iter_display_options is display
print("OK | real SDK dispatcher: direct open, same page, other buttons/mods unchanged, no duplicate adapters")
