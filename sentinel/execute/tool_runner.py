# TODO: clean up this code

import os
import json
import sys
import base64
from typing import Any, List


def main() -> None:
    tool_code_b64: str = os.environ.get("TOOL_CODE", "")
    args_json_b64: str = os.environ.get("ARGS", "[]")
    tool_code: str = base64.b64decode(tool_code_b64).decode()
    args_json: str = base64.b64decode(args_json_b64).decode()
    try:
        args: dict[str, Any] = json.loads(args_json)
    except Exception as e:
        print("Error decoding ARGS:", e, flush=True)
        sys.exit(1)
    if not tool_code.strip():
        print("No TOOL_CODE provided.", flush=True)
        sys.exit(1)
    try:
        local_ns = {}
        exec(tool_code, {}, local_ns)
        if "main_tool" not in local_ns:
            print("Tool code must define 'main_tool'.", flush=True)
            sys.exit(1)
        result: Any = local_ns["main_tool"](**args)
        if not isinstance(result, int):
            raise TypeError(
                f"Expected int result, got {result} (type {type(result)})")
        sys.stdout.write(f"{result}")
        sys.stdout.flush()
    except Exception as e:
        print("Error executing tool code:", e, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
