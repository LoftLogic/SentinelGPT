from langchain.tools import Tool as LangchainTool


def generate_langchain_tool_source(
    tool: LangchainTool
) -> str:
    tool_name = tool.__class__.__name__
    import_stmt = f"from langchain.tools import {tool_name}\n"

    # TODO: borrow from https://github.com/letta-ai/letta/blob/a1a2dd44f57ff868d46e7e4bc517e4d299185771/letta/functions/helpers.py#L104

    source_code = None
    return source_code
