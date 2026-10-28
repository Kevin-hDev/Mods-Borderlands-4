"""Icon presentation only: the existing native selectors still capture and save keys."""

from . import game, input_list, panel_glyphs as glyphs, panel_i18n as i18n, panel_widgets as w, report


def visibility(widget, state):
    widget.SetVisibility(w.enum("ESlateVisibility", state))


class Display:
    def __init__(self):
        self.catalogue = glyphs.Catalogue()
        self.previous = {}  # Exactly two draft slots; no engine resources cached here.
        self.images_failed = False

    def image_failure(self):
        # A rejected optional image must not cancel capture or undo an already saved binding.
        self.images_failed = True
        report.error_once("panel:icon_render", "Controller images unavailable; using button names.")

    def slot(self, form, widgets, name, key, show, brush):
        selector = widgets[name]
        # The sized wrapper preserves height when the native label is collapsed.
        selector.SetTextBlockVisibility(w.enum("ESlateVisibility", "Collapsed" if show else "Visible"))
        image, label = widgets[f"{name}:icon"], widgets[f"{name}:key_label"]
        if brush is not None:
            image.SetBrush(brush)
        elif show:
            label.SetText(glyphs.label(key, form.model.controller_icons, form.model.language))
        visibility(image, "HitTestInvisible" if brush is not None else "Collapsed")
        visibility(label, "HitTestInvisible" if show and brush is None else "Collapsed")

    def update(self, form, widgets):
        for name in ("first", "second"):
            selector = widgets[name]
            key = str(selector.SelectedKey.Key.KeyName)
            selecting = selector.GetIsSelectingKey()
            state = (key, selecting, form.model.controller_icons, form.model.language, form.two, self.images_failed)
            if self.previous.get(name) == state:
                continue
            show = key.startswith("Gamepad_") and not selecting and (name == "first" or form.two)
            try:
                brush = self.catalogue.brush(form.model.controller_icons, key) if show and not self.images_failed else None
                self.slot(form, widgets, name, key, show, brush)
            except Exception:
                self.image_failure()
                self.slot(form, widgets, name, key, show, None)
                self.summary(form, widgets)
            self.previous[name] = state

    def summary(self, form, widgets):
        from .panel_controls import summary
        text = summary(form.bindings, form.model.language)
        widgets["current"].SetText(text)
        visibility(widgets["pad_summary"], "Collapsed")
        if self.images_failed:
            return
        try:
            self.summary_images(form, widgets, text)
        except Exception:
            self.image_failure()
            # Leave the full text intact even if the second image failed after the first.
            visibility(widgets["pad_summary"], "Collapsed")
            widgets["current"].SetText(text)

    def summary_images(self, form, widgets, text):
        try:
            device = next(d for d in form.bindings.config.DEVICES if d.name == "gamepad")
            selected = device.selection()
            keys = selected or tuple(sorted(key for key in input_list.grapple_keys(game.input_mappings())
                                           if form.bindings.config.device_of(key) == device.name))
            if not 1 <= len(keys) <= 2:
                return  # Keep all names visible if the game defines more alternatives.
            brushes = [self.catalogue.brush(form.model.controller_icons, key) for key in keys]
            if any(brush is None for brush in brushes):
                return
        except Exception:
            report.error_once("panel:icon_summary", "Controller icons unavailable for current controls.")
            return  # The ordinary summary already reports invalid/unavailable controls.
        widgets["pad_label"].SetText(i18n.text("gamepad", form.model.language) + " :")
        for name, brush in zip(("pad_first", "pad_second"), brushes):
            widgets[name].SetBrush(brush)
            visibility(widgets[name], "HitTestInvisible")
        second = "HitTestInvisible" if len(keys) == 2 else "Collapsed"
        visibility(widgets["pad_second_box"], second)
        visibility(widgets["pad_separator"], second)
        widgets["pad_separator"].SetText("+" if selected else "/")
        visibility(widgets["pad_summary"], "HitTestInvisible")
        # Replace only the controller line; the keyboard and heading stay exactly where they were.
        widgets["current"].SetText(text.rsplit("\n", 1)[0])
