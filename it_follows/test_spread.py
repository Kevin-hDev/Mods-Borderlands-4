"""Tests the spread of the distances (decision 66): over each round of the shares' total each offset comes as often as
its share, Kevin's example at every level, interleaved rather than in runs; one share alone always gives its offset."""

import collections
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import levels, spread  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    kevin = spread.Spread(levels.SPREAD)
    first = [kevin.next() for _ in range(10)]
    check("Kevin's example over ten: six at the distance, two 10 m farther, one 15 m farther, one 5 m nearer",
          collections.Counter(first) == {0.0: 6, 10.0: 2, 15.0: 1, -5.0: 1})
    check("interleaved: never three at the same distance in a row, the farther ones apart",
          all(len({first[index], first[index + 1], first[index + 2]}) > 1 for index in range(8))
          and first == [0.0, 10.0, 0.0, 0.0, 15.0, 0.0, -5.0, 0.0, 10.0, 0.0])
    many = [kevin.next() for _ in range(1000)]
    check("and so over each ten that follows", collections.Counter(many) == {0.0: 600, 10.0: 200, 15.0: 100,
                                                                            -5.0: 100}
          and many[:10] == first)
    alone = spread.Spread(((100, 0.0),))
    check("one share alone: always its offset", [alone.next() for _ in range(5)] == [0.0] * 5)
except Exception as error:
    check(f"exception {type(error).__name__}: {error}", False)

print(f"RESULTAT: {'TOUS LES TESTS PASSENT' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
