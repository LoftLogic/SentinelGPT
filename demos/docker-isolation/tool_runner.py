import os
import json
import sys
from typing import Any, List


def main() -> None:
    tool_code: str = os.environ.get("TOOL_CODE", "")
    args_json: str = os.environ.get("ARGS", "[]")
    try:
        args: List[Any] = json.loads(args_json)
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
        result: Any = local_ns["main_tool"](*args)
        if not isinstance(result, int):
            raise TypeError(
                f"Expected int result, got {result} (type {type(result)})")
        sys.stdout.write(f"{result}\0")
        sys.stdout.flush()
    except Exception as e:
        print("Error executing tool code:", e, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
