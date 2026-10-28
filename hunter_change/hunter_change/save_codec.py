"""Opens and closes a Borderlands 4 save in pure Python, with the AES-256 of save_aes.py.

A .sav is AES-256-ECB, no IV, of the zlib stream of the text (its own Adler-32 included), then the text's length
(4 bytes, little-endian), then padding to whole blocks in the PKCS7 way, only when needed: a text that already fills
whole blocks gets none (Kevin's saves, essai 36). The key is BASE_KEY with its first 8 bytes XORed with the Steam ID in
little-endian. Cipher and key were read on 2026-09-28 in three independent sources that agree:
github.com/iyre/bl4-save-tools (assets/crypto.js), github.com/monokrome/bl4 (src/bl4/src/crypto.rs), glacierpiece's
blcrypt.py. The layout after the zlib stream was read in Kevin's seven saves the same day: the game writes the length
alone, where those editors put the text's Adler-32 in little-endian before it. Both are read, the game's is written;
the game loads the editors' files too (essais 1 to 3). Epic accounts (a different key) are not handled.

Opening never guesses: a wrong Steam ID, a damaged file or a checksum that does not match raises ValueError, so a
save is either opened whole or not at all. Only decode_start reads a part, the text's beginning, to tell which game a
save is without paying for the whole. The text is returned as bytes and closed as given, never re-written by a
parser: the game's own layout and tags are kept.
"""

import zlib

from .save_aes import BLOCK, aes_ecb, expand_key

BASE_KEY = bytes.fromhex("35ec3377f35db0eabe6b83115403ebfb2725642ed54906290578bd60ba4aa787")
# A character save is about 14 KB and its text about 63 KB (2026-09-28): the bounds leave room without letting a
# wrong file be read whole.
MAX_SAVE_BYTES = 1_000_000
MAX_TEXT_BYTES = 8_000_000
# decode_start decrypts 16 AES blocks at a time and stops at the first chunk that gives the size asked for: one chunk
# costs about 2 ms, a whole save about 45 times as much (measured on 2026-09-29).
START_CHUNK = 16 * BLOCK


def steam_key(steam_id: int) -> list[bytes]:
    if not 0 < steam_id < 2 ** 64:
        raise ValueError("not a Steam ID")
    head = bytes(a ^ b for a, b in zip(BASE_KEY[:8], steam_id.to_bytes(8, "little")))
    return expand_key(head + BASE_KEY[8:])


def decode(data: bytes, steam_id: int) -> bytes:
    """The save's text, or ValueError when it is not a whole save of this Steam account."""
    if not data or len(data) > MAX_SAVE_BYTES or len(data) % BLOCK:
        raise ValueError("not a save file")
    plain = aes_ecb(data, steam_key(steam_id), decrypt=True)
    # Unpadded, the text ends on its length's top byte, 0 below 16 MB; padded, on a byte from 1 to 16.
    pad = plain[-1]
    if pad and (pad > BLOCK or plain[-pad:] != bytes([pad]) * pad):
        raise ValueError("not a save of this Steam account")
    body = plain[:-pad] if pad else plain
    if len(body) < 10 or body[0] != 0x78:
        raise ValueError("not a save of this Steam account")
    inflater = zlib.decompressobj()
    try:
        text = inflater.decompress(body, MAX_TEXT_BYTES)
    except zlib.error as error:
        raise ValueError("damaged save") from error
    trailer = inflater.unused_data
    if not inflater.eof or inflater.unconsumed_tail or len(trailer) not in (4, 8):
        raise ValueError("damaged save")
    if int.from_bytes(trailer[-4:], "little") != len(text):
        raise ValueError("damaged save")
    if len(trailer) == 8 and int.from_bytes(trailer[:4], "little") != zlib.adler32(text):
        raise ValueError("damaged save")
    return text


def decode_start(data: bytes, steam_id: int, size: int) -> bytes:
    """The first `size` bytes of the save's text, all of it when shorter, decrypting and inflating only the chunks
    needed; ValueError when it is not the start of a save of this Steam account. The padding, the length and the
    checksum at the end are never reached, so a save damaged further on passes here: a save kept after its start was
    read is opened whole with decode()."""
    if not data or len(data) > MAX_SAVE_BYTES or len(data) % BLOCK:
        raise ValueError("not a save file")
    if not 0 < size <= MAX_TEXT_BYTES:
        raise ValueError("not a start size")
    keys = steam_key(steam_id)
    inflater = zlib.decompressobj()
    text = b""
    for at in range(0, len(data), START_CHUNK):
        plain = aes_ecb(data[at:at + START_CHUNK], keys, decrypt=True)
        if at == 0 and plain[0] != 0x78:
            raise ValueError("not a save of this Steam account")
        try:
            # Never more than asked: a small save can inflate to far more than its size.
            text += inflater.decompress(plain, size - len(text))
        except zlib.error as error:
            raise ValueError("damaged save") from error
        if len(text) >= size or inflater.eof:
            return text
    raise ValueError("damaged save")


def encode(text: bytes, steam_id: int) -> bytes:
    if len(text) > MAX_TEXT_BYTES:
        raise ValueError("text too large for a save")
    packed = zlib.compress(text) + len(text).to_bytes(4, "little")
    pad = -len(packed) % BLOCK
    return aes_ecb(packed + bytes([pad]) * pad, steam_key(steam_id), decrypt=False)
