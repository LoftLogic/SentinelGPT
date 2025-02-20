#!/usr/bin/env python
import os
import json
import traceback


def main():
    try:
        payload_json = os.environ.get("TOOL_PAYLOAD", "")
        if not payload_json:
            raise ValueError("Expected TOOL_PAYLOAD environment variable.")
        payload = json.loads(payload_json)
        code = payload["code"]
        function_name = payload["function"]
        args = payload["args"]
        kwargs = payload["kwargs"]
        # Create a fresh namespace.
        namespace = {}
        # Inject allowed constants.
        namespace["FILE_PATH"] = "/data/file.txt"
        # Execute only the provided code.
        exec(code, namespace)
        if function_name not in namespace:
            raise ValueError(
                f"Function {function_name} not defined in provided code.")
        func = namespace[function_name]
        result = func(*args, **kwargs)
        print(json.dumps({"result": result}))
    except Exception as e:
        print(json.dumps({"error": str(e), "trace": traceback.format_exc()}))


if __name__ == "__main__":
    main()
