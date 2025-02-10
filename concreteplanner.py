from langchain_openai import ChatOpenAI

from registeredtool import RegisteredTool

from langchain.prompts.chat import ChatPromptTemplate

from prompts.concrete_templates import generate_concrete_template

from langchain_core.output_parsers import JsonOutputParser

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

import ast


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
    
    def __init__(self):
        self.planner_llm: ChatOpenAI = ChatOpenAI(model="gpt-4o", temperature=0.0)
        self.planner_template: ChatPromptTemplate = generate_concrete_template() # We may end up not using this
        self.planner_parser = JsonOutputParser()
        
        self.plangen_chain = self.planner_template | self.planner_llm | self.planner_parser

    def adapt_plan(self, tool_grouping: dict[str, set[RegisteredTool]], abs_tools: list[dict], abs_plan: ast.Module):
        """
        Adapts an abstract plan, creating a concrete executable equivelent
        Starts by matching each abstract developed tool with an existing concrete tool
        Then reformats the abstract plan to use the selected concrete tools
        """
        for abs_tool in abs_tools:
            selected_tools = self.__match_tool(tool_grouping, abs_tool) # Return value/type of __match_tool() currently unknown

    
    def __match_tool(self, tool_grouping: dict[str, set[RegisteredTool]], abstract_tool: dict):
        """
        Matches abstract tools to concrete tools
        
        params:
            tool_grouping- map from provider to tools
        Note: An abstract tools has: name, description, input, output,
        
        return:
            TBD
        """
        if "description" not in abstract_tool:
            raise ValueError("Abstract Tool has no description")
        # THRESHOLD: float = 0.80
        # NOTE: Lift to orchestrator later
        embeddings = OpenAIEmbeddings()
        for group in tool_grouping:
            docs = []
            tool_index_mapping = { tool: idx for idx, tool in enumerate(tool_grouping[group]) }
            for tool in tool_grouping[group]:
                index = tool_index_mapping.get(tool)
                docs.append(Document(page_content=tool.get_description(), metadata={"index": index}))
            faiss_store = FAISS.from_documents(docs, embeddings)
            retrieved_docs = faiss_store.similarity_search(abstract_tool["description"])
            # Write code that converts the docs list into a list of numerical simaliarity scores between abstract_tool["description"] and the docs
            print(f"Results for {group}:")
            for doc in retrieved_docs:
                print((list(tool_index_mapping.keys())[doc.metadata['index']]).get_name())