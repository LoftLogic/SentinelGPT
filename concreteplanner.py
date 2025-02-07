from langchain_openai import ChatOpenAI

from registeredtool import RegisteredTool

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
    
    def __init__(self, tools, tool_grouping: dict):
        #self.tool_grouping: dict[str: set[]]
        pass
    
    def adapt_plan(self, plan: dict):
        for abs_tool in plan:
            self.__match_tool(abs_tool)
    
    def __match_tool(self, abstract_tool):
        pass