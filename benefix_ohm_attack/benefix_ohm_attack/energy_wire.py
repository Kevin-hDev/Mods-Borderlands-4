"""The energy service's wire: a loopback HTTP server that answers one path and refuses the rest in its own words.

What it answers is not its business: the server it is given carries `answer`, `asked` and `note`, set by the
service that owns it (energy_service.py).

A program on this PC that holds a connection open, or feeds it a byte at a time, stalls the bar for CONNECTION_S at
most, never the game. That time is one deadline for the whole connection, not a wait renewed at each byte
(docs/candidats/HUD/ERREURS.md, 49; audit of 2026-10-01: a byte every 0.3 s held the service for good).
"""

import json
import pkgutil
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# Shared with the bar's script, which the bar's builder writes them into. Read through the package's loader: in
# game the mod runs from inside its .sdkmod archive, where this file has no path of its own.
CONSTANTS = json.loads(pkgutil.get_data(__package__, "assets/bar.constants.json").decode("utf-8"))
CONNECTION_S = 0.5
# More than any request the bar's script sends; past it the connection is dropped.
MAX_REQUEST_BYTES = 8192
FAILED = b'{"error":"request_failed"}'
DROPPED = "the energy service dropped a request"


class Server(HTTPServer):
    # Windows lets two listeners share a port unless one claims it alone (docs/candidats/HUD/ERREURS.md, 43).
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, request, client_address) -> None:
        self.note(DROPPED)


class Request:
    """The request's bytes, read under one deadline set when the connection opens, and no more than
    MAX_REQUEST_BYTES of them: past either, TimeoutError, which http.server takes as a request to drop. The time
    left at the last read is also what the answer's writing gets: the connection has no other timeout."""

    def __init__(self, connection: socket.socket) -> None:
        self._connection = connection
        self._deadline = time.perf_counter() + CONNECTION_S
        self._buffer = b""
        self._taken = 0

    def readline(self, limit: int = -1) -> bytes:
        while b"\n" not in self._buffer and (limit < 0 or len(self._buffer) < limit):
            remaining = self._deadline - time.perf_counter()
            if remaining <= 0 or self._taken >= MAX_REQUEST_BYTES:
                raise TimeoutError("the request took too long or too much")
            self._connection.settimeout(remaining)
            chunk = self._connection.recv(min(1024, MAX_REQUEST_BYTES - self._taken))
            if not chunk:
                break
            self._taken += len(chunk)
            self._buffer += chunk
        cut = self._buffer.find(b"\n") + 1 or len(self._buffer)
        if limit >= 0:
            cut = min(cut, limit)
        line, self._buffer = self._buffer[:cut], self._buffer[cut:]
        return line

    def close(self) -> None:
        self._buffer = b""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self) -> None:
        super().setup()
        self.rfile.close()
        self.rfile = Request(self.connection)

    def version_string(self) -> str:
        # Not the Python version the game runs: nobody asking needs it.
        return "BenefixOhmAttack"

    def _send(self, status: int, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)

    def send_error(self, code, message=None, explain=None) -> None:
        # Not http.server's own page, which hands the request's words back and names the library.
        self._send(code, FAILED)

    def do_GET(self) -> None:
        if self.path != CONSTANTS["path"]:
            self._send(404, FAILED)
            return
        self.server.asked()
        payload = self.server.answer()
        if payload is None:
            self._send(503, FAILED)
        else:
            self._send(200, payload)

    def log_error(self, format, *args) -> None:
        # http.server's only word left here: a request it gave up reading (the deadline, or too many bytes).
        self.server.note(DROPPED)

    def log_message(self, format, *args) -> None:
        return
