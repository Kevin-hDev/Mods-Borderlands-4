# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Loopback HTTP service of Mod Settings: gives the page its values, writes what the page reports into the log,
runs the key capture. It owns one socket and one thread, which waits on the socket and does nothing else between
requests (OPTI.md, rule 19). It runs while the mod is on and stops when the mod is turned off. Once its thread
ends, on_stopped runs there: the mod hands the game-side cleanup to the game thread with it."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import threading


class LoopbackServer(HTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        # Windows lets a second socket share a port unless it is claimed exclusively (HUD Editor, ERREURS.md).
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Service:
    def __init__(self, constants: dict, make_routes, log, port=None, on_stopped=None):
        self.constants = constants
        self.on_stopped = on_stopped
        self.lock = threading.Lock()
        self.raw_log = log
        self.routes = make_routes(self.log)
        self.stop_requested = False
        self.stop_reason = None
        http = constants["http"]
        self.server = LoopbackServer((http["host"], http["port"] if port is None else port), self.handler())
        self.server.timeout = None
        self.port = self.server.server_address[1]
        self.routes.port = self.port
        self.thread = threading.Thread(target=self.serve, name="mod-settings", daemon=True)

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
            self.routes.capture.cancel()
            self.server.server_close()
            self.log(f"{self.constants['logPrefix']} STOPPED reason={self.stop_reason} requests={self.routes.requests}")
            if self.on_stopped is not None:
                self.on_stopped()

    def handler(self):
        routes = self.routes

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            server_version = "ModSettings"
            sys_version = ""
            # A client that connects and sends nothing must not hold the only thread past its budget.
            timeout = self.constants["http"]["clientTimeoutS"]

            def reply(self, status: int, payload: bytes) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                # Only a trusted request may read the answer: any other origin gets no permission to.
                origin = self.headers.get("Origin")
                if origin is not None and routes.protocol.trusted_request(self.headers, routes.port, routes.constants):
                    self.send_header("Access-Control-Allow-Origin", origin)
                    self.send_header("Vary", "Origin")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)

            def do_GET(self):
                self.reply(*routes.get(self.headers, self.path))

            def do_POST(self):
                length = self.headers.get("Content-Length", "")
                limit = routes.constants["http"]["maxRequestBytes"]
                body = self.rfile.read(int(length)) if length.isdigit() and 0 < int(length) <= limit else None
                self.reply(*routes.post(self.headers, self.path, body))

            def log_message(self, _format, *_args):
                return

        return Handler
