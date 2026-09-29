"""Tests AES-256 against the standard: the test vector of FIPS-197, appendix C.3, both ways; a key of another size
and a text that is not whole blocks are refused."""

import sys

import sdk_stubs

sdk_stubs.install()

from hunter_change import save_aes as aes  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def refused(action) -> bool:
    try:
        action()
    except ValueError:
        return True
    return False


KEY = aes.expand_key(bytes(range(32)))
PLAIN = bytes.fromhex("00112233445566778899aabbccddeeff")
CIPHER = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")
check("the vector of FIPS-197, encrypted", aes.aes_ecb(PLAIN, KEY, decrypt=False) == CIPHER)
check("the vector of FIPS-197, decrypted", aes.aes_ecb(CIPHER, KEY, decrypt=True) == PLAIN)
check("two blocks are two independent blocks",
      aes.aes_ecb(PLAIN * 2, KEY, decrypt=False) == CIPHER * 2)
check("a key of another size is refused", refused(lambda: aes.expand_key(bytes(16))))
check("a text that is not whole blocks is refused", refused(lambda: aes.aes_ecb(PLAIN[:-1], KEY, decrypt=False)))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
