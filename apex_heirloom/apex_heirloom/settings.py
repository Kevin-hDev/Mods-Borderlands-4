"""Every setting the window shows, in its pages' order: the heirloom's, then the holster's. Each part keeps its own in
heirloom_settings.py and holster_settings.py; the window's model, Restore and Undo read them all from here.

A separate file has its own part's settings only (pack.py): the other part never runs there, and a setting it cannot
use would be listed, saved and reset for nothing.
"""

from . import heirloom_settings, holster_settings, pack

ALL = (*(heirloom_settings.ALL if pack.runs(heirloom_settings.heirloom.identifier) else ()),
       *(holster_settings.ALL if pack.runs(holster_settings.holster.identifier) else ()))
