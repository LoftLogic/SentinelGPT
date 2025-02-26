# worker.py
from typing import Any

import os
import ast
import queue
import sys
import socket
import threading
import base64
import json

listener_ip = socket.gethostbyname(socket.gethostname())
listener_port = 8080
listener_addr = (listener_ip, listener_port)

ORCHESTRATOR_IP = "172.17.0.1"
ORCHESTRATOR_PORT = 65432
ORCHESTRATOR_ADDR = (ORCHESTRATOR_IP, ORCHESTRATOR_PORT)

response_queue = queue.Queue()

orchestrator_response = ''


def display(data: str) -> None:
    encoded = base64.b64encode(data.encode()).decode()
    writer_thread = threading.Thread(
        target=handle_write,
        args=(ORCHESTRATOR_ADDR, f"PRINT: {encoded}"), daemon=True
    )
    writer_thread.start()


def invoke(tool_name: str, **kwargs: Any) -> Any:
    # Prepare message
    msg_json = json.dumps([tool_name, kwargs])
    msg_b64 = base64.b64encode(msg_json.encode()).decode()
    message = f"INVOKE: {msg_b64}"

    # Send message to orchestrator
    writer_thread = threading.Thread(
        target=handle_write,
        args=(ORCHESTRATOR_ADDR, message),
        daemon=True
    )
    writer_thread.start()

    response = response_queue.get()
    return json.loads(base64.b64decode(response).decode())


def start_listener():
    """Starts the server and listens for connections until shutdown."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(listener_addr)
    server.listen(5)
    # Set timeout so we can periodically check for shutdown
    server.settimeout(1.0)
    print(f"[WORKER] listening on {listener_ip}:{listener_port}")

    while True:
        try:
            client_socket, addr = server.accept()
        except socket.timeout:
            continue  # Check the shutdown event again
        threading.Thread(
            target=handle_client,
            args=(client_socket, addr),
            daemon=True
        ).start()


def handle_client(client_socket, address):
    """Handles incoming messages from a connected client."""
    print(f"[WORKER] New connection from {address}")

    try:
        while True:
            message = client_socket.recv(1024).decode()
            if not message:
                break

            if message.startswith("RESPONSE:"):
                payload = message.split(":", 1)[1].strip()
                try:
                    response_queue.put(payload)
                except Exception as e:
                    raise TypeError(
                        f"Expected int result, got: {payload}") from e

            print(f"[WORKER] Received {message} from {address}")
    except ConnectionResetError:
        print(f"[-] Connection lost with {address}")
    finally:
        client_socket.close()


def handle_write(addr, message):
    try:
        print("attempting to write to", addr)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(addr)
        client_socket.send(message.encode())
        print("worker msg:", message)
    except Exception as e:
        print(f"[-] Error sending message to {addr}: {e}")
    finally:
        client_socket.close()


def main() -> None:
    # Start listener thread
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()

    # Send IP of listener
    # writer_thread = threading.Thread(
    #     target=handle_write,
    #     args=(ORCHESTRATOR_ADDR, f"INFO {listener_ip}:{listener_port}"),
    #     daemon=True
    # )
    # writer_thread.start()

    # Get script from environment variable
    script_b64 = os.environ.get("SCRIPT", "")
    script = base64.b64decode(script_b64).decode() if script_b64 else ""
    if not script.strip():
        writer_thread = threading.Thread(
            target=handle_write,
            args=(ORCHESTRATOR_ADDR, "PRINT: No script provided in $SCRIPT."),
            daemon=True
        )
        writer_thread.start()
        sys.exit(1)

    # Execute script
    try:
        code = compile(
            ast.parse(script, mode="exec"),
            filename="<script>",
            mode="exec"
        )
        exec(code, globals())
    except Exception as e:
        writer_thread = threading.Thread(
            target=handle_write,
            args=(ORCHESTRATOR_ADDR, f"PRINT: Error executing script: {e}"),
            daemon=True
        )
        writer_thread.start()

    # Send termination message
    writer_thread = threading.Thread(
        target=handle_write,
        args=(ORCHESTRATOR_ADDR, "TERMINATE"),
        daemon=True
    )
    writer_thread.start()

    # Signal the listener to shutdown and wait for it to finish.
    writer_thread.join()
    listener_thread.join()


if __name__ == "__main__":
    main()
