from langchain.tools import StructuredTool
from clearence import Clearence

class RegisteredTool():
    """
    Represents an app containing a tool that is registered in the orcherstrator
    Composes with StructuredTool
    State also includes clearance level and tool provider
    """
    def __init__(self, name: str, func, description: str, provider: str = "Unaffiliated", clearance: Clearence = Clearence.LOW):
        self.tool = StructuredTool.from_function(name=name, func=func, description=description)
        self.provider = provider
        self.clearence = clearance
    
    
    """
    Returns the name of the field.
    Equivelent to self.tool.name
    """
    def get_name(self) -> str:
        return self.tool.name
    
    
    """
    Returns the func of the field.
    Equivelent to self.tool.func
    """
    def get_func(self):
        return self.tool.func
    
    """
    Returns the description of the field.
    Equivelent to self.tool.description
    """
    def get_description(self) -> str:
        return self.tool.description