from planner import Planner
from abstractplanner import AbstractPlanner
from toolselector import ToolSelector
from registeredtool import RegisteredTool
from concreteplanner import ConcretePlanner

from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from astpretty import pprint

from parsers import parse_ai_message_to_ast


class Orchestrator:
    """
    Represents the central manager of the LLM system.
    In charge of executing tools in an isolated space and delegating responsibilities to other system components.
    """

    def __init__(self, debug: bool = True):
        # Map from app names to the RegisteredApp
        self.tools: set[RegisteredTool] = set()
        self.tool_blind_planner: AbstractPlanner = AbstractPlanner()
        self.concrete_planner: ConcretePlanner = ConcretePlanner()
        self.tool_selector: ToolSelector = ToolSelector()
        self.debug = debug
        self.llm: ChatOpenAI = ChatOpenAI(model='gpt-4o', temperature=0.0)

    def add_tool(self, tool: RegisteredTool):
        """
        Adds a tool to the state

        param:
            RegisteredTool to add

        returns:
            self for easy callback
        """
        self.tools.add(tool)
        if (self.debug):
            print(f"{tool.get_name()} added")
        return self

    def remove_tool(self, tool: RegisteredTool):
        """
        Removes a tool from the state

        param:
            RegisteredTool to remove

        returns:
            self for easy callback
        """
        self.tools.pop(tool.get_name(), None)
        print(f"{tool.get_name()} removed")
        return self

    def remove_tool_by_name(self, name: str):
        """
        Removes a tool from the state by name

        params:
            - Name of the RegisteredTool to remove

        returns:
            self for easy callback
        """
        self.tools.pop(name, None)
        print(f"{name} removed")
        return self

    def run_query(self, query: str) -> str:
        """
        Runs the query. Uses relevant apps sequentially, synthesizes outputs and returns a final response to the user

        Returns:
        - A final output for the user

        Steps:
        - First, synthesizes the output rules
        - Second, choosing which tools should be selected, then grouping them by provider.
        - Third, an sequential execution plan involving tools is created
        - Fourth, the plan is executed and its outputs are gathered
        - Fifth, the outputs are conformed to the correct type
        - Sixth, the conformed outputs are synthesized and shown to the user
        """
        if self.debug:
            print(f"Running {query}...")
        grouping: dict[str, set[str]] = self.__selection_step(query)

        # If not apps are expected to be used
        """
        if not grouping:
            messages = [SystemMessage(content="You are a helpful assistant."), HumanMessage(content=query)]
            response = self.llm.invoke(messages)
            return response.content
        """
        self.__planning_step(query, grouping)

    def __selection_step(self, query: str) -> dict[str, set[str]]:
        """
        Performs the selection step (step 2). Filters out tools based on the query and groups them by provider.

        Returns:
            A mapping of providers to its corresponding set of tool names
        """        
        if self.debug:
            print("Filtering and grouping tools...\n\n")
        
        similarities: dict[RegisteredTool, float] = self.tool_selector.get_similarities(query, self.tools)
        
        if self.debug:
            print("\nSimilarity scores: \n")
            for tool, score in similarities.items():
                print(f"{tool.get_name()} has a simaliarity of {score}")

        tools: set[RegisteredTool] = self.tool_selector.filter_tools(similarities)

        if self.debug:
            print("\nSelected Tools:")
            for tool in tools:
                print(tool.get_name())

        grouping: dict[str, set[RegisteredTool]] = self.tool_selector.group_tools(tools)
        if self.debug:
            for provider in grouping:
                print(f"Tools in {provider}:")
                for tool in grouping[provider]:
                    print(tool.get_name())
                print("\n")
        return grouping

    def __planning_step(self, query: str, grouping: dict[str, set[RegisteredTool]]):
        """
        Performs the planning step (step 3). Plans the tools accordingly to their group.

        Params:
            - A dictionary mapping providers to a set of correlated tool names

        Returns:
            - A sequential plan of execution for the apps
        """

        abstract_tools = self.tool_blind_planner.generate_abstract_tools(query)
        if self.debug:
            print("Generating a plan of execution... \n\n")
            print("Abstract tool signatures:\n")
            print(abstract_tools)
        plan = self.tool_blind_planner.generate_abstract_plan(query, abstract_tools)
        plan = parse_ai_message_to_ast(plan)
        if self.debug:
            self.__print_plan(plan)
        self.concrete_planner.adapt_plan(grouping, abstract_tools['apps'])        
        return plan

    def __execute_plan(self, plan: dict):
        """
        Executes the given plan. Gives its outputs.
        Fourth step in the process
        """
        pass

    def __conform_types(self):
        """
        Conform the outputs from tools to types
        Fifth Step in the process
        """
        pass

    def __finalize(self, conformed_outputs, synthesis_rule) -> str:
        """
        Use synthesis rules and type conformed output to generate a final output for the user
        Sixth and final step in the process.
        """
        final_prompt = ""
        return (self.invoke(final_prompt).content)

    def __print_plan(self, plan: dict):
        """
        Purely for debugging/logging.
        """
        if not self.debug:
            raise RuntimeError("Not in debug mode")
        steps = 1
        print("Tools: ")
        print(plan)