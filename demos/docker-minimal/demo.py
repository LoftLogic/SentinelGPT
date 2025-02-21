#!/usr/bin/env python3
import socket
import threading
import json
import time
import docker


def ipc_server(sock_addr):
    # Create a UNIX socket using the abstract namespace.
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_addr)
    server.listen(1)
    print(f"A: Listening on abstract socket {repr(sock_addr)}")
    conn, _ = server.accept()
    print("A: Connection accepted")
    # Send a JSON message (newline-delimited) to the container.
    msg = {"msg": "hello world", "value": 5}
    conn.sendall((json.dumps(msg) + "\n").encode('utf-8'))
    print(f"A: Sent message {msg}")
    # Read the response from the container over the socket.
    response_line = b""
    while not response_line.endswith(b"\n"):
        chunk = conn.recv(1024)
        if not chunk:
            break
        response_line += chunk
    if response_line:
        response = json.loads(response_line.decode('utf-8').strip())
        print(f"A: Received IPC response {response}")
    conn.close()
    server.close()


def main():
    # Define an abstract socket address (leading '\0' means abstract namespace)
    sock_addr = "\0demo_sock"

    # Start the IPC server in a separate thread.
    server_thread = threading.Thread(target=ipc_server, args=(sock_addr,))
    server_thread.start()

    client = docker.from_env()

    # Build the Docker image (Dockerfile and d_script.py should be in the current directory).
    print("A: Building Docker image ...")
    image, build_logs = client.images.build(path=".", tag="my-docker-ipc-demo")
    for chunk in build_logs:
        if 'stream' in chunk:
            print(chunk['stream'].strip(), end='')

    # Run container D using the built image.
    # Use network_mode="host" so that both the host and container share the same abstract namespace.
    print("A: Starting container D ...")
    container = client.containers.run(
        "my-docker-ipc-demo",
        network_mode="host",
        detach=True,
        remove=True  # Remove container after it finishes.
    )

    # Wait for the container to finish.
    result = container.wait()
    # Retrieve and parse the container's output (which is expected to be a JSON string).
    logs = container.logs().decode('utf-8').strip()
    try:
        parsed_output = json.loads(logs)
        print("A: Parsed container output:", parsed_output)
    except Exception as e:
        print("A: Failed to parse container output as JSON:")
        print(logs)
        print(e)

    server_thread.join()


if __name__ == "__main__":
    main()
