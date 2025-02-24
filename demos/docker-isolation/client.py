import socket
import os
import time

# Get the Docker container's IP
hostname = os.popen("hostname -I").read().strip()
server_port = 5000  # Each client starts its own server on port 5000

# Notify the main Python process about the new server's IP
host_machine_ip = "192.168.1.100"  # Change to the host machine IP
host_machine_port = 6000  # Host process listening port

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host_machine_ip, host_machine_port))
client_socket.send(f"{hostname}:{server_port}".encode())
client_socket.close()

# Start a simple TCP server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((hostname, server_port))
server_socket.listen(5)

print(f"Client's server running on {hostname}:{server_port}")

while True:
    conn, addr = server_socket.accept()
    data = conn.recv(1024).decode()
    print(f"Received: {data} from {addr}")
    conn.send(f"Message received: {data}".encode())  # Respond to the sender
    conn.close()
