import argparse
import socket


def main() -> None:
    parser = argparse.ArgumentParser(description="Time client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()

    sock = socket.create_connection((args.host, args.port))
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            print(data.decode("utf-8", errors="replace"), end="")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
