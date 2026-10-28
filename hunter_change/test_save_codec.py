"""Tests the save codec without the game: a save in the game's own layout opens; a save made by the bl4 tool from an
invented text and an invented Steam ID opens to that text; a text is closed in the game's own layout; a text closed then
opened comes back the same; a wrong Steam ID, a damaged checksum, a damaged compressed text, an uneven padding, a
padding longer than a block, a file that is not whole blocks and an oversized file are refused, never opened as garbage.
A save's start is its text's first bytes, whole when shorter, reading only the chunks needed; the start of another
account's save, of garbage, of a truncated first block, of a zlib stream the game never writes or of a save cut before
its text's end is refused.

No real save nor real Steam ID here: 76561190000000001 is below the first Steam account number (76561197960265728)."""

import sys
import zlib

import sdk_stubs

sdk_stubs.install()

from hunter_change import save_codec as codec  # noqa: E402

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


INVENTED_ID = 76561190000000001
TEXT = (b"state:\n  class: Char_ExoSoldier\n  char_name: Rafa\n  char_guid: 0123456789ABCDEF0123456789ABCDEF\n"
        b"gbxactorparts:\n  character: gap,Cosmetics_Colorization_Primary[Color_01]\n")
# Made on 2026-09-28 by: bl4 save -s 76561190000000001 synth.sav encrypt synth.yaml (bl4 0.8.5), synth.yaml being TEXT.
BL4_SAVE = bytes.fromhex(
    "73b5b73e978c9c43a1bbcf4ff163445f995bc767b32ae87e63dd2aec2f6c7c5dcc6d885e3b08196d994c28ceb6949022f4fc7f78e5610dd4e5"
    "d4513e40b4c1534310092aee7afc9710b66ff25a079c532c1eb4896c8967ad17e9fd2e64fb6fd8d4ec214f06202e15c0f1230ee908100b27ae"
    "dcf8e18a44e36bdd1f2c08d75a8d46a378deef418c2eac25e902068c55003f77f1b5c655fdc33f240a829fea38b6")
key = codec.steam_key(INVENTED_ID)


def sealed(packed: bytes) -> bytes:
    pad = 16 - len(packed) % 16
    return codec.aes_ecb(packed + bytes([pad]) * pad, key, decrypt=False)


# The game's own layout, read in Kevin's seven saves on 2026-09-28: the zlib stream, then the text's length.
GAME_LAYOUT = zlib.compress(TEXT) + len(TEXT).to_bytes(4, "little")
check("a save in the game's own layout opens", codec.decode(sealed(GAME_LAYOUT), INVENTED_ID) == TEXT)
check("a save made by the bl4 tool opens to its text", codec.decode(BL4_SAVE, INVENTED_ID) == TEXT)
closed = codec.encode(TEXT, INVENTED_ID)
unsealed = codec.aes_ecb(closed, key, decrypt=True)
check("a text is closed in the game's own layout", unsealed[:-unsealed[-1]] == GAME_LAYOUT)

# The game pads only when needed: a text whose zlib stream and length fill whole blocks gets no padding (Kevin's
# Harlowe save written at 20:10:32 on 2026-09-28, essai 36).
filler = 0
while (len(zlib.compress(TEXT + b"#" * filler)) + 4) % 16:
    filler += 1
WHOLE = TEXT + b"#" * filler
WHOLE_LAYOUT = zlib.compress(WHOLE) + len(WHOLE).to_bytes(4, "little")
check("a save whose text fills whole blocks, without padding, opens",
      codec.decode(codec.aes_ecb(WHOLE_LAYOUT, key, decrypt=False), INVENTED_ID) == WHOLE)
check("a text that fills whole blocks is closed without padding, as the game does",
      codec.aes_ecb(codec.encode(WHOLE, INVENTED_ID), key, decrypt=True) == WHOLE_LAYOUT)
check("a text closed then opened comes back the same", codec.decode(closed, INVENTED_ID) == TEXT
      and len(closed) % 16 == 0)

# A text whose layout ends one byte short of a block: a padding of 17 bytes of 17 then makes whole blocks.
filler = 0
while (len(zlib.compress(TEXT + bytes([filler % 251]) * filler)) + 4) % 16 != 15:
    filler += 1
LONG = TEXT + bytes([filler % 251]) * filler
LONG_LAYOUT = zlib.compress(LONG) + len(LONG).to_bytes(4, "little")
check("a padding longer than a block is refused", refused(
    lambda: codec.decode(codec.aes_ecb(LONG_LAYOUT + bytes([17]) * 17, key, decrypt=False), INVENTED_ID)))
check("a wrong Steam ID is refused", refused(lambda: codec.decode(BL4_SAVE, INVENTED_ID + 1)))
opened = codec.aes_ecb(BL4_SAVE, key, decrypt=True)
body = opened[:-opened[-1]]
damaged = body[:-8] + ((zlib.adler32(TEXT) ^ 1).to_bytes(4, "little")) + body[-4:]
pad = 16 - len(damaged) % 16
check("a damaged checksum is refused",
      refused(lambda: codec.decode(codec.aes_ecb(damaged + bytes([pad]) * pad, key, decrypt=False), INVENTED_ID)))
pad = opened[-1]
uneven = opened[:-pad] + bytes(range(1, pad)) + bytes([pad])
check("a padding that does not repeat its length is refused",
      pad > 1 and refused(lambda: codec.decode(codec.aes_ecb(uneven, key, decrypt=False), INVENTED_ID)))
broken = bytearray(GAME_LAYOUT)
broken[len(broken) // 2] ^= 0xFF
check("a damaged compressed text is refused", refused(lambda: codec.decode(sealed(bytes(broken)), INVENTED_ID)))
wrong_length = zlib.compress(TEXT) + (len(TEXT) + 1).to_bytes(4, "little")
check("a length that does not match the text is refused",
      refused(lambda: codec.decode(sealed(wrong_length), INVENTED_ID)))
extra = zlib.compress(TEXT) + bytes(8) + len(TEXT).to_bytes(4, "little")
check("bytes left after the length are refused", refused(lambda: codec.decode(sealed(extra), INVENTED_ID)))
check("a file that is not whole blocks is refused", refused(lambda: codec.decode(BL4_SAVE[:-1], INVENTED_ID)))
decrypted: list[int] = []
real_aes = codec.aes_ecb
codec.aes_ecb = lambda data, keys, decrypt: decrypted.append(len(data)) or real_aes(data, keys, decrypt)
oversized = refused(lambda: codec.decode(bytes(codec.MAX_SAVE_BYTES + 16), INVENTED_ID))
codec.aes_ecb = real_aes
check("an oversized file is refused before any decryption", oversized and not decrypted)

# A text whose zlib stream spans many 256-byte chunks, as a real game's does.
BIG = TEXT + b"".join(f"  item_{n}: {n * 7919 % 100003}\n".encode() for n in range(600))
BIG_SAVE = codec.encode(BIG, INVENTED_ID)
check("the start of a save is its text's first bytes, whole when shorter",
      len(BIG_SAVE) > 8 * codec.START_CHUNK and all(
          codec.decode_start(save, INVENTED_ID, size) == codec.decode(save, INVENTED_ID)[:size]
          for save in (BIG_SAVE, closed, BL4_SAVE) for size in (1, 16, 100, 4096, len(BIG), len(BIG) + 1000)))
decrypted.clear()
codec.aes_ecb = lambda data, keys, decrypt: decrypted.append(len(data)) or real_aes(data, keys, decrypt)
start = codec.decode_start(BIG_SAVE, INVENTED_ID, 64)
codec.aes_ecb = real_aes
check("only the chunks needed are decrypted", start == BIG[:64] and decrypted == [codec.START_CHUNK])
check("a start of another account's save is refused", refused(lambda: codec.decode_start(BIG_SAVE, INVENTED_ID + 1, 64)))
check("a start of garbage is refused", refused(lambda: codec.decode_start(bytes(range(64)), INVENTED_ID, 64))
      and refused(lambda: codec.decode_start(b"", INVENTED_ID, 64))
      and refused(lambda: codec.decode_start(bytes(codec.MAX_SAVE_BYTES + 16), INVENTED_ID, 64)))
check("a truncated first block is refused", refused(lambda: codec.decode_start(BIG_SAVE[:10], INVENTED_ID, 64)))
# A sound zlib stream the game never writes (a small window: its first byte is not 0x78), refused whole and from its
# start alike.
narrow = zlib.compressobj(wbits=9)
NARROW = narrow.compress(TEXT) + narrow.flush() + len(TEXT).to_bytes(4, "little")
check("a start that does not open as the game's zlib stream is refused, as the whole save is",
      NARROW[0] != 0x78 and refused(lambda: codec.decode(sealed(NARROW), INVENTED_ID))
      and refused(lambda: codec.decode_start(sealed(NARROW), INVENTED_ID, 16)))
check("a save cut before its text's end is refused once the text runs out",
      refused(lambda: codec.decode_start(BIG_SAVE[:512], INVENTED_ID, len(BIG))))
check("a start size out of bounds is refused",
      refused(lambda: codec.decode_start(BIG_SAVE, INVENTED_ID, 0))
      and refused(lambda: codec.decode_start(BIG_SAVE, INVENTED_ID, codec.MAX_TEXT_BYTES + 1)))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
