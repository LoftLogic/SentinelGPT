import docker
import threading
import re
import json
import select
from typing import Any, Tuple


class SimplePipe:
    def __init__(self, sock):
        # Wrap the underlying socket with a file-like object.
        self.f = sock.makefile('rwb', buffering=0)

    def send(self, data: str) -> None:
        # Append a null terminator.
        self.f.write(data.encode('utf-8') + b'\0')
        self.f.flush()

    def recv(self) -> str:
        buf = bytearray()
        while True:
            # Use select to avoid hanging indefinitely.
            r, _, _ = select.select([self.f.fileno()], [], [], 5)
            if not r:
                print("[SimplePipe] Timeout waiting for data")
                break
            ch = self.f.read(1)
            if not ch:
                break
            if ch == b'\0':
                break
            buf.extend(ch)
        message = buf.decode('utf-8')
        print(f"[SimplePipe] Received raw message: '{message}'")
        return message


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


def handle_invoke(message: str, pipe: SimplePipe) -> None:
    print(f"[Orchestrator] Received INVOKE message: '{message}'")
    m = re.match(r"INVOKE:\s+(\S+)\s+(.*)", message)
    if not m:
        pipe.send("RESPONSE: ERROR: Malformed INVOKE.")
        return
    tool = m.group(1)
    args_str = m.group(2)
    try:
        args = eval(args_str)
        if not isinstance(args, tuple):
            args = (args,)
    except Exception as e:
        pipe.send(f"RESPONSE: ERROR: Couldn't parse arguments: {args_str}")
        return
    print(f"[Orchestrator] Invoking tool '{tool}' with args {args}")
    if tool not in tool_codes:
        pipe.send("RESPONSE: ERROR: Unknown tool")
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
            remove=True
        )
        tool_container.wait()
        output = tool_container.logs().decode('utf-8').strip()
        print(f"[Orchestrator] Raw tool container output: '{output}'")

        result = int(output)
        response = f"RESPONSE: {result}"
    except Exception as e:
        response = f"RESPONSE: ERROR: {str(e)}"
        print(f"[Orchestrator] Error invoking tool '{tool}': {e}")
    pipe.send(response)
    print(f"[Orchestrator] Sent response: '{response}'")


def read_loop(pipe: SimplePipe) -> None:
    while True:
        msg = pipe.recv()
        if not msg:
            break
        print(f"[Orchestrator] Received message: '{msg}'")
        if msg.startswith("PRINT:"):
            print(msg[len("PRINT:"):].strip())
        elif msg.startswith("INVOKE:"):
            handle_invoke(msg, pipe)
    print("[Orchestrator] Finished reading worker messages.")


def orchestrator_main() -> None:
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
        detach=True
    )
    print(f"[Orchestrator] Worker container started: {container.short_id}")

    sock = container.attach_socket(
        params={"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1},
        ws=False
    )
    sock._sock.setblocking(True)
    pipe = SimplePipe(sock._sock)

    t = threading.Thread(target=read_loop, args=(pipe,), daemon=True)
    t.start()

    container.wait()
    print("[Orchestrator] Worker container finished.")
    container.remove()
    print("[Orchestrator] Worker container removed.")


if __name__ == "__main__":
    orchestrator_main()
