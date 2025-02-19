from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import RedisChatMessageHistory

"""
To be implemented
"""


class Memory:
    """
    Provides context for LLMs.
    Reponsible for saving and retrieving conversation data, summarizing past conversations, and tracking entities.
    """

    def __init__(self, name: str):
        # Expiration for the key
        self.TTL: int = 450
        llm = ChatOpenAI(model="Qwen/Qwen2.5-72B-Instruct", temperature=0.0,
                         openai_api_base="http://localhost:8000/v1")
