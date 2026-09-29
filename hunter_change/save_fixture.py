"""Invented saves for the save tests, in the game's own layout as read in Kevin's saves on 2026-09-28. No real save
and no real Steam ID here: the accounts are below the first Steam account number (76561197960265728)."""

import hashlib
import pathlib
import tempfile

from hunter_change import save_codec

ACCOUNT, OTHER = 76561190000000001, 76561190000000002
HARLOWE_GAME, VEX_GAME = "8107146506D5906AD9BCCD4479661B4D", "0123456789ABCDEF0123456789ABCDEF"
TREES = {
    "Gravitar": (b"  graphs: \n  - name: progress_graph_grav_action_skills\n    group_def_name: progress_group_gravitar\n"
                 b"    nodes: \n    - name: Grav\n      is_activated: true\n    - name: Progress_Grav_Trunk\n"
                 b"      points_spent: 3\n"),
    "Paladin": (b"  graphs: \n  - name: Progress_Paladin_ActionSkills\n    group_def_name: ProgressGroup_Paladin\n"
                b"    nodes: \n    - name: Calamity\n      is_activated: true\n"),
    "DarkSiren": (b"  graphs: \n  - name: Progress_DarkSiren_ActionSkills\n    group_def_name: ProgressGroup_DarkSiren\n"
                  b"    nodes: \n  - name: Progress_DS_Trunk_Domination\n    group_def_name: ProgressGroup_DarkSiren\n"
                  b"    nodes: \n    - name: DS_Node\n      points_spent: 5\n"),
}


def game_text(game: str, code: str, name: str, tree: bytes | None) -> bytes:
    """A game's text: its state block, a decoy class further down, then progression with or without a tree."""
    return (f"state: \n  char_guid: {game}\n  class: Char_{code}\n  char_name: {name}\n  experience: \n"
            f"  - type: Character\n    level: 52\n    points: 3910506\n  inventory: \n    items: \n"
            f"save_game_header: \n  guid: 76C11FD05C8997C7F3C9BCF1DA5A2AE7\n  class: Char_Decoy\n").encode("utf-8") + (
        b"progression: \n" + (tree or b"") + b"  point_pools: \n    characterprogresspoints: 51\n"
        b"missions: \n  local_sets: \n")


def full_size(text: bytes) -> bytes:
    """The text with invented items in its inventory up to a real game's size: about 61 KB of text closing to about
    12.5 KB, where Kevin's are about 63 KB and 14 KB (2026-09-28). The serials are hashes, so they pack about as
    badly as the game's own."""
    serials = (hashlib.sha256(str(n).encode()).hexdigest()[:10 + n % 14] for n in range(820))
    items = b"".join(f"    - slot_{n % 40}: \n      serial: '@Ugr{serial}'\n      state_flags: {n % 7}\n".encode()
                     for n, serial in enumerate(serials))
    return text.replace(b"    items: \n", b"    items: \n" + items, 1)


def saves_folder() -> tuple[pathlib.Path, pathlib.Path]:
    """A fresh Documents folder, and the client folder of ACCOUNT inside it."""
    documents = pathlib.Path(tempfile.mkdtemp())
    client = documents / "My Games" / "Borderlands 4" / "Saved" / "SaveGames" / str(ACCOUNT) / "Profiles" / "client"
    client.mkdir(parents=True)
    return documents, client


def put(client: pathlib.Path, slot: int, text: bytes, account: int = ACCOUNT) -> pathlib.Path:
    path = client / f"{slot}.sav"
    path.write_bytes(save_codec.encode(text, account))
    return path
