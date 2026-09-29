"""AES-256 in pure Python, for the save codec: the game's Python has no AES (FIPS-197, electronic codebook mode only).

Correctness is tied to the standard's own test vector (appendix C.3) by test_save_aes.py, and to the bl4 tool and
the game's saves through test_save_codec.py. Slow but enough: a 14 KB save takes about 80 ms each way
(2026-09-28).
"""

BLOCK = 16
ROUNDS = 14


def _xtime(value: int) -> int:
    value <<= 1
    return (value ^ 0x11B) if value & 0x100 else value


def _multiply(a: int, b: int) -> int:
    result = 0
    while b:
        if b & 1:
            result ^= a
        a, b = _xtime(a), b >> 1
    return result


def _sboxes() -> tuple[bytes, bytes]:
    """The S-box from its definition: the inverse in GF(2^8), then the affine map of FIPS-197, section 5.1.1."""
    inverse = [0] * 256
    for a in range(1, 256):
        inverse[a] = next(b for b in range(1, 256) if _multiply(a, b) == 1)
    box = bytearray(256)
    for a in range(256):
        b = inverse[a]
        box[a] = b ^ ((b << 1 | b >> 7) & 0xFF) ^ ((b << 2 | b >> 6) & 0xFF) ^ ((b << 3 | b >> 5) & 0xFF) \
            ^ ((b << 4 | b >> 4) & 0xFF) ^ 0x63
    inverse_box = bytearray(256)
    for a in range(256):
        inverse_box[box[a]] = a
    return bytes(box), bytes(inverse_box)


SBOX, INVERSE_SBOX = _sboxes()
_TIMES = {factor: bytes(_multiply(a, factor) for a in range(256)) for factor in (2, 3, 9, 11, 13, 14)}
# ShiftRows on a block held column by column (byte r + 4c is row r, column c): row r moves r columns left.
_SHIFT = [r + 4 * ((c + r) % 4) for c in range(4) for r in range(4)]
_UNSHIFT = [r + 4 * ((c - r) % 4) for c in range(4) for r in range(4)]


def expand_key(key: bytes) -> list[bytes]:
    """The 15 round keys of AES-256."""
    if len(key) != 32:
        raise ValueError("an AES-256 key is 32 bytes")
    words = [list(key[index:index + 4]) for index in range(0, 32, 4)]
    rcon = 1
    for index in range(8, 4 * (ROUNDS + 1)):
        word = list(words[index - 1])
        if index % 8 == 0:
            word = [SBOX[byte] for byte in word[1:] + word[:1]]
            word[0] ^= rcon
            rcon = _xtime(rcon)
        elif index % 8 == 4:
            word = [SBOX[byte] for byte in word]
        words.append([a ^ b for a, b in zip(words[index - 8], word)])
    return [bytes(sum(words[4 * turn:4 * turn + 4], [])) for turn in range(ROUNDS + 1)]


def _mix(state: list[int], factors: tuple[int, int, int, int]) -> list[int]:
    t0, t1, t2, t3 = (_TIMES[factor] if factor != 1 else None for factor in factors)
    mixed = []
    for column in range(0, 16, 4):
        a = state[column:column + 4]
        for row in range(4):
            value = 0
            for offset, table in enumerate((t0, t1, t2, t3)):
                byte = a[(row + offset) % 4]
                value ^= byte if table is None else table[byte]
            mixed.append(value)
    return mixed


def _encrypt_block(block: bytes, keys: list[bytes]) -> bytes:
    state = [a ^ b for a, b in zip(block, keys[0])]
    for turn in range(1, ROUNDS + 1):
        state = [SBOX[state[index]] for index in _SHIFT]
        if turn != ROUNDS:
            state = _mix(state, (2, 3, 1, 1))
        state = [a ^ b for a, b in zip(state, keys[turn])]
    return bytes(state)


def _decrypt_block(block: bytes, keys: list[bytes]) -> bytes:
    state = [a ^ b for a, b in zip(block, keys[ROUNDS])]
    for turn in range(ROUNDS - 1, -1, -1):
        state = [INVERSE_SBOX[state[index]] for index in _UNSHIFT]
        state = [a ^ b for a, b in zip(state, keys[turn])]
        if turn:
            state = _mix(state, (14, 11, 13, 9))
    return bytes(state)


def aes_ecb(data: bytes, keys: list[bytes], decrypt: bool) -> bytes:
    if len(data) % BLOCK:
        raise ValueError("not whole AES blocks")
    step = _decrypt_block if decrypt else _encrypt_block
    return b"".join(step(data[index:index + BLOCK], keys) for index in range(0, len(data), BLOCK))
