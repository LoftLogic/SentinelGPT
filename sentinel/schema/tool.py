from typing import Type

from pydantic import BaseModel
from langchain.tools import StructuredTool


class Tool(BaseModel):
    name: str
    id: str
    description: str
    clearances: set[str]
    provider: str
    args_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    source_code: str


class ToolCreator:
    @classmethod
    def from_structured_tool(cls, tool: StructuredTool) -> Tool:
        raise NotImplementedError

# TODO:
# check out https://github.com/letta-ai/letta/blob/main/letta/schemas/tool.py
