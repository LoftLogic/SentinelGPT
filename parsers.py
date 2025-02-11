import ast
import re
from langchain.schema import AIMessage

def parse_text_to_python(text: str) -> str:
    """
    Extracts Python code enclosed in triple backticks (optionally marked with 'python')
    from the provided text.
    """
    pattern = r"```(?:python)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        code = match.group(1)
    else:
        # Fallback: assume the entire text is code.
        code = text
    # Remove any leading or trailing whitespace.
    code = code.strip()
    print("stripped code, pre-AST:\n", code)
    return code


def parse_python_code_to_ast(text: str | AIMessage) -> ast.Module:
    """
    Extracts Python code enclosed in triple backticks (optionally marked with 'python')
    from the provided text and returns its AST. If no code block is found,
    the entire text is assumed to be Python code.
    """
    if isinstance (text, AIMessage):
        text = text.content
    code = parse_text_to_python(text)
    syntax_tree = ast.parse(code)
    print("AST DUMP:\n", ast.dump(syntax_tree, indent=4))
    return syntax_tree

def parse_ai_message_to_ast(ai_message: AIMessage) -> ast.Module:
    """
    Given an AIMessage from LangChain, extracts Python code from its content and
    returns the corresponding AST.
    """
    return parse_python_code_to_ast(ai_message.content)