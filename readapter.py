from enum import Enum
from langchain_openai import ChatOpenAI
from abstractplanner import AbstractPlanner


class Status(Enum):
    CLEAR = 0,
    ERROR = 1,
    # Other Potential Ideas: Too Modular, Not Modular Enough, Too many params, Not enough prams, Param type mismatch, Output type mismatch

class Readapter():
    """
    If a concrete one to one matching fails, this is used in place.
    """
    def __init__(self, abstract_planner: AbstractPlanner):
        self.abstract_planner = abstract_planner
        self.llm: ChatOpenAI = ChatOpenAI(model="gpt-4o", temperature=0.0)