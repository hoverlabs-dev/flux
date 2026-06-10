from __future__ import annotations

import socketserver
import threading
import traceback
from dataclasses import dataclass, field
from queue import Queue

import bpy


_SERVER = None
_QUEUE = Queue()


@dataclass(slots=True)
class _Request:
    code: str
    done: threading.Event = field(default_factory=threading.Event)
    response: str = ""


class _BlenderRequestHandler(socketserver.BaseRequestHandler):
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
        request = _Request(code=code)
        _QUEUE.put(request)
        request.done.wait(timeout=60.0)
        response = request.response or "Timed out waiting for Blender main thread."
        self.request.sendall(response.encode("utf-8", errors="replace"))


class _ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def start(port: int = 7722) -> None:
    global _SERVER
    if _SERVER:
        print(f"Portal Blender command server already running on :{port}")
        return
    if not bpy.app.timers.is_registered(_process_queue):
        bpy.app.timers.register(_process_queue, persistent=True)
    _SERVER = _ReusableTCPServer(("127.0.0.1", port), _BlenderRequestHandler)
    thread = threading.Thread(target=_SERVER.serve_forever, daemon=True)
    thread.start()
    print(f"Portal Blender command server started on :{port}")


def _process_queue():
    while not _QUEUE.empty():
        request = _QUEUE.get()
        namespace = {"__name__": "__portal_blender_exec__"}
        try:
            exec(request.code, namespace, namespace)
            request.response = "OK"
        except Exception:
            request.response = traceback.format_exc()
        finally:
            request.done.set()
    return 0.1
