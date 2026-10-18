"""Tests a run's settings: Kevin's choices and their defaults, Buff and Buff+ with their two factors and a help without
figures; no row for the killed coming back, who always come back; the RUN page's rows and the OPTIONS page's; the
starting point off at first, the place chosen kept with no row, read only when the row is on, a place not kept read as
Kevin's first; the
settings read as they stand, each choice with its value, the bar in the window's language; a value that is no choice
read as its default; a language the mod does not have read as English; a time limit's choice found again from its
seconds."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import options, texts  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    check("five levels, 40 at first", options.level.choices == ["25", "40", "60", "80", "100"]
          and options.level.value == "40")
    check("speeds from Normal to +50 % by 10 %, Normal at first", options.speed.choices
          == ["Normal", "+10%", "+20%", "+30%", "+40%", "+50%"] and options.speed.value == "Normal")
    check("time limits of 10 to 60 minutes or none, none at first", options.duration.choices
          == ["10 min", "20 min", "30 min", "45 min", "60 min", "Unlimited"] and options.duration.value == "Unlimited")
    check("Normal, Buff and Buff+, Normal at first", options.buff.choices == ["Normal", "Buff", "Buff+"]
          and options.buff.value == "Normal")
    check("decision 79: Buff, enemies' health x1.2 and damage taken x1.1; Buff+, x1.4 and x1.2",
          options.BUFFS == {"Normal": (1.0, 1.0), "Buff": (1.2, 1.1), "Buff+": (1.4, 1.2)})
    check("the Buff's help names no figure (Kevin: only the names BUFF and BUFF+)",
          not any(character.isdigit() for character in options.buff.description))
    check("no row for the killed coming back: a Horde run always brings them back (decision 80)",
          not hasattr(options, "respawn"))
    check("the bar shown at first, in three sizes, medium at first", options.bar.value is True
          and options.bar_size.choices == ["Small", "Medium", "Large"] and options.bar_size.value == "Medium")
    check("the RUN page's rows, Starting point first (decision 138), then the OPTIONS page's; no button, no language "
          "of its own (decision 62)",
          options.RUN == [options.start_point, options.level, options.speed, options.buff, options.duration,
                          options.crowd, options.far]
          and options.DISPLAY == [options.bar, options.bar_size]
          and options.ALL == [*options.RUN, options.start_place, *options.DISPLAY]
          and not hasattr(options, "language") and not hasattr(options, "start_button"))
    check("Starting point off at first, Kevin's first place chosen, kept with no row of its own",
          options.start_point.value is False and options.start_place.value == "3" and options.start_place.is_hidden
          and options.read().start_place is None)
    options.start_point.value = True
    check("on, the run starts from the place chosen", options.read().start_place == 3)
    options.start_place.value = "11"
    check("another place chosen", options.read().start_place == 11)
    options.start_place.value = "10"
    check("a place Kevin did not keep reads as his first", options.read().start_place == 3)
    options.start_point.value = "yes"
    check("on only when the file says so as a switch", options.read().start_place is None)
    options.start_point.value, options.start_place.value = False, "11"
    check("off, the place chosen kept", options.read().start_place is None and options.start_place.value == "11")
    options.start_place.value = "3"
    check("decision 96: the most enemies from 30 to 120 by 10, 120 at first", options.crowd.choices
          == ["30", "40", "50", "60", "70", "80", "90", "100", "110", "120"] and options.crowd.value == "120"
          and options.read().crowd_max == 120)
    check("decision 97: the far enemies managed at first", options.far.value is True and options.read().manage_far)
    options.crowd.value, options.far.value = "50", False
    check("each gives its value, but the far enemies always managed (decision 99)",
          (options.read().crowd_max, options.read().manage_far) == (50, True))
    options.shelve()
    check("decision 99: the shelved row back at its default, whatever the file held",
          options.SHELVED == (options.far,) and options.far.value is True)
    options.crowd.value, options.far.value = "125", "no"
    check("a value that is no choice reads as its default", (options.read().crowd_max, options.read().manage_far)
          == (120, True))
    options.crowd.value, options.far.value = "120", True
    check("the defaults read as they stand, in English, the killed coming back", options.read()
          == options.Settings(40, 1.0, None, True, texts.ENGLISH, True, 19.0, 1.0, 1.0))
    options.level.value, options.speed.value, options.duration.value = "100", "+30%", "45 min"
    options.buff.value = "Buff+"
    options.bar.value, options.bar_size.value = False, "Large"
    check("each choice gives its value, the bar in the window's language", options.read(texts.FRENCH)
          == options.Settings(100, 1.3, 2700.0, True, texts.FRENCH, False, 24.0, 1.4, 1.2))
    options.buff.value = "Buff"
    check("Buff gives its two factors", (options.read().health, options.read().taken) == (1.2, 1.1))
    options.buff.value = "Mega"
    options.level.value, options.speed.value, options.duration.value = "120", "fast", "forever"
    options.bar_size.value = "Huge"
    check("a value that is no choice reads as its default, a language the mod has not as English",
          options.read("Klingon") == options.Settings(40, 1.0, None, True, texts.ENGLISH, False, 19.0, 1.0, 1.0))
    options.level.value = "abc"
    check("a level that is no number reads as the default", options.read().level == 40)
    check("a time limit's choice from its seconds, Unlimited for none or one it has not",
          options.duration_name(2700.0) == "45 min" and options.duration_name(None) == "Unlimited"
          and options.duration_name(42.0) == "Unlimited")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
