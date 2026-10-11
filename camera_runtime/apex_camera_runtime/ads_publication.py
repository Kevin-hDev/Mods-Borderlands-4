"""The aim context handed to the .dll at each publication (generated_ads.py's contract)."""
import ctypes

from .generated_ads import ADS_ABI, AdsContext, ObjectId

# The .dll orders publications by generation: the last value is never handed out.
LAST_GENERATION = (1 << 64) - 1


def next_generation(counter: int, native_generation: int) -> int | None:
    """Past both ours and the .dll's, or None once the counter is spent."""
    generation = max(counter, native_generation) + 1
    return generation if generation < LAST_GENERATION else None


def owner_key(snapshot) -> tuple:
    """Which owners and weapon type a publication belongs to: another key is another aim."""
    return tuple((ref.address, ref.index, ref.serial) for ref in snapshot.references), snapshot.category


def context(snapshot, generation: int) -> AdsContext:
    return AdsContext(ADS_ABI, ctypes.sizeof(AdsContext), 1, 0, generation,
                      (ObjectId * 8)(*snapshot.references), snapshot.paths)
