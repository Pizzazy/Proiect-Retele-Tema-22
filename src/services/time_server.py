import argparse
import socket
import threading
import time
from datetime import datetime


def handle_client(conn: socket.socket, addr: tuple, interval: float) -> None:
    try:
        while True:
            now = datetime.now().isoformat(timespec="seconds")
            conn.sendall((now + "\n").encode("utf-8"))
            time.sleep(interval)
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Time service")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9001)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((args.host, args.port))
    server_sock.listen(50)
    print(f"[time] listening on {args.host}:{args.port}")

    while True:
        conn, addr = server_sock.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr, args.interval), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
