import socket
import subprocess
import threading

host = "0.0.0.0"  # Listen on all interfaces
port = 6000       # Port to receive messages from Docker clients

# Start a socket server to receive IPs from clients
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(5)

print("Waiting for clients to send their server IPs...")

# Function to handle incoming client connections
def handle_client(conn, addr):
    data = conn.recv(1024).decode()
    print(f"Received client server details: {data}")
    conn.close()

# Run the client listener in a separate thread
def start_listener():
    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

listener_thread = threading.Thread(target=start_listener, daemon=True)
listener_thread.start()

# Function to spawn a new Docker client
def spawn_client():
    docker_command = [
        "docker", "run", "--rm",
        "--network", "bridge",  # Ensures clients get unique IPs
        "my_docker_client"
    ]
    subprocess.Popen(docker_command)

# Spawn multiple clients dynamically
for _ in range(3):  # Change 3 to any number of clients you need
    spawn_client()
