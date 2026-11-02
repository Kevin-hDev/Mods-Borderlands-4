# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Loopback HTTP service of Logs & Conflicts, rewritten from Mod Settings' server.py. It owns one socket and one
thread, which waits on the socket and does nothing else between requests (OPTI.md, rule 19). It runs while the mod
is on and stops when the mod is turned off, without making the game wait."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import socket
import sys
import threading
import time

# ASCII digits only, and few of them: str.isdigit() takes "²", which int() then refuses (security audit,
# 1 November 2026).
CONTENT_LENGTH = re.compile(r"[0-9]{1,9}")
CHUNK = 4096


class LoopbackServer(HTTPServer):
    allow_reuse_address = False
    # Set by the service: a request failing inside the standard library writes one bounded line, never a traceback.
    report_failure = None

    def server_bind(self):
        # Windows lets a second socket share a port unless it is claimed exclusively (HUD Editor, ERREURS.md).
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def handle_error(self, request, client_address):
        if self.report_failure is not None:
            self.report_failure(sys.exc_info()[0])


class RequestReader:
    """The request's reader, with one deadline for the whole request rather than one per read: a client sending a byte
    now and then must not hold the only thread, nor keep it from stopping (security audit, 1 November 2026)."""

    def __init__(self, connection, budget_s: float, file, clock=time.monotonic):
        self.connection = connection
        self.deadline = clock() + budget_s
        self.clock = clock
        self.file = file
        self.buffer = b""

    def fill(self) -> bool:
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise TimeoutError("request deadline")
        self.connection.settimeout(remaining)
        chunk = self.connection.recv(CHUNK)
        self.buffer += chunk
        return bool(chunk)

    def readline(self, limit: int = -1) -> bytes:
        while b"\n" not in self.buffer and (limit < 0 or len(self.buffer) < limit) and self.fill():
            pass
        end = self.buffer.find(b"\n")
        size = end + 1 if end >= 0 else len(self.buffer)
        if limit >= 0:
            size = min(size, limit)
        line, self.buffer = self.buffer[:size], self.buffer[size:]
        return line

    def read(self, size: int) -> bytes:
        while len(self.buffer) < size and self.fill():
            pass
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        return data

    def close(self) -> None:
        self.file.close()


def failure_cause(kind) -> str:
    """A failed request's cause among a few, by which its log lines are counted: the error classes are many. A request
    the page gave up on must not hide a real error that comes later (second review)."""
    if isinstance(kind, type) and issubclass(kind, ConnectionError):
        return "connection"
    if isinstance(kind, type) and issubclass(kind, TimeoutError):
        return "timeout"
    return "other"


def request_body(length: str, rfile, limit: int):
    """b"" when no body is sent, the body when its size is within the limit, None otherwise: a body too long is
    refused, never taken for an empty one."""
    if length in ("", "0"):
        return b""
    if not CONTENT_LENGTH.fullmatch(length) or int(length) > limit:
        return None
    return rfile.read(int(length))


class Service:
    def __init__(self, constants: dict, make_routes, log, port=None):
        self.constants = constants
        self.lock = threading.Lock()
        self.raw_log = log
        self.routes = make_routes(self.log)
        self.stop_requested = False
        self.stop_reason = None
        http = constants["http"]
        self.server = LoopbackServer((http["host"], http["port"] if port is None else port), self.handler())
        self.server.timeout = None
        self.server.report_failure = lambda kind: self.routes.note(
            f"request_failed_{failure_cause(kind)}", f"REQUEST_FAILED error={getattr(kind, '__name__', 'none')}")
        self.port = self.server.server_address[1]
        self.routes.port = self.port
        self.thread = threading.Thread(target=self.serve, name="logs-conflicts", daemon=True)

    def log(self, message: str) -> None:
        with self.lock:
            self.raw_log(message)

    def start(self) -> None:
        self.log(f"{self.constants['logPrefix']} STARTED port={self.port}")
        self.thread.start()

    def request_stop(self, reason: str) -> None:
        if self.stop_requested:
            return
        self.stop_reason = reason
        self.stop_requested = True
        # A thread already ended has nothing to wake, and on Windows a connection to a closed port takes a second to
        # be refused: the game would wait that long (rules audit, 1 November 2026).
        if not self.thread.is_alive():
            return
        # The thread waits on the socket without a timeout: one connection of our own wakes it to see the flag.
        http = self.constants["http"]
        try:
            with socket.create_connection((http["host"], self.port), timeout=http["stopConnectTimeoutS"]):
                pass
        except OSError:
            # Nothing to wake: the socket is already closed, or the thread ends at its next request.
            pass

    def stop(self, timeout_s: float = 2.0) -> bool:
        """Stop and wait: off the game thread only (tests). In game, request_stop() alone."""
        self.request_stop("stop_command")
        self.thread.join(timeout_s)
        return not self.thread.is_alive()

    def serve(self) -> None:
        try:
            while not self.stop_requested:
                self.server.handle_request()
        except OSError:
            self.stop_reason = "socket_error"
        finally:
            self.server.server_close()
            self.log(f"{self.constants['logPrefix']} STOPPED reason={self.stop_reason} requests={self.routes.requests}")

    def handler(self):
        routes = self.routes
        budget_s = self.constants["http"]["clientTimeoutS"]

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            server_version = "LogsConflicts"
            sys_version = ""
            timeout = budget_s

            def setup(self):
                super().setup()
                self.rfile = RequestReader(self.connection, budget_s, self.rfile)

            def reply(self, status: int, payload: bytes) -> None:
                # The reading may have used up the request's deadline: the answer gets a budget of its own.
                self.connection.settimeout(budget_s)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                # Only a trusted request may read the answer: any other origin gets no permission to.
                origin = self.headers.get("Origin")
                if origin is not None and routes.protocol.trusted_request(self.headers, routes.port, routes.constants):
                    self.send_header("Access-Control-Allow-Origin", origin)
                    self.send_header("Vary", "Origin")
                # No web page may load an answer as a script (conception, section 6).
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)

            def do_GET(self):
                self.reply(*routes.get(self.headers, self.path))

            def do_POST(self):
                body = request_body(self.headers.get("Content-Length", ""), self.rfile,
                                    routes.constants["http"]["maxRequestBytes"])
                self.reply(*routes.post(self.headers, self.path, body))

            def log_message(self, _format, *_args):
                return

            def log_error(self, _format, *args):
                # The standard library catches a request's timeout itself and passes it only here (handle_one_request):
                # a request cut at its deadline left no line at all (third review, 1 November 2026).
                if args and isinstance(args[0], TimeoutError) and self.server.report_failure is not None:
                    self.server.report_failure(TimeoutError)

        return Handler
