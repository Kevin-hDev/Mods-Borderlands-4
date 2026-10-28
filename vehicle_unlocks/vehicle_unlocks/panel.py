"""Shared page layout and click routing, using each owner's existing visual widgets."""
from . import config as cfg, service, text


def page(owner, key, widgets, template, _world, ui):
    p, w, tx, b, t = ui.p, ui.w, ui.tx, ui.b, ui.t
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    widgets['vehicles:hint'] = tx.text(rows, '', 'hint', wrap=True)
    w.column(rows, widgets['vehicles:hint'], padding=w.pad(t.SPACE_3, 0, t.SPACE_5))
    for action in cfg.ACTIONS:
        key = f'vehicles:{action}'
        w.column(rows, b.button(rows, widgets, key, 'action', template, 'secondary'),
                 padding=w.pad(t.SPACE_3, 0, t.SPACE_2), halign='Left')
        widgets[f'{key}:description'] = tx.text(rows, '', 'hint', wrap=True)
        w.column(rows, widgets[f'{key}:description'], padding=w.pad(t.SPACE_2, 0, t.SPACE_5))
    widgets['vehicles:result'] = tx.text(rows, '', 'hint', wrap=True)
    w.column(rows, widgets['vehicles:result'], padding=w.pad(t.SPACE_3, 0, t.SPACE_3))
    return scroll


def paint(form, widgets, ui):
    language = form.model.language
    for key in ('undo', 'restore'):
        container = widgets.get(f'{key}:container')
        if container is not None:
            shown = form.model.pages[form.page] != 'vehicles'
            container.SetVisibility(ui.w.enum('ESlateVisibility', 'Visible' if shown else 'Collapsed'))
    reason = service.available(form.model.mod)
    widgets['vehicles:hint'].SetText(text.get(f'vehicles:reason:{reason}' if reason else 'vehicles:hint', language))
    for action in cfg.ACTIONS:
        key = f'vehicles:{action}'
        widgets[f'{key}_label'].SetText(text.get(key, language))
        widgets[f'{key}:description'].SetText(text.get(f'{key}:description', language))
        widgets[key].SetIsEnabled(reason is None)
        ui.b.paint(widgets, key, 'secondary' if reason is None else 'disabled')
    result = getattr(form, 'vehicle_result', None)
    if result is None:
        message = ''
    else:
        key = f'vehicles:reason:{result.reason or "unreadable"}' if result.kind == 'refused' else f'vehicles:result:{result.kind}'
        message = text.get(key, language).format(changed=result.changed, skipped=result.skipped)
    widgets['vehicles:result'].SetText(message)


def poll(form, widgets, ui):
    clicked = tuple(action for action in cfg.ACTIONS if form.take(widgets[f'vehicles:{action}']))
    if form.model.pages[form.page] == 'vehicles':
        for name in ('undo', 'restore'):
            if name in widgets:
                form.take(widgets[name])  # These settings actions do not undo persistent game rewards.
    if not clicked or form.model.pages[form.page] != 'vehicles':
        return False  # Hidden-page latches must never survive into a later navigation.
    if form.flush(widgets):
        form.vehicle_result = service.run(clicked[0], form.model.mod)
        form.refresh_labels(widgets)
    return True
