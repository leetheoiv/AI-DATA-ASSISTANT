#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Import Libraries                                                                                                                                                                   
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
from dataclasses import dataclass
import openai
import os
import json
import time 
import logging
import langchain
from langchain_openai import ChatOpenAI 
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from langchain.messages import SystemMessage, HumanMessage, AIMessage

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Open Log                                                                                                                                                                
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "agent.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)   

logger = logging.getLogger(__name__)

def write_log(message: str):
    filepath = os.path.join(LOG_DIR, "agent.log")
    with open(filepath, "a") as f:
        f.write(f"{time.asctime()} {message}\n")
    



#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Load AI Key                                                                                                                                                                 
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
load_dotenv()  # Load environment variables from .env file



#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Agent Class                                                                                                                                                                
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# How to make a response: 
#   response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=5)
#   response_text = response.choices[0].text.strip()
#   print(response_text)

class AIAgent:
    """
    LangChain-first AI agent . Prefer passing an explicit `llm` (langchain.OpenAI).

    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini", temperature=0.6,timeout: int = 30,max_tokens=4000,max_retries=3):
        load_dotenv("config/.env")
        import openai as _openai


        self._openai = _openai
        self.timeout = timeout
        self.temperature = temperature
        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise ValueError("OPENAI_API_KEY not set")
        
        
            

    
        
    
    
