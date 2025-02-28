from langchain_openai import ChatOpenAI

from registeredtool import RegisteredTool

from langchain.prompts.chat import ChatPromptTemplate

from prompts.concrete_templates import generate_concrete_template

from langchain_core.output_parsers import JsonOutputParser

from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

import ast
import astor

from typing import Callable

import inspect

import sentinel


class ToolCallTransformer(ast.NodeTransformer):
    def __init__(self, tool_functions):
        self.tool_functions = tool_functions

    def visit_Call(self, node):
        # First, process the children nodes.
        self.generic_visit(node)
        # Check if the function call is a call to one of our tool functions.
        if isinstance(node.func, ast.Name) and node.func.id in self.tool_functions:
            # Replace call: tool1(arg1, arg2, ...) with invoke("tool1", arg1, arg2, ...)
            new_args = [ast.Constant(value=node.func.id)]
            new_args.extend(node.args)
            new_node = ast.Call(
                func=ast.Name(id="invoke", ctx=ast.Load()),
                args=new_args,
                keywords=node.keywords
            )
            return ast.copy_location(new_node, node)
        return node


"""
Expiremental

Ideation:
    - Recieves an abstract plan
    - Recieves a list of available tools
    - Tries to "match" tools
    - Runs an LLM session in parallel with each available app group
        - It is critical that the session cannot be interfered with by another apps description if its from a different group
"""


class ConcretePlanner():
    """
    Represents a planner that implements the generated abstract plan.
    Has the following responsibilities:
    - "Match" a corresponding abstract tool to its concrete equivelent
    - If multiple options are available, and are in seperate groups, run them all cuncurrently
    - If a match fails, then...
        - Idea 1: Use a "plan adpter", which can interpret commands from one and rely them in the form of bools or enums to the other 
            - This would avoid more attack surfaces
    """

    def __init__(self, debug: bool = True):
        self.planner_llm: ChatOpenAI = ChatOpenAI(model="Qwen/Qwen2.5-72B-Instruct", temperature=0.0,
                                                  openai_api_base="http://localhost:8000/v1")
        # We may end up not using this
        self.planner_template: ChatPromptTemplate = generate_concrete_template()
        self.planner_parser = JsonOutputParser()
        self.debug = debug

        self.plangen_chain = self.planner_template | self.planner_llm | self.planner_parser

    def adapt_plan(self, tools: set[RegisteredTool], abs_tools: list[dict], abs_code: str):
        """
        Adapts an abstract plan, creating a concrete executable equivelent
        Starts by matching each abstract developed tool with an existing concrete tool
        Then reformats the abstract plan to use the selected concrete tools
        """
        matches: dict[str, RegisteredTool] = {}
        new_matches: dict[str, sentinel.schema.concrete.Tool] = {}
        for abs_tool in abs_tools:
            # Return value/type of __match_tool() currently unknown
            selected_tool = self.__match_tool(tools, abs_tool)
            matches[abs_tool['name']] = selected_tool
            print(
                f"Matched tool for {abs_tool['name']}: args_schema: {selected_tool.tool.args_schema}, output_schema: {selected_tool.tool.output_schema}, source_code: {type(selected_tool.get_function_source())}\n")

            # Replace the function name in the source code
            sc = selected_tool.get_function_source().replace(
                selected_tool.get_func().__name__, "main")

            new_matches[abs_tool['name']] = sentinel.schema.CustomTool(
                name=selected_tool.get_name(),
                # func_name=selected_tool.get_func().__name__,
                description=selected_tool.get_description(),
                clearances={"basic"},
                permissions=set(),
                provider=selected_tool.provider,
                args_schema=selected_tool.tool.args_schema,
                output_schema=selected_tool.tool.output_schema,
                # source_code=selected_tool.get_function_source()
                source_code=sc,
            )

        if self.debug:
            for abs_name in matches:
                print(
                    f"Matched tool for {abs_name}: {matches[abs_name].get_name()}\n")
                print("\n")

        # Parse the script into an AST.
        tree = ast.parse(abs_code)
        transformer = ToolCallTransformer(
            list(map(lambda tool: tool["name"], abs_tools)))
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        comp_code = astor.to_source(new_tree)
        comp_code = comp_code + "\n" + "display(main())"

        code = self.__match_func(abs_code, matches)
        # cheat with the tools for now, since we hard-code the ast transform
        plan = sentinel.schema.AbstractPlan(script=comp_code, abs_tools=[])
        if self.debug:
            print(f"Abstract Code:\n {abs_code}")
            print(f"Compiled Code:\n {comp_code}")
            print(f"Code:\n {code}")

        # exec_scope = {}
        # exec(code, exec_scope)
        # if "main" in exec_scope:
        #     result = exec_scope["main"]()
        #     if self.debug:
        #         print(f"RESULTS:\n", result)
        # else:
        #     if self.debug:
        #         print(f"Results NOT FOUND")
        # if self.debug:
        #     print("\n")

        exec_sandbox = sentinel.execute.PlanOrchestrator(
            plan=plan,
            tools=new_matches
        )
        exec_sandbox.launch()
        exec_sandbox.join()

    def __match_tool(self, tools: set[RegisteredTool], abstract_tool: dict) -> RegisteredTool:
        """
        Matches abstract tools to concrete tools.

        Parameters:
            tool_grouping: A dictionary mapping a provider (e.g., "Microsoft") to a set of RegisteredTool objects.
                        Each RegisteredTool represents a concrete LLM application with attributes such as name,
                        description, function, and provider.
            abstract_tool: A dictionary representing an abstract tool. This should include keys such as 'name',
                        'description', 'input', and 'output'. The matching is done based on the tool's name and description.

        Returns:
            A dictionary mapping each provider group (string) to a list of matched RegisteredTool objects.
            The list is expected to be ordered from the most to the least similar tool. In the current implementation,
            it will usually be only one tool that gets matched.
        """

        if "description" not in abstract_tool:
            raise ValueError("Abstract Tool has no description")

        embeddings = OpenAIEmbeddings()  # for now; should change to local model later!!!
        # embeddings = OpenAIEmbeddings(
        #     model="sentence-transformers/all-MiniLM-L6-v2", openai_api_base="http://localhost:8001/v1")
        # embeddings = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-MiniLM-L6-v2")
        # embeddings = NormalizedHuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-MiniLM-L6-v2")

        if self.debug and "name" in abstract_tool:
            print("\n-------------------------")
            print("Matching: " + abstract_tool["name"])
            print("-------------------------\n")

        names: dict = {}

        docs = []

        for tool in tools:
            names[tool.get_name()] = tool

            doc = Document(page_content=(tool.get_name(
            ) + ": " + tool.get_description() + tool.input_str() + tool.output_str()))
            docs.append(doc)

        faiss_store = FAISS.from_documents(docs, embeddings)

        compstr: str = abstract_tool["name"] + \
            ": " + abstract_tool["description"]
        compstr += "\nInputs:"
        for name, details in abstract_tool["inputs"].items():
            try:
                compstr += f" {name} ({details['type']}): {details['description']}, "
            except Exception as e:
                print("Input parse error: ", e)

        compstr += f"\nOutput ({abstract_tool['output']['type']}: {abstract_tool['output']['description']})"

        retrieved_docs_with_scores = faiss_store.similarity_search_with_score(
            compstr)

        best = float('inf')
        for doc, score in retrieved_docs_with_scores:
            best = min(score, best)
            if self.debug:
                print(
                    f"Tool: {doc.page_content.split(':')[0]}, Similarity Score: {score:.4f}")

        chosen_tools = list(filter(
            lambda item: len(item) > 1 and item[1] < 0.6 and abs(
                item[1] - best) < 0.03,
            retrieved_docs_with_scores
        ))

        best_doc: tuple = max(chosen_tools, key=lambda tool: names[tool[0].page_content.split(
            ":")[0]].get_clearance_level())

        if self.debug:
            if not best_doc:
                print("No tools chosen.")
            else:
                print(f"Chosen tool: {best_doc}")
            print("\n")

        return names[best_doc[0].page_content.split(":")[0]]

    def __match_func(self, code: str, matches: dict[str, RegisteredTool]) -> str:
        """
        Matches functions for each group

        Returns:
            The code with concrete functions in place of abstract
        """
        def find_keyword(text: str, keywords: set[str]) -> str | None:
            """
            Searches for keywords in the given text.

            :param text: The string to search within.
            :param keywords: A set of keywords to look for.
            :return: The first keyword found or None if none are found.
            """
            for word in keywords:
                if word in text:
                    return word
            return None

        # Map abstract tool's function name to its tool
        function_map: dict[str, str] = {}

        for abs_tool in matches:
            function_map[abs_tool.replace(" ", "")] = abs_tool

        functions: set[str] = set(function_map.keys())
        used_functions: set[Callable] = set()
        code: list[str] = code.splitlines()
        new_code: str = ""
        conc_tool: RegisteredTool = None
        for line in code:
            found: str | None = find_keyword(line, functions)
            if found:
                abs_tool_name = function_map[found]
                if abs_tool_name not in matches:
                    raise ValueError("Abs tool not found in matches")
                conc_tool = matches[abs_tool_name]
                if self.debug:
                    print("Concrete tool found:", conc_tool.get_name())
                new_code += line.replace(found,
                                         conc_tool.get_func().__name__) + "\n"
            else:
                new_code += line + "\n"

            if conc_tool and conc_tool.get_func() not in used_functions:
                used_functions.add(conc_tool.get_func())
                new_code = inspect.getsource(
                    conc_tool.get_func()) + "\n" + new_code

        return new_code.lstrip()
