#!/usr/bin/env python3
import socket
import json
import time
import os

# Use abstract namespace: leading null byte indicates an abstract socket.
sock_addr = "\0demo_sock"

# Repeatedly try connecting until successful.
while True:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(sock_addr)
        break
    except Exception:
        time.sleep(0.1)

# Read newline-delimited JSON from the socket.
data = b""
while not data.endswith(b"\n"):
    chunk = s.recv(1024)
    if not chunk:
        break
    data += chunk

if data:
    msg = json.loads(data.decode('utf-8').strip())
    # Compute the result by adding 20 to the integer value.
    result_value = msg.get("value", 0) + 20
    response = {"msg": "result", "value": result_value}
    # Send the response back over the socket.
    s.sendall((json.dumps(response) + "\n").encode('utf-8'))
s.close()

# Output the computed result as JSON (and nothing else)
print(json.dumps(response))
