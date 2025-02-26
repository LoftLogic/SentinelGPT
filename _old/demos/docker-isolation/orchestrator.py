import ast
import os
import sys
import time
import docker
import threading
import re
import json
import select
from typing import Any, Tuple
import socket

listener_ip = "0.0.0.0"
listener_port = 65432

clients = []
client_map = {}

worker_port = 0
worker_id = ''
value_assigned = threading.Event()


# Define tool code strings with proper type signatures.
tool_codes = {
    "tool1": """def main_tool(a: int, b: int) -> int:
    return a + b
""",
    "tool2": """def main_tool(x: int) -> int:
    return x * 2
"""
}

docker_client = docker.from_env()

# need to edit


def handle_invoke(message: str, addr) -> None:
    # print(f"[Orchestrator] Received INVOKE message: '{message}'")
    m = re.match(r"INVOKE:\s+(\S+)\s+(.*)", message)
    if not m:
        writer_thread = threading.Thread(target=handle_write, args=(
            addr, "RESPONSE: ERROR: Malformed INVOKE."), daemon=True)
        writer_thread.start()
        return
    tool = m.group(1)
    args_str = m.group(2)
    try:
        args = eval(args_str)
        if not isinstance(args, tuple):
            args = (args,)
    except Exception as e:
        writer_thread = threading.Thread(target=handle_write, args=(
            addr, f"RESPONSE: ERROR: Couldn't parse arguments: {args_str}"), daemon=True)
        writer_thread.start()
        return
    print(f"[Orchestrator] Invoking tool '{tool}' with args {args}")
    if tool not in tool_codes:
        writer_thread = threading.Thread(target=handle_write, args=(
            addr, "RESPONSE: ERROR: Unknown tool"), daemon=True)
        writer_thread.start()
        return
    code = tool_codes[tool]
    try:
        tool_container = docker_client.containers.run(
            "tool-runner-image",
            environment={
                "TOOL_CODE": code,
                "ARGS": json.dumps(args)
            },
            detach=True,
            tty=False,
            remove=False
        )
        tool_container.wait()
        output = tool_container.logs().decode('utf-8').strip()
        print(f"[Orchestrator] Raw tool container output: '{output}'")

        result = int(output)
        response = f"RESPONSE: {result}"
    except Exception as e:
        response = f"RESPONSE: ERROR: {str(e)}"
        print(f"[Orchestrator] Error invoking tool '{tool}': {e}")
    value_assigned.wait()
    global worker_port
    writer_thread = threading.Thread(target=handle_write, args=(
        ('127.0.0.1', worker_port), response), daemon=True)
    writer_thread.start()


def start_listener():
    """Starts the server and listens for connections indefinitely."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((listener_ip, listener_port))
    server.listen(5)
    print(f"[*] Orchestrator listening on {listener_ip}:{listener_port}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(
            client_socket, addr), daemon=True).start()


def handle_client(client_socket, address):
    """Handles incoming messages from a connected client."""
    print(f"[Orchestrator] New connection from {address}")

    try:
        while True:
            message = client_socket.recv(1024).decode()
            if not message:
                break
            # need to send ip of server from workwe..handle that here
            if message.startswith("INVOKE:"):
                handle_invoke(message, address)
            elif message.startswith("PRINT"):
                print(f"Print from worker {message.split(":", 1)[1].strip()}")
            elif message.startswith("INFO"):
                _, addy = message.split()
                ipaddr, port = addy.split(":")
                client_map[ipaddr] = int(port)
            elif message.startswith("TERMINATE"):
                client = docker.from_env()
                container = client.containers.get(worker_id)
                container.kill()
                os._exit(0)
            print(f"[Orchestrator] Received {message} from [{address}]")
    except ConnectionResetError:
        print(f"[-] Connection lost with {address}")
    finally:
        client_socket.close()


def handle_write(addr, message):
    try:
        # Create a new socket to send the message
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr_tuple = (str(addr[0]), int(addr[1]))
        client_socket.connect(addr_tuple)  # Connect to the specified client

        client_socket.send(message.encode())  # Send the message
        print(f"[Orchestrator] Sent {message} to {addr_tuple}")
    except Exception as e:
        print(f"[-] Error sending {message} to {addr_tuple}: {e}")
    finally:
        client_socket.close()  # Close the connection after sending


def orchestrator_main() -> None:

    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()

    with open("script.txt", "r") as f:
        script_content = f.read()
    print("[Orchestrator] Loaded script:")
    print(script_content)

    container = docker_client.containers.run(
        "worker-image",
        command="python /app/worker.py",
        environment={"SCRIPT": script_content},
        tty=False,         # tty=False for a raw stream.
        stdin_open=True,
        detach=True,
        network_mode="none",
        ports={'8080/tcp': None},
    )
    time.sleep(1)

    container.reload()
    global worker_port
    worker_port = int(container.ports['8080/tcp'][0]["HostPort"])
    value_assigned.set()
    print(f"[Orchestrator] Worker container started: {container.short_id}")
    global worker_id
    worker_id = container.short_id
    print(container.ports)

    listener_thread.join()
    container.wait()


if __name__ == "__main__":
    orchestrator_main()
