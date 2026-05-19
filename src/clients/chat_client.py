import argparse
import socket
import threading


def recv_loop(sock: socket.socket) -> None:
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            print(data.decode("utf-8", errors="replace"), end="")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5002)
    args = parser.parse_args()

    sock = socket.create_connection((args.host, args.port))
    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    try:
        while True:
            line = input()
            sock.sendall((line + "\n").encode("utf-8", errors="replace"))
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()
