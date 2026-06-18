from __future__ import annotations

import socket


def send_python(port: int, code: str, timeout: float = 10.0) -> str:
    payload = code.rstrip() + "\n"
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as connection:
        connection.sendall(payload.encode("utf-8"))
        connection.settimeout(timeout)
        try:
            return connection.recv(65535).decode("utf-8", errors="replace")
        except socket.timeout:
            return ""
