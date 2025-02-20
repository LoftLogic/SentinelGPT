import os
import ast
import sys
from typing import Any


def write_message(msg: str) -> None:
    # sys.stdout.write("ELLO GOVNA \0")
    sys.stdout.write(msg + "\0")
    sys.stdout.flush()


def read_message() -> str:
    # Read bytes until a null terminator is encountered.
    buf = bytearray()
    while True:
        ch = sys.stdin.buffer.read(1)
        if not ch:
            break
        if ch == b'\0':
            break
        buf.extend(ch)
    return buf.decode('utf-8')


def invoke(tool_name: str, *args: Any) -> int:
    message = f"INVOKE: {tool_name} {args}"
    write_message(message)
    response_line = read_message()
    if response_line.startswith("RESPONSE:"):
        payload = response_line.split(":", 1)[1].strip()
        try:
            return int(payload)
        except Exception as e:
            raise TypeError(f"Expected int result, got: {payload}") from e
    raise RuntimeError("No valid response received.")


def main() -> None:
    script = os.environ.get("SCRIPT", "")
    if not script.strip():
        write_message("PRINT: No script provided in $SCRIPT.")
        sys.exit(1)
    write_message("PRINT: Running script:")
    write_message(f"PRINT: {script}")
    try:
        code = compile(ast.parse(script, mode="exec"),
                       filename="<script>", mode="exec")
        exec(code, globals())
    except Exception as e:
        write_message(f"PRINT: Error executing script: {e}")


if __name__ == "__main__":
    main()
