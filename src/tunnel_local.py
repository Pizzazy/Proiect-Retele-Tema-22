import argparse
import socket
import struct
import threading
from typing import Dict, Tuple

from protocol import recv_status, pipe_bidirectional, STATUS_OK


def parse_listen(value: str) -> Dict[int, int]:
    mapping: Dict[int, int] = {}
    for part in value.split(","):
        if not part.strip():
            continue
        local_str, dest_str = part.split(":")
        local_port = int(local_str.strip())
        dest_port = int(dest_str.strip())
        mapping[local_port] = dest_port
    return mapping


def handle_client(
    client_sock: socket.socket,
    client_addr: Tuple[str, int],
    remote_host: str,
    remote_port: int,
    dest_port: int,
) -> None:
    try:
        remote_sock = socket.create_connection((remote_host, remote_port), timeout=5)
        remote_sock.settimeout(None)
    except Exception:
        try:
            client_sock.sendall(b"ERROR: tunnel remote unavailable\n")
        except Exception:
            pass
        client_sock.close()
        return

    try:
        remote_sock.sendall(struct.pack("!H", dest_port))
        status, message = recv_status(remote_sock)
        if status != STATUS_OK:
            msg = message or "invalid destination"
            try:
                client_sock.sendall(f"ERROR: {msg}\n".encode("utf-8", errors="replace"))
            except Exception:
                pass
            remote_sock.close()
            client_sock.close()
            return
        pipe_bidirectional(client_sock, remote_sock)
    except Exception:
        try:
            remote_sock.close()
        except Exception:
            pass
        try:
            client_sock.close()
        except Exception:
            pass


def serve_port(local_port: int, dest_port: int, remote_host: str, remote_port: int) -> None:
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("0.0.0.0", local_port))
    server_sock.listen(50)
    print(f"[local] listening on {local_port} -> {dest_port}")
    while True:
        client_sock, client_addr = server_sock.accept()
        t = threading.Thread(
            target=handle_client,
            args=(client_sock, client_addr, remote_host, remote_port, dest_port),
            daemon=True,
        )
        t.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local tunneling server")
    parser.add_argument(
        "--listen",
        default="5001:9001,5002:9002,5003:9999",
        help="Comma-separated mappings local:dest (e.g. 5001:9001)",
    )
    parser.add_argument("--remote-host", default="tunnel_remote")
    parser.add_argument("--remote-port", type=int, default=7000)
    args = parser.parse_args()

    mapping = parse_listen(args.listen)
    threads = []
    for local_port, dest_port in mapping.items():
        t = threading.Thread(
            target=serve_port,
            args=(local_port, dest_port, args.remote_host, args.remote_port),
            daemon=True,
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
