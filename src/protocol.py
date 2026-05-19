import socket
import struct
import threading
from typing import Optional, Tuple

STATUS_OK = 0
STATUS_INVALID_PORT = 1
STATUS_SERVICE_UNAVAILABLE = 2
STATUS_BAD_HEADER = 3


def read_exact(sock: socket.socket, size: int) -> Optional[bytes]:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def send_status(sock: socket.socket, code: int, message: Optional[str] = None) -> None:
    payload = b"" if message is None else message.encode("utf-8", errors="replace")
    sock.sendall(struct.pack("!BH", code, len(payload)) + payload)


def recv_status(sock: socket.socket) -> Tuple[Optional[int], Optional[str]]:
    header = read_exact(sock, 3)
    if header is None:
        return None, None
    code, length = struct.unpack("!BH", header)
    msg = ""
    if length:
        payload = read_exact(sock, length)
        if payload is None:
            return code, None
        msg = payload.decode("utf-8", errors="replace")
    return code, msg


def pipe_bidirectional(a: socket.socket, b: socket.socket) -> None:
    def forward(src: socket.socket, dst: socket.socket) -> None:
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                dst.sendall(data)
        except Exception:
            pass
        finally:
            try:
                src.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                dst.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass

    t1 = threading.Thread(target=forward, args=(a, b), daemon=True)
    t2 = threading.Thread(target=forward, args=(b, a), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
