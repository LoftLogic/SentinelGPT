from langchain.tools import StructuredTool
from langchain_openai import OpenAIEmbeddings
from registeredtool import RegisteredTool
import numpy as np

def cosine_similarity(vec1, vec2) -> float:
    """
    Given two vectors, return its cosine simaliarity
    """
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class ToolSelector:
    """
    Manages a collection of tools to use.
    
    Has the following responsibilities:
        - Use a user query to retireve a filtered list of relevant tools
        - Group relevant tools by their provider
    """
    
    def __init__(self):
        self.embedding: OpenAIEmbeddings = OpenAIEmbeddings()
        # self.tools: dict[str, set[str]] = {} Not sure yet if this should be a returned value or a part of state

    
    def get_similarities(self, query: str, tools: set[RegisteredTool]) -> dict[RegisteredTool, float]:
        """
        Uses vector embeddings to get a numerical representation of simalirities between each tools description and the user prompt

        params:
            Relevant User query/task
            - Example Query: I would like to buy some donuts
            List of RegisteredTools to examine

        returns:
            A dictionary mapping tool names to their similarity scores
        """
        # NOTE: In the future, we may want to implement FAISS embedding
        result: dict[str, float] = {}
        query_embedding = self.embedding.embed_query(query)
                    
        for tool in tools:
            description_embedding = self.embedding.embed_query(tool.get_description())
            similarity = cosine_similarity(query_embedding, description_embedding)
            result[tool] = similarity
        
        return result
    
    def filter_tools(self, similarities: dict[str, float], threshold = 0.83) -> set[StructuredTool]:
        """
        Filters out the tools based on their similarity scores, removing any that don't meet a certain threshold. 
        By default, the threshold will be 0.83
        
        params:
            similarities: The mapping between tool names and their numerical simalirity to the user query
            Threshold: The minimum similairty to meet to not be removed
        
        return:
            A list of tool names that meet the threshold
        """
        return set({tool: similarity for tool, similarity in similarities.items() if similarity > threshold}.keys())

        
        
    def group_tools(self, tools: set[RegisteredTool]) -> dict[str, set[RegisteredTool]]:
        """
        Groups a list of tools into a dictionary based on their providers
        
        params:
            names: List of names of the tools to use
            
        return:
            A dictionary mapping providers and their associated tool's
        """
        result: dict[str, set[RegisteredTool]] = {}
        
        for tool in tools:
            result[tool.provider] = result.get(tool.provider, set()).union({tool})
        
        return result
            
        
        
            
        

    


        
        
