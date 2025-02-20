#!/usr/bin/env python
import sys
import json
import traceback


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("Expected a single JSON argument.")
        payload = json.loads(sys.argv[1])
        tool_code = payload["code"]
        function_name = payload["function"]
        args = payload["args"]
        kwargs = payload["kwargs"]
        # Create a fresh namespace.
        namespace = {}
        # Optionally, pre-populate namespace with allowed constants, e.g., FILE_PATH.
        namespace["FILE_PATH"] = "/data/file.txt"  # In container, the file is mounted here.
        # Execute the tool code.
        exec(tool_code, namespace)
        if function_name not in namespace:
            raise ValueError(f"Function {function_name} not defined in provided code.")
        func = namespace[function_name]
        result = func(*args, **kwargs)
        print(json.dumps({"result": result}))
    except Exception as e:
        print(json.dumps({"error": str(e), "trace": traceback.format_exc()}))


if __name__ == "__main__":
    main()
