"""The companions' bars service's wire (decision 36 of docs/renforts/README.md), a loopback HTTP server that answers
one path and refuses the rest in its own words. Benefix Ohm Attack's energy_wire.py, the way verified in game (its bar,
1 October 2026), taken over rather than loaded, as one mod never leans on another; then the trials' copy
(docs/renforts/sondes, trials 178 to 182), moved here.

What it answers is not its business: the server carries `path`, `answer`, `asked` and `note`, set by the service
that owns it (bars_service.py).

A program on this PC that holds a connection open, or feeds it a byte at a time, stalls the bars for CONNECTION_S at
most, never the game: one deadline for the whole connection, not a wait renewed at each byte
(docs/candidats/HUD/ERREURS.md, 49).

Its thread sleeps until a request comes or the stop wakes it (serve, stop): http.server's own loop woke every 50 ms
for nothing, and its stop waited for the next of those wakes, the game held 30 to 48 ms at each team's stop (trial
219; audit of 24 October 2026, A1). The thread closes the port itself as it ends, so that a mod starting its own
team just after finds the port free.
"""

import selectors
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

CONNECTION_S = 0.5
# More than any request the bars' script sends; past it the connection is dropped.
MAX_REQUEST_BYTES = 8192
FAILED = b'{"error":"request_failed"}'
DROPPED = "the companions' bars service dropped a request"


class Server(HTTPServer):
    # Windows lets two listeners share a port unless one claims it alone (docs/candidats/HUD/ERREURS.md, 43).
    allow_reuse_address = False
    # handle_request waits no longer: serve calls it once a request is there.
    timeout = 0

    def __init__(self, address: tuple, handler: type) -> None:
        # Made first: a port refused closes the server at once (socketserver calls server_close), these with it.
        self._waking, self._woken = socket.socketpair()
        self._stopping = False
        super().__init__(address, handler)

    def serve(self) -> None:
        """Answers each request as it comes until stop(), asleep in between; the port closed as it ends."""
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self, selectors.EVENT_READ)
                selector.register(self._woken, selectors.EVENT_READ)
                while not self._stopping:
                    ready = selector.select()
                    if not self._stopping and any(key.fileobj is self for key, _events in ready):
                        self.handle_request()
        finally:
            self.server_close()

    def stop(self) -> None:
        """The serving thread told to end now, woken if it sleeps."""
        self._stopping = True
        try:
            self._waking.send(b"\0")
        except OSError:
            # Closed already: the thread has ended, the port with it.
            return

    def server_close(self) -> None:
        super().server_close()
        self._waking.close()
        self._woken.close()

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, request, client_address) -> None:
        self.note(DROPPED)


class Request:
    """The request's bytes, read under one deadline set when the connection opens, and no more than
    MAX_REQUEST_BYTES of them: past either, TimeoutError, which http.server takes as a request to drop."""

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
        return "Reinforcements"

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
        if self.path != self.server.path:
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
