from __future__ import annotations

import socketserver
import threading
import traceback


_SERVER = None


class _MayaRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        chunks = []
        while True:
            data = self.request.recv(65535)
            if not data:
                break
            chunks.append(data)
            if data.endswith(b"\n"):
                break

        code = b"".join(chunks).decode("utf-8", errors="replace")
        try:
            response = _execute_in_maya_main_thread(code)
        except Exception:
            response = traceback.format_exc()
        self.request.sendall((response or "OK").encode("utf-8", errors="replace"))


class _ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start(port: int = 7821) -> None:
    global _SERVER
    if _SERVER:
        print(f"Portal Maya command server already running on :{port}")
        return

    _SERVER = _ThreadedServer(("127.0.0.1", port), _MayaRequestHandler)
    thread = threading.Thread(target=_SERVER.serve_forever, daemon=True)
    thread.start()
    print(f"Portal Maya command server started on :{port}")


def _execute_in_maya_main_thread(code: str) -> str:
    import maya.utils

    def _runner() -> str:
        namespace = {"__name__": "__portal_maya_exec__"}
        exec(code, namespace, namespace)
        return "OK"

    return maya.utils.executeInMainThreadWithResult(_runner)


if __name__ == "__main__":
    start()
