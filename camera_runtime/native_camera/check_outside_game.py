"""Exercise the real native preflight boundary without SDK/game access."""

import ctypes
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2 or len(sys.argv[1]) > 32768:
        print("RESULTAT: ECHEC (invalid library argument)")
        return 1
    candidate = Path(sys.argv[1])
    if ".." in candidate.parts or not candidate.is_absolute() or candidate.suffix != ".dll":
        print("RESULTAT: ECHEC (invalid library argument)")
        return 1
    stage = "load"
    try:
        library = ctypes.CDLL(str(candidate))
        stage = "preparation"
        if library.ads_prepare() == 0:
            raise RuntimeError("Preparation unexpectedly accepted")
        stage = "verification"
        with ThreadPoolExecutor(max_workers=2) as workers:
            outcomes = tuple(workers.map(lambda _: library.ads_verify_files(), range(4)))
        stage = "preparation_recheck"
        if not all(outcome != 0 for outcome in outcomes) or library.ads_prepare() == 0:
            raise RuntimeError("Preflight unexpectedly accepted")
    except Exception as error:
        kind = type(error).__name__
        if not kind.isascii() or not kind.isidentifier() or len(kind) > 80:
            kind = "Exception"
        print(f"RESULTAT: ECHEC (outside-game native boundary stage={stage} error_type={kind})")
        return 1
    print("RESULTAT: OK (DLL loaded outside game; worker preflight and preparation refused)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
