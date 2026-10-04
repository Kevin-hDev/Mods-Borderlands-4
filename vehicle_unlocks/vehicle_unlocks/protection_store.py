"""Shared requests survive restarts; the file never contains player save data."""
import json
import os
from pathlib import Path
import tempfile
from . import protection_config as cfg
from .protection import keys


def path():
    from mods_base import SETTINGS_DIR
    return Path(SETTINGS_DIR) / cfg.FILE


def load():
    target = path()
    try:
        with target.open('rb') as stream:
            raw = stream.read(cfg.MAX_SETTINGS_BYTES + 1)
    except FileNotFoundError:
        return ()
    if len(raw) > cfg.MAX_SETTINGS_BYTES:
        raise ValueError('Settings exceed bound')
    data = json.loads(raw)
    if (type(data) is not dict or set(data) != {'schema', 'selected'}
            or type(data['schema']) is not int or data['schema'] != cfg.SCHEMA
            or type(data['selected']) is not list):
        raise ValueError('Settings schema differs')
    return keys(tuple(data['selected']))


def save(selected):
    selected = keys(selected)
    raw = json.dumps({'schema': cfg.SCHEMA, 'selected': selected}).encode('utf8')
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=cfg.FILE, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink()
