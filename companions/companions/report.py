"""Companions' lines in the SDK log: the journal of the characters' package (characters/report.py, decision 69 of
docs/renforts), named Companions. Its modules and its window's generated ones import report from Companions' package,
as every window of ours does; this module puts the shared journal in its own place in sys.modules, so that they all
write through the one module: one run number, one set of the window's errors written once.
"""

import sys

from .characters import report

report.named("Companions")
sys.modules[__name__] = report
