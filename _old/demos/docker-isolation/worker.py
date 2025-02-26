import contextlib
import io
import os
import ast
import queue
import sys
import time
from typing import Any
import socket
import threading
import subprocess

listener_ip = socket.gethostbyname(socket.gethostname())
listener_port = 8080

orchestrator_ip = "172.17.0.1"
orchestrator_port = 65432

response_queue = queue.Queue()


orchestrator_response = ''


def display(data: str) -> None:
    writer_thread = threading.Thread(target=handle_write, args=(
        (orchestrator_ip, orchestrator_port), f"PRINT: {data}"), daemon=True)
    writer_thread.start()


def invoke(tool_name: str, *args: Any) -> int:
    message = f"INVOKE: {tool_name} {args}"

    writer_thread = threading.Thread(target=handle_write, args=(
        (orchestrator_ip, orchestrator_port), message), daemon=True)
    writer_thread.start()

    try:
        orchestrator_response = response_queue.get()
        # Convert payload to int if necessary.
        return int(orchestrator_response)
    except Exception as e:
        raise TypeError(
            f"Expected int result, got: {orchestrator_response}") from e


def start_listener():
    """Starts the server and listens for connections indefinitely."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((listener_ip, listener_port))
    server.listen(5)
    print(f"[WORKER] listening on {listener_ip}:{listener_port}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(
            client_socket, addr), daemon=True).start()


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
        # Create a new socket to send the message
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the specified client
        client_socket.connect((str(addr[0]), int(addr[1])))

        client_socket.send(message.encode())  # Send the message

        print("worker msg:", message)
    except Exception as e:
        print(f"[-] Error sending message to {addr}: {e}")
    finally:
        client_socket.close()  # Close the connection after sending


def main() -> None:

    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()

    # Send IP of listener
    writer_thread = threading.Thread(target=handle_write, args=(
        (orchestrator_ip, orchestrator_port), f"INFO {listener_ip}:{listener_port}"), daemon=True)
    writer_thread.start()

    script = os.environ.get("SCRIPT", "")
    if not script.strip():
        writer_thread = threading.Thread(target=handle_write, args=(
            (orchestrator_ip, orchestrator_port), "PRINT: No script provided in $SCRIPT."), daemon=True)
        writer_thread.start()
        sys.exit(1)

    writer_thread = threading.Thread(target=handle_write, args=(
        (orchestrator_ip, orchestrator_port), "PRINT: Running script:"), daemon=True)
    writer_thread.start()

    writer_thread = threading.Thread(target=handle_write, args=(
        (orchestrator_ip, orchestrator_port), f"PRINT: {script}"), daemon=True)
    writer_thread.start()

    try:
        code = compile(ast.parse(script, mode="exec"),
                       filename="<script>", mode="exec")

        exec(code, globals())
    except Exception as e:
        writer_thread = threading.Thread(target=handle_write, args=(
            (orchestrator_ip, orchestrator_port), f"PRINT: Error executing script: {e}"), daemon=True)
        writer_thread.start()

    writer_thread = threading.Thread(target=handle_write, args=(
        (orchestrator_ip, orchestrator_port), "TERMINATE"), daemon=True)
    writer_thread.start()

    listener_thread.join()


if __name__ == "__main__":
    main()
