"""Clients for the tests of the energy service and of its wire: a well-behaved one, a raw one, and one that feeds
its request a byte at a time. Always on the port a test gives: never the game's own."""

import http.client
import socket
import threading
import time

HOST = "127.0.0.1"


def ask(port: int, path: str, method: str = "GET"):
    """(status, headers, body) of one request."""
    connection = http.client.HTTPConnection(HOST, port, timeout=2)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def raw(port: int, request: bytes) -> bytes:
    """What the server sends back to these bytes, until it closes the connection."""
    with socket.create_connection((HOST, port), timeout=2) as plain:
        plain.sendall(request)
        answer = b""
        try:
            while chunk := plain.recv(4096):
                answer += chunk
        except OSError:
            pass
        return answer


def drip(port: int, seconds: float) -> None:
    """A client that feeds its request a byte every tenth of a second: each byte comes well within the connection's
    bound, the whole request never does."""
    try:
        with socket.create_connection((HOST, port), timeout=2) as slow:
            end = time.perf_counter() + seconds
            for byte in b"GET /" + b"x" * 1000:
                if time.perf_counter() >= end:
                    break
                slow.sendall(bytes([byte]))
                time.sleep(0.1)
    except OSError:
        pass  # The server closed the connection: what the test waits for.


def dripping(port: int, seconds: float) -> threading.Thread:
    """Starts that client and waits until the server has it in hand."""
    thread = threading.Thread(target=drip, args=(port, seconds), daemon=True)
    thread.start()
    time.sleep(0.15)
    return thread
