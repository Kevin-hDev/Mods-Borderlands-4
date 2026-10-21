"""The key that opens the window (open_key.py) and its MENU SHORTCUT card (panel_open_key.py), in the real window:
F7 at first, the card first on the COMMANDS page in three languages; another key chosen, saved and bound; NONE; a
camera command's key, now or by default, a profile's and a reserved key refused, the cancelling keys ignored; a camera
command or a profile refused the key; a camera command saved with the key before it keeps it; the key closes the
window, never while a key is chosen, a pop-up or a profile's window is open; the Escape watch reads the key given."""

from types import SimpleNamespace as NS

import panel_fixture as f
from third_person_fov import open_key as module, settings
from third_person_fov.control_escape import EscapeWatch

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Watch:
    """The closing watch, without reading the real keyboard: released when told, the busy it was given kept."""
    made: list = []

    def __init__(self, key):
        self.key, self.muted, self.let_go, self.busy = key, False, False, []
        Watch.made.append(self)

    def released(self, busy=False):
        self.busy.append(busy)
        return self.let_go and not busy


module.EscapeWatch = Watch
open_key = settings.open_key
root, widgets, form = f.build()
ROW = "open_window:keyboard"
selector = widgets[f"command:{ROW}"]


def shown():
    return widgets[f"value:{ROW}"].calls["SetText"][0]


def status():
    return widgets["commands_status"].calls["SetText"][0]


def choose(name):
    selector.SelectedKey = NS(Key=NS(KeyName=name))
    form.poll()
    form.poll()  # the next turn binds it


try:
    page = widgets["pages"].children[form.model.pages.index("commands")]
    order = [id(node) for node in f.walk(page)]
    check("the card is on the COMMANDS page, before the camera commands' cards",
          id(widgets["heading:command_open_window"]) in order
          and order.index(id(widgets["heading:command_open_window"]))
          < order.index(id(widgets["heading:command_third_person"])))
    f.click(form, widgets, "nav:commands")
    check("F7 at first, bound, shown on the card; the window's watch made for F7 and deaf until F7 is up",
          open_key.key() == "F7" and open_key.bind.key == "F7" and shown() == "F7"
          and Watch.made[-1].key == 0x76 and Watch.made[-1].muted)
    words = {}
    for language in ("FR", "ZH", "EN"):
        f.click(form, widgets, language)
        words[language] = (widgets["heading:command_open_window"].calls["SetText"][0],
                           widgets["group:command_open_window"].calls["SetText"][0])
    check("the card speaks the window's three languages", words == {
        "FR": ("RACCOURCI DU MENU", "Ouvre cette fenêtre en jeu, et la ferme."),
        "ZH": ("菜单快捷键", "在游戏中打开或关闭此窗口。"),
        "EN": ("MENU SHORTCUT", "Opens this window in game, and closes it.")})

    choose("K")
    check("another key chosen: saved, bound, shown, the field emptied, the watch made for it",
          open_key.option.value == "K" and open_key.bind.key == "K" and shown() == "K" and status() == "Saved."
          and str(selector.SelectedKey.Key.KeyName) == "None" and Watch.made[-1].key == ord("K"))
    choose("P")
    check("a camera command's key refused, the page saying why",
          open_key.option.value == "K" and form.command_form.notice == "open_key_command"
          and status() == "This key is already a camera command's: choose another one.")
    settings.commands.apply({"third_person_key": "J"})
    choose("P")
    check("a camera command's key by default refused too: its reset would give it back",
          open_key.option.value == "K" and form.command_form.notice == "open_key_command")
    settings.commands.apply({"third_person_key": "P"})
    choose("Tilde")
    check("the console's key refused", open_key.option.value == "K" and form.command_form.notice == "refused")
    form.command_form.notice = "ready"
    for name in ("Escape", "LeftMouseButton"):
        choose(name)
    check("Escape and a second click end the choice without choosing",
          open_key.option.value == "K" and form.command_form.notice == "ready")
    form.model._held_by_profile = lambda keys: setattr(form.model, "profile_holder", "Combat") or True
    choose("L")
    del form.model._held_by_profile
    check("a camera profile's key refused, the profile named",
          open_key.option.value == "K" and status().startswith("The profile “COMBAT” already has this key"))

    widgets[f"command:third_person:keyboard"].SelectedKey = NS(Key=NS(KeyName="K"))
    form.poll()
    check("a camera command refused the key that opens the window",
          settings.commands.option("third_person_key").value == "P"
          and status() == "This key opens this window (MENU SHORTCUT): choose another one.")
    form.profile_form.notice = None
    form.profile_form._set_key(NS(draft=NS(keyboard=None, controller=None)), "keyboard", "K")
    check("a camera profile refused it too", form.profile_form.notice == "key_command")
    settings.commands.apply({"orbit_key": "K"})
    check("a camera command saved with that key before keeps it, this one doing nothing",
          open_key.chosen() == "K" and open_key.key() is None)
    settings.commands.apply({"orbit_key": settings.commands.defaults()["orbit_key"]})

    widgets[f"clear:{ROW}"].SetIsChecked(True)
    form.poll()
    form.poll()
    check("NONE: no key, nothing bound, no watch, the card says NONE",
          open_key.option.value is None and open_key.key() is None and open_key.bind.key is None
          and open_key.closer() is None and shown() == "NONE")
    choose("F7")
    check("F7 chosen again", open_key.option.value == "F7" and open_key.bind.key == "F7")

    watch = Watch.made[-1]
    watch.let_go = True
    selector.selecting = True
    check("never closed while a key is being chosen", form.poll() is False and watch.busy[-1] is True)
    selector.selecting = False
    form.popup = next(name.split(":")[1] for name in widgets if name.startswith("popup:") and name.endswith(":beside"))
    form.poll()
    check("nor while a pop-up is open", watch.busy[-1] is True)
    form.popup = None
    form.profile_form.open = True
    form.poll()
    check("nor while a profile's window is open", watch.busy[-1] is True)
    form.profile_form.open = False
    check("let go otherwise: the window closes as with Close", form.poll() is True)
    watch.let_go = False

    option_value = open_key.option.value
    open_key.option.value = 42
    check("a value the file holds that is no key: F7", open_key.key() == "F7")
    open_key.option.value = option_value
    read = []
    EscapeWatch(api=NS(GetAsyncKeyState=lambda code: read.append(code) or 0), key=0x76)
    EscapeWatch(api=NS(GetAsyncKeyState=lambda code: read.append(code) or 0))
    check("the Escape watch reads the key it is given, Escape by default", read == [0x76, 0x1B])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")
    raise

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
