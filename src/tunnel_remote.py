import argparse
import socket
import struct
import threading
from typing import Dict, Tuple

from protocol import read_exact, send_status, pipe_bidirectional, STATUS_OK, STATUS_INVALID_PORT, STATUS_SERVICE_UNAVAILABLE


def parse_services(value: str) -> Dict[int, str]:
    mapping: Dict[int, str] = {}
    for part in value.split(","):
        if not part.strip():
            continue
        port_str, host = part.split(":")
        mapping[int(port_str.strip())] = host.strip()
    return mapping


def handle_tunnel(conn: socket.socket, addr: Tuple[str, int], services: Dict[int, str]) -> None:
    try:
        header = read_exact(conn, 2)
        if header is None:
            conn.close()
            return
        dest_port = struct.unpack("!H", header)[0]
        if dest_port not in services:
            send_status(conn, STATUS_INVALID_PORT, "invalid destination port")
            conn.close()
            return

        target_host = services[dest_port]
        try:
            target_sock = socket.create_connection((target_host, dest_port), timeout=5)
            target_sock.settimeout(None)
        except Exception:
            send_status(conn, STATUS_SERVICE_UNAVAILABLE, "service unavailable")
            conn.close()
            return

        send_status(conn, STATUS_OK, "ok")
        pipe_bidirectional(conn, target_sock)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Remote tunneling server")
    parser.add_argument("--listen", type=int, default=7000)
    parser.add_argument(
        "--services",
        default="9001:time_service,9002:chat_service",
        help="Comma-separated port:host mappings (e.g. 9001:time_service)",
    )
    args = parser.parse_args()

    services = parse_services(args.services)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("0.0.0.0", args.listen))
    server_sock.listen(100)
    print(f"[remote] listening on {args.listen}")

    while True:
        conn, addr = server_sock.accept()
        t = threading.Thread(target=handle_tunnel, args=(conn, addr, services), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
