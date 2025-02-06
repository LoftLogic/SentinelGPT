from planner import Planner
from abstractplanner import AbstractPlanner
from toolselector import ToolSelector
from registeredtool import RegisteredTool
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage



class Orchestrator:
    """
    Represents the central manager of the LLM system.
    In charge of executing tools in an isolated space and delegating responsibilities to other system components.
    """
    def __init__(self, debug: bool = True):
        # Map from app names to the RegisteredApp
        self.tools: dict[str, RegisteredTool] = {}
        self.planner: Planner = Planner()
        self.tool_blind_planner: Planner = AbstractPlanner()
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
        self.tools[tool.get_name()] = tool
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
        self.__synthesize_rules(query)
        grouping: dict[str, set[str]] = self.__selection_step(query)
        
        # If not apps are expected to be used
        """
        if not grouping:
            messages = [SystemMessage(content="You are a helpful assistant."), HumanMessage(content=query)]
            response = self.llm.invoke(messages)
            return response.content
        """
        
        self.__planning_step(query, grouping)
    
    def __synthesize_rules(self, query: str):
        """
        Performs the synthesis step (step 1). Generates synthesis rules for the program to follow.
        NOTE: We might end up removing this
        """
        print("Synthesizing rules for ouput...\n\n")
        
    
    def __selection_step(self, query: str) -> dict[str, set[str]]:
        """
        Performs the selection step (step 2). Filters out tools based on the query and groups them by provider.
        
        Returns:
            A mapping of providers to its corresponding set of tool names
        
        Raises:
            ValueError if a name is generated from tool_selector but isn't registered in self.tools
        """
        tools = list(self.tools.values())
        print("Filtering and grouping tools...\n\n")
        similarities: dict[str, float] = self.tool_selector.get_similarities(query, tools)
        if self.debug:
            print("\nSimilarity scores: \n")
            for name, score in similarities.items():
                print(f"{name} has a simaliarity of {score}")
                
        names: set[str] = self.tool_selector.filter_tools(similarities)
        
        if self.debug:
            print("\nSelected Tools:")   
        tools: list[RegisteredTool] = []    
        
        for name in names:
            if (self.tools[name]):
                tools.append(self.tools[name])
            else:
                raise ValueError("Name not stored in state")
            if self.debug:
                print(name)
                
        grouping: dict[str, set[str]] = self.tool_selector.group_tools(tools)
        if self.debug:
            for provider in grouping:
                print(f"Tools in {provider}:")
                for tool in grouping[provider]:
                    print(tool)
                print("\n")
        return grouping
            
    def __planning_step(self, query: str, grouping: dict[str, set[str]]):
        """
        Performs the planning step (step 3). Plans the tools accordingly to their group.
        
        Params:
            - A dictionary mapping providers to a set of correlated tool names
            
        Returns:
            - A sequential plan of execution for the apps
        """
        print("Generating a plan of execution... \n\n")
        tools_ls = [self.tools[name] for names in grouping.values() for name in names]
        tool_info: str = ""
        for tool in tools_ls:
            tool_info += "Name: " + tool.get_name() + ", Description: " + tool.get_description() + "\n"
            
        print("Tool Info:" + "\n" + tool_info)
        plan = self.tool_blind_planner.generate_abstract_tools(query)
        if self.debug:
            self.__print_plan(plan)
            print("plan:", plan)
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
        return(self.invoke(final_prompt).content)
        
    def __print_plan(self, plan: dict):
        """
        Purely for debugging/logging.
        """
        if not self.debug:
            raise RuntimeError("Not in debug mode")
        steps = 1
        for tool in plan["steps"]:
            print("Step:", steps, "\n")
            for key, value in tool.items():
                print(key.upper() + ": ")
                print(value)
            steps += 1