from langchain_openai import ChatOpenAI

from registeredtool import RegisteredTool

from langchain.prompts.chat import ChatPromptTemplate

from prompts.concrete_templates import generate_concrete_template

from langchain_core.output_parsers import JsonOutputParser

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

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
        self.planner_llm: ChatOpenAI = ChatOpenAI(model="gpt-4o", temperature=0.0)
        self.planner_template: ChatPromptTemplate = generate_concrete_template() # We may end up not using this
        self.planner_parser = JsonOutputParser()
        self.debug = debug
        
        self.plangen_chain = self.planner_template | self.planner_llm | self.planner_parser

    def adapt_plan(self, tool_grouping: dict[str, set[RegisteredTool]], abs_tools: list[dict], abs_code: str):
        """
        Adapts an abstract plan, creating a concrete executable equivelent
        Starts by matching each abstract developed tool with an existing concrete tool
        Then reformats the abstract plan to use the selected concrete tools
        """
        matches: dict[str, dict[str, list[RegisteredTool]]] = {}
        print("Abstract Tool Param:", abs_tools)
        for abs_tool in abs_tools:
            selected_tools = self.__match_tool(tool_grouping, abs_tool) # Return value/type of __match_tool() currently unknown        
            matches[abs_tool['name']] = selected_tools
                
        if self.debug:
            print("Match pure JSON:", str(matches))
            for abs_name in matches:
                print(f"Matched tools for {abs_name}:\n")
                for group, tools in matches[abs_name].items():
                    if len(tools) == 1:
                        print(group + ":", tools[0].get_name())
                    else:
                        print(group, list(map(lambda t: t.get_name(), tools)), sep=":")
                print("\n")            
    
    
    
    def __match_tool(self, tool_grouping: dict[str, set[RegisteredTool]], abstract_tool: dict) -> dict[str, list[RegisteredTool]]:
        """
        Matches abstract tools to concrete tools
        
        params:
            tool_grouping - map from provider to tools
        Note: An abstract tool has: name, description, input, output,
        
        return:
            A mapping of the group to its matched tool(s), in order from most to least simaliar
            In this current implementation, it will usually be only one tool that gets matched
        """
        if "description" not in abstract_tool:
            raise ValueError("Abstract Tool has no description")
        
        # NOTE: Lift to orchestrator later
        embeddings = OpenAIEmbeddings()
    
        if self.debug and "name" in abstract_tool:
            print("\n-------------------------")
            print("Matching: " + abstract_tool["name"])
            print("-------------------------\n")

        matches: dict[str, list[RegisteredTool]] = {}
        
        # NOTE: We need to implement a different type of selection for 'Unaffiliated'
        for group in tool_grouping:
            names: dict = {}
            
            for tool in tool_grouping[group]:
                names[tool.get_name()] = tool
            
            docs = []
            tool_index_mapping = { tool: idx for idx, tool in enumerate(tool_grouping[group]) }
            
            for tool in tool_grouping[group]:
                index = tool_index_mapping.get(tool)
                docs.append(Document(page_content=(tool.get_name() + ": " + tool.get_description()), metadata={"index": index}))
            
            faiss_store = FAISS.from_documents(docs, embeddings)
            
            retrieved_docs_with_scores = faiss_store.similarity_search_with_score(abstract_tool["name"] + ": " + abstract_tool["description"])
            
            if self.debug:
                print(f"Results for {group}:")
                
            best = float('inf')
            for doc, score in retrieved_docs_with_scores:
                tool = list(tool_index_mapping.keys())[doc.metadata['index']]
                best = min(score, best)
                if self.debug:
                    print(f"Tool: {tool.get_name()}, Similarity Score: {score:.4f}")

            chosen_tools = list(filter(lambda item: len(item) > 1 and item[1] < 0.4 and abs(item[1] - best) < 0.03, retrieved_docs_with_scores))
            if self.debug:
                if not chosen_tools:
                    print("No tools chosen.")
                elif len(chosen_tools) == 1:
                    print(f"Chosen tool: {chosen_tools[0]}")
                else:
                    print(f"Chosen tools: {chosen_tools}")
                print("\n")
            for pair in chosen_tools:
                matches[group] = matches.get(group, []) + [names[pair[0].page_content.split(":")[0]]]
                
        return matches
                    
    
    def __match_func(self, code: str, matches: dict[str, dict[str, list[RegisteredTool]]], group):
        """
        Matches functions for each group
        
        Example code:
        def main():
            document_summary: str = DocumentSummarizer(Document_Name="Findings")
            graph_summary: str = GraphSummarizer(Graph_Name="Analysis")
            slideshow_summary: str = SlideshowSummarizer(Slideshow_Name="Results")
            
            combined_summary: str = f"Document Summary:\n{document_summary}\n\nGraph Summary:\n{graph_summary}\n\nSlideshow Summary:\n{slideshow_summary}"
            
            confirmation: str = EmailSender(Email_Address="johndoe@gmail.com", Content=combined_summary)
            return confirmation
        
        Example matches:
            {'Document Summarizer': 
                {'Google Drive': [<registeredtool.RegisteredTool object at 0x7f724eb9f850>], 
                'Microsoft Office': [<registeredtool.RegisteredTool object at 0x7f724eb9eb60>]}, 
            'Graph Summarizer': 
                {'Google Drive': [<registeredtool.RegisteredTool object at 0x7f724eb9fd60>], 
                'Microsoft Office': [<registeredtool.RegisteredTool object at 0x7f724eb9f070>]}, 
            'Slideshow Summarizer': 
                {'Google Drive': [<registeredtool.RegisteredTool object at 0x7f724eb9ee30>], 
                'Microsoft Office': [<registeredtool.RegisteredTool object at 0x7f724eb9f340>]}, 
            'Email Sender': 
                {'Google Drive': [<registeredtool.RegisteredTool object at 0x7f724eb9fe50>], 
                'Microsoft Office': [<registeredtool.RegisteredTool object at 0x7f724eb9f910>]}}
        
        Process:
            Map abs functions to their tool names
            Split the code into lines
            Go through each line, then look for abs functions
            When an abs function is found, get the corresponding concrete tool from matches
        
        TO BE IMPLEMENTED
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
        functions: set[str] = set(function_map.keys())
        for abs_tool in matches:
            function_map[abs_tool.replace(" ", "")] = abs_tool
        
        code: list[str] = code.splitlines()

        for line in code:
            found: str | None = find_keyword(line, functions)
            if found:
                abs_tool_name = function_map[found]
                if abs_tool_name not in matches or group not in matches:
                    raise ValueError("Abs tool not found in matches")
                # For now, we are going to assume each group has one matched tool
                conc_tool = matches[abs_tool_name][group][0]
                line.replace(found, conc_tool.get_name)        
                
        print("New code", str(code))    
        
    def old_match_code(self, tool_grouping: dict[str, set[RegisteredTool]], abstract_tool: dict):
        """
        This is the older version of our match code. Does not display the simaliarities after execution. 
        Not currently used anywhere
        
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