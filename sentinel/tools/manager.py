from typing import Any, Dict, List

from pathlib import Path
import logging
import json

from ..schema import ConcreteToolBase, CustomTool, LangChainTool, Permission

logger = logging.getLogger(__name__)


class ToolManager():
    manifest_path: Path
    tools: List[ConcreteToolBase]

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        self.tools: List[ConcreteToolBase] = []
        self.load_manifest()

    def load_manifest(self) -> None:
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest file {self.manifest_path} not found."
            )

        with open(self.manifest_path, "r") as f:
            data = json.load(f)

        self.tools = []
        for item in data:
            try:
                tool = self._instantiate_tool(item)
                self.tools.append(tool)
            except Exception as e:
                logger.warning(
                    f"Error instantiating tool {item['name']}: {e}"
                )

    def get_by_name(self, name: str) -> ConcreteToolBase:
        # yeah yeah, I know.
        for tool in self.tools:
            if tool.name == name:
                return tool

        raise ValueError(f"Tool {name} not found.")

    def _instantiate_tool(self, item: Dict[str, Any]) -> ConcreteToolBase:
        # TODO: should maybe make schema or ORM for manifest file . . .
        tool_type = item["tool_type"]

        name = item["name"]
        clearances = item["clearances"]
        permissions = set(map(Permission, item["permissions"]))

        if tool_type == "custom":
            provider = item["provider"]
            description = item["description"]
            tool_path = self.manifest_path.parent / item["path"]

            with open(tool_path, "r") as f:
                source_code = f.read()

            return CustomTool(
                name=name,
                provider=provider,
                description=description,
                clearances=clearances,
                permissions=permissions,
                source_code=source_code,
            )
        elif tool_type == "langchain":
            return LangChainTool(
                name=name,
                provider="LangChain Community",
                clearances=clearances,
                permissions=permissions,
                function_name=item["function_name"],
            )
        else:
            raise ValueError(f"Unknown tool type: {tool_type}")
