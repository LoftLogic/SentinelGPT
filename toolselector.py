from langchain.tools import StructuredTool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import numpy as np


def cosine_similarity(vec1, vec2) -> float:
    """
    Given two vectors, return its cosine simaliarity
    """
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class ToolSelector:
    """
    Represents a selection of tools
    
    Stores tools, and their associated provider as state
    
    Has the ability to add more tools and retrieve tools relevant to the user query grouped by provider
    """
    
    def __init__(self):
        # A mapping of providers (str) to all tools under them.
        self.providers: dict[str, list[StructuredTool]] = {}
        # A general mapping of tools and their associated names
        self.tools: dict[str, StructuredTool] = {}
        
    def add_tool(self, name: str, func, description: str, provider: str = "Default"):
        """
        Adds a tool to the state
        
        params: 
            name, function and description of the tool, as well as its provider
            
        effect:
            Creates a StructuredTool from name, function, and description, and adds it to a dict with provider as the key
        """
        tool = StructuredTool.from_function(name=name, func=func, description=description)
        self.providers[provider] = self.providers.get(provider, []) + [tool]
        self.tools[tool.name] = tool
            
    
    def get_simaliarites(self, query: str) -> dict[str, float]:
        """
        Uses vector embeddings to get a numerical representation of simalirities between each tools description and the user prompt

        params:
            Relevant User query/task
            Example Query: I would like to buy some donuts

        returns:
            A dictionary mapping tool names to their similarity scores
        """
        result: dict[str, int] = {}
        embedding = OpenAIEmbeddings()
        query_embedding = embedding.embed_query(query)
                    
        for tool in self.tools.values():
            description_embedding = embedding.embed_query(tool.description)
            similarity = cosine_similarity(query_embedding, description_embedding)
            result[tool.name] = similarity
        
        return result
    
    def filter_tools(self, similarities: dict[str, float], threshold = 0.83) -> list[str]:
        """
        Filters out the tools based on their similarity scores, removing any that don't meet a certain threshold
        
        params:
            similarities: The mapping between tool names and their numerical simalirity to the user query
            Threshold: The minimum similairty to meet to not be removed
        
        return:
            A list of tool names that meet the threshold
        """
        return list({name: similarity for name, similarity in similarities.items() if similarity > threshold}.keys())
        
    def group_tools(self, names: list[str]) -> dict[str, str]:
        """
        Groups a list of tools into a dictionary based on their providers
        
        params:
            names: List of names of the tools to use
            
        return:
            A dictionary mapping providers and their associated 
            
        raises:
            A value error if it recieves a name not present fields (the tool name wasn't added yet)
        """
        
        

    


        
        
