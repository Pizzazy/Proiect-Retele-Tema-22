import os
import sys
import subprocess
from dataclasses import dataclass
from typing import Optional


ROOT = os.path.abspath(os.path.dirname(__file__))
PYTHON = sys.executable
LOG_DIR = os.path.join(ROOT, "logs")


@dataclass
class ProcessInfo:
    name: str
    process: subprocess.Popen
    log_handle: Optional[object]


def format_cmd(cmd):
    if os.name == "nt":
        return subprocess.list2cmdline(cmd)
    return " ".join(cmd)


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def spawn_process(name, cmd, use_console=False, log_file=None):
    ensure_log_dir()
    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        if use_console:
            creationflags |= subprocess.CREATE_NEW_CONSOLE
        creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        start_new_session = True

    stdout = None
    stderr = None
    log_handle = None
    if log_file:
        log_path = os.path.join(LOG_DIR, log_file)
        log_handle = open(log_path, "a", encoding="utf-8")
        stdout = log_handle
        stderr = subprocess.STDOUT

    process = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=stdout,
        stderr=stderr,
        text=True,
        creationflags=creationflags,
        start_new_session=start_new_session,
    )
    return ProcessInfo(name=name, process=process, log_handle=log_handle)


def spawn_docker_console():
    if os.name != "nt":
        return spawn_process("docker", cmd_docker_up(), use_console=True)
    cmd_line = format_cmd(cmd_docker_up())
    process = subprocess.Popen(
        [
            "cmd.exe",
            "/c",
            "start",
            "",
            "cmd.exe",
            "/k",
            f"title DockerLogs & {cmd_line}",
        ],
        cwd=ROOT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    return ProcessInfo(name="docker", process=process, log_handle=None)


def spawn_console(title, cmd):
    if os.name != "nt":
        return spawn_process(title, cmd, use_console=True)
    cmd_line = format_cmd(cmd)
    process = subprocess.Popen(
        [
            "cmd.exe",
            "/c",
            "start",
            "",
            "cmd.exe",
            "/k",
            f"title {title} & {cmd_line}",
        ],
        cwd=ROOT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    return ProcessInfo(name=title, process=process, log_handle=None)


def find_listening_pids_windows(port):
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    pids = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        proto, local_addr, state, pid = parts[0], parts[1], parts[3], parts[4]
        if proto.upper() != "TCP" or state.upper() != "LISTENING":
            continue
        if local_addr.endswith(f":{port}"):
            pids.add(pid)
    return pids


def kill_local_listeners(ports):
    if os.name != "nt":
        return
    for port in ports:
        for pid in find_listening_pids_windows(port):
            subprocess.run(["taskkill", "/PID", pid, "/F"], cwd=ROOT)


def stop_process(info: ProcessInfo):
    if info.process.poll() is None:
        try:
            info.process.terminate()
            info.process.wait(timeout=5)
        except Exception:
            info.process.kill()
    if info.log_handle:
        info.log_handle.close()


def cmd_time_server():
    return [PYTHON, "src/services/time_server.py", "--port", "9001"]


def cmd_chat_server():
    return [PYTHON, "src/services/chat_server.py", "--port", "9002"]


def cmd_tunnel_remote():
    return [
        PYTHON,
        "src/tunnel_remote.py",
        "--listen",
        "7000",
        "--services",
        "9001:127.0.0.1,9002:127.0.0.1",
    ]


def cmd_tunnel_local():
    return [
        PYTHON,
        "src/tunnel_local.py",
        "--listen",
        "5001:9001,5002:9002,5003:9999",
        "--remote-host",
        "127.0.0.1",
        "--remote-port",
        "7000",
    ]


def cmd_time_client():
    return [PYTHON, "src/clients/time_client.py", "--host", "127.0.0.1", "--port", "5001"]


def cmd_chat_client():
    return [PYTHON, "src/clients/chat_client.py", "--host", "127.0.0.1", "--port", "5002"]


def cmd_direct_time():
    return [PYTHON, "src/clients/time_client.py", "--host", "127.0.0.1", "--port", "9001"]


def cmd_invalid_port():
    return [PYTHON, "src/clients/time_client.py", "--host", "127.0.0.1", "--port", "5003"]


def cmd_docker_up():
    return ["docker", "compose", "up", "--build"]


def cmd_docker_down():
    return ["docker", "compose", "down"]


def print_menu():
    print("\n=== UI Tunelare (Proiect 22) ===")
    print("\n-- Setup (Docker) --")
    print("1) Pornire Docker: tunel local + tunel remote + servicii")
    print("2) Oprire Docker")
    print("\n-- Clienti prin tunel --")
    print("3) Serviciu 1: client timp prin tunel (port 5001)")
    print("4) Serviciu 2: client chat prin tunel (port 5002)")
    print("\n-- Erori si refuz acces --")
    print("5) Refuz acces direct (port 9001 direct, fara tunel)")
    print("6) Eroare port destinatie invalid (port 5003 -> 9999)")
    print("\n-- Informatii --")
    print("7) Afiseaza toate comenzile (cu explicatii)")
    print("0) Iesire")


def print_commands():
    print("\n--- Comenzi explicate ---")
    print("1) Pornire Docker (stack complet):")
    print(f"   {format_cmd(cmd_docker_up())}")
    print("2) Oprire Docker:")
    print(f"   {format_cmd(cmd_docker_down())}")
    print("3) Client timp prin tunel:")
    print(f"   {format_cmd(cmd_time_client())}")
    print("4) Client chat prin tunel:")
    print(f"   {format_cmd(cmd_chat_client())}")
    print("5) Refuz acces direct (fara tunel):")
    print(f"   {format_cmd(cmd_direct_time())}")
    print("6) Eroare port invalid (5003 -> 9999):")
    print(f"   {format_cmd(cmd_invalid_port())}")






def main():
    processes = {}

    while True:
        print_menu()
        choice = input("Selectie: ").strip()

        if choice == "1":
            if "docker" in processes and processes["docker"].process.poll() is None:
                print("Docker este deja pornit (stack complet).")
                continue
            info = spawn_docker_console()
            processes["docker"] = info
            print("Docker pornit intr-o fereastra separata (stack complet).")

        elif choice == "2":
            subprocess.run(cmd_docker_down(), cwd=ROOT)
            if "docker" in processes:
                stop_process(processes["docker"])
                processes.pop("docker", None)
            print("Docker oprit.")

        elif choice == "3":
            spawn_console("TimeClient", cmd_time_client())
            print("Client timp pornit intr-o fereastra separata.")

        elif choice == "4":
            raw_count = input("Cate ferestre chat vrei? (default 2): ").strip()
            count = 2
            if raw_count:
                try:
                    count = max(1, int(raw_count))
                except ValueError:
                    count = 2
            for index in range(count):
                spawn_console(f"ChatClient{index + 1}", cmd_chat_client())
            print(f"Clienti chat porniti in {count} ferestre separate.")

        elif choice == "5":
            spawn_console("DirectAccess", cmd_direct_time())
            print("Diagnostic direct pornit intr-o fereastra separata.")

        elif choice == "6":
            spawn_console("InvalidPort", cmd_invalid_port())
            print("Diagnostic port invalid pornit intr-o fereastra separata.")

        elif choice == "7":
            print_commands()

        elif choice == "0":
            for key in list(processes.keys()):
                stop_process(processes[key])
                processes.pop(key, None)
            kill_local_listeners([5001, 5002, 5003, 7000, 9001, 9002])
            print("Iesire.")
            break

        else:
            print("Optiune invalida.")


if __name__ == "__main__":
    main()
