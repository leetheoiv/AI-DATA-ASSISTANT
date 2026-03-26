#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Import Libraries                                                                                                                                                                   
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
from dataclasses import dataclass
from openai import OpenAI
import os
import json
import time 
import logging
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

    def __init__(self, system_prompt=None,response_format=None, tools=None ,api_key: str | None = None, model: str = "gpt-4o-mini", temperature=0.6,timeout: int = 30,max_tokens=4000,max_retries=3):
        load_dotenv("config/.env")

        self.model=model
        self.temperature = temperature
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.system_prompt = system_prompt
        self.tools = tools
        self.response_format = response_format
        self.history = []   

        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise ValueError("OPENAI_API_KEY not set")
        
        # Create OpenAI client with API Key
        self.client = OpenAI(api_key=self.key)

        
    def ask(self, user_prompt: str,use_tools=False) -> str:
        """
            Generate a response from the agent based on user input.

            Args:
                user_input (str): The input prompt from the user.
                use_tools (bool): Whether to allow the agent to use tools for generating the response. If tools are used then structured response is not needed as tools already uses it in its response.
            Returns:
                str: The generated response from the agent.
        """
        # Agent configuration
        response = None
        if use_tools == True:
            response = self.client.responses.create(
                input=[{"role":"user","content":user_prompt}],
                model=self.model,
                instructions=self.system_prompt,
                tools=self.tools,
                temperature=self.temperature,
                timeout=self.timeout,
                max_output_tokens=self.max_tokens,
                max_tool_calls=3,
                previous_response_id=self.history[-1] if self.history else None
            )
        else:
            response = self.client.responses.parse(
                input=[{"role":"user","content":user_prompt}],
                model=self.model,
                instructions=self.system_prompt,
                temperature=self.temperature,
                timeout=self.timeout,
                max_output_tokens=self.max_tokens,
                max_tool_calls=3,
                text_format=self.response_format,
                previous_response_id=self.history[-1] if self.history else None
            )

        try:
            print(response)

            if len(self.history) > 2:
                self.history.pop(0) # Keep only the last 2 responses in history to manage context
            self.history.apend(response.id)

            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error while generating a response."
            

agent = AIAgent()
agent.ask("What is the capital of France?")
print('-----------')
print(agent.history)
    
    
