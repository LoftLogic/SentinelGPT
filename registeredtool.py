from langchain.tools import StructuredTool
from clearence import Clearence
from typing import Callable

class RegisteredTool():
    """
    Represents an app containing a tool that is registered in the orcherstrator
    Composes with StructuredTool
    State also includes clearance level and tool provider
    """
    def __init__(self, name: str, func, description: str, provider: str = "Unaffiliated", inputs: list[dict] = None, output: dict = None,\
        clearance: Clearence = Clearence.LOW):
        self.tool: StructuredTool = StructuredTool.from_function(name=name, func=func, description=description)
        self.provider: str = provider
        self.clearence: Clearence = clearance
        if not inputs:
            self.inputs = []
        else:
            for input in inputs:
                if not "type" in input or not "description" in input:
                    raise ValueError("Inputs must each have a type and description")
                if input["type"] not in ("str", "int", "float", "list[str]", "list[int]", "list[float]", "dict"):
                    raise ValueError("Unrecognized type")
            self.inputs: list[dict] = inputs
        if not output:
            self.output = {}
        else:
            if not "type" in output or not "description" in output:
                raise ValueError("Output must be a dict with type and description")
            self.output: dict = output

    def get_name(self) -> str:
        """
        Returns the name of the field.
        Equivelent to self.tool.name
        """
        return self.tool.name
    
    
    
    def get_func(self) -> Callable:
        """
        Returns the func of the field.
        Equivelent to self.tool.func
        """
        return self.tool.func
    
    
    def get_description(self) -> str:
        """
        Returns the description of the field.
        Equivelent to self.tool.description
        """
        return self.tool.description
    
    def input_str(self) -> str:
        """
        Returns strings rep of input
        """
        if not self.inputs:
            return ""
        result = "\nInputs:"
        for name, details in self.inputs.items():
            try:
                result += f" {name} ({details['type']}): {details['description']}, " 
            except Exception as e:
                print("ERROR:", e)
                continue
            
    def output_str(self) -> str:
        """
        """
        if not self.output:
            return ""
        result = "\nOutput"
        try:
            result += f"({self.output['type']}): {self.output['description']}"
        except Exception as e:
            print("Error:", e)
        return result