import argparse
import socket
import threading
from typing import List


class ChatRoom:
    def __init__(self) -> None:
        self.clients: List[socket.socket] = []
        self.lock = threading.Lock()

    def add(self, conn: socket.socket) -> None:
        with self.lock:
            self.clients.append(conn)

    def remove(self, conn: socket.socket) -> None:
        with self.lock:
            if conn in self.clients:
                self.clients.remove(conn)

    def broadcast(self, data: bytes, sender: socket.socket) -> None:
        with self.lock:
            targets = list(self.clients)
        for conn in targets:
            if conn is sender:
                continue
            try:
                conn.sendall(data)
            except Exception:
                self.remove(conn)


def handle_client(conn: socket.socket, addr: tuple, room: ChatRoom) -> None:
    room.add(conn)
    try:
        conn.sendall(b"Welcome to chat\n")
        while True:
            data = conn.recv(4096)
            if not data:
                break
            room.broadcast(data, conn)
    except Exception:
        pass
    finally:
        room.remove(conn)
        try:
            conn.close()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat broadcast service")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9002)
    args = parser.parse_args()

    room = ChatRoom()
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((args.host, args.port))
    server_sock.listen(50)
    print(f"[chat] listening on {args.host}:{args.port}")

    while True:
        conn, addr = server_sock.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr, room), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
