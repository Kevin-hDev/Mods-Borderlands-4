"""Deterministic ownership when several installed mods request the camera."""

from dataclasses import dataclass
import re
from typing import Any

from .constants import MAX_CLIENTS, PROTOCOL

_OWNER = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


@dataclass(frozen=True)
class Client:
    owner: str
    priority: int
    settings: Any


class Arbiter:
    def __init__(self, max_clients: int = MAX_CLIENTS) -> None:
        if not isinstance(max_clients, int) or not 1 <= max_clients <= MAX_CLIENTS:
            raise ValueError("invalid client limit")
        self._max_clients = max_clients
        self._clients: dict[str, Client] = {}

    def register(self, client: Client, protocol: int) -> None:
        if protocol != PROTOCOL:
            raise RuntimeError("incompatible camera protocol")
        if not isinstance(client.owner, str) or not _OWNER.fullmatch(client.owner):
            raise ValueError("invalid camera owner")
        if not isinstance(client.priority, int) or not -10_000 <= client.priority <= 10_000:
            raise ValueError("invalid camera priority")
        if client.owner not in self._clients and len(self._clients) >= self._max_clients:
            raise RuntimeError("camera client limit reached")
        self._clients[client.owner] = client

    def unregister(self, owner: str) -> None:
        self._clients.pop(owner, None)

    def active(self) -> Client | None:
        if not self._clients:
            return None
        return max(self._clients.values(), key=lambda client: (client.priority, client.owner))

    def __len__(self) -> int:
        return len(self._clients)
