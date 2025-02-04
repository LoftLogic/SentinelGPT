from planner import Planner
from toolselector import ToolSelector
from registeredtool import RegisteredTool


class Orchestrator:
    """
    Represents the central manager of the LLM system.
    In charge of executing tools in an isolated space and delegating responsibilities to other system components.
    """
    def __init__(self):
        # Map from app names to the RegisteredApp
        self.tools: dict[str, RegisteredTool] = {}
        self.planner: Planner = Planner()
        self.tool_selector: ToolSelector = ToolSelector()
        
        
    """
    Adds a tool to the state
    
    param:
        RegisteredTool to add
    """
    def add_tool(self, tool: RegisteredTool):
        self.tools.put(tool.name())
    
    
    """
    Removes a tool from the state
    
    param:
        RegisteredTool to remove
    """
    def remove_tool(self, tool: RegisteredTool):
        self.tools.pop(tool.name, None)
        
        
    """
    Removes a tool from the state by name
    
    param:
        Name of the RegisteredTool to remove
    """
    def remove_tool_by_name(self, name: str):
        self.tools.pop(name, None)