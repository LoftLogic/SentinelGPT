import os
import json

TOOLS_DIR = os.path.join(os.getcwd(), "tools")
PERMISSIONS_FILE = os.path.join(os.getcwd(), "tool_permissions.json")


def get_tool_path(tool_name: str) -> str:
    """Return the path to the tool file given its name (without .py)."""
    path = os.path.join(TOOLS_DIR, f"{tool_name}.py")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Tool {tool_name} not found at {path}.")
    return path


def load_tool_code(tool_name: str) -> str:
    path = get_tool_path(tool_name)
    with open(path, "r") as f:
        return f.read()


def load_permissions() -> dict:
    with open(PERMISSIONS_FILE, "r") as f:
        return json.load(f)


def get_tool_permissions(tool_name: str) -> dict:
    perms = load_permissions()
    # Permissions keys are the filenames, e.g. "arithmetic.py"
    return perms.get(f"{tool_name}.py", {})
