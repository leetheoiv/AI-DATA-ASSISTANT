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
from dotenv import load_dotenv


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
        AIAgent is a class that interacts with the OpenAI API to generate responses based on prompts. It handles API key management, request configuration, and response parsing. 
        The agent can be configured with different models, temperature settings, and other parameters to customize the behavior of the generated responses.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini", temperature=0.6,timeout: int = 30,max_tokens=4000,max_retries=3):
        load_dotenv("config/.env")
  
        self.timeout = timeout
        self.temperature = temperature
        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise ValueError("OPENAI_API_KEY not set")
        
        
            

    
        
    
    
