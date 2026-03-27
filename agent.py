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
from pydantic import BaseModel
import requests

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
        self.input_list = [] 
        self.tokens_used = 0

        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise ValueError("OPENAI_API_KEY not set")
        
        # Create OpenAI client with API Key
        self.client = OpenAI(api_key=self.key)

        
    def ask(self, user_prompt: str,use_tools=False,tool_map=None,use_structured_response=False) -> str:
        """
            Generate a response from the agent based on user input.

            Args:
                user_input (str): The input prompt from the user.
                use_tools (bool): Whether to allow the agent to use tools for generating the response. If tools are used then structured response is not needed as tools already uses it in its response.
                use_structured_response (bool): Whether to format the response in a structured way (e.g., JSON). This is useful for easier parsing of the response.

            use_tools and use_structured_response cannot be true at the same time as tools already uses structured response in its response.

            Returns:
                str: The generated response from the agent.
        """

        # Agent configuration
        response = None
        self.input_list.append({"role":"user","content":user_prompt})
        # Used if tools are enabled and use_structured_response is not enabled
        if use_tools == True and use_structured_response == False and tool_map is not None:
            response = self.client.responses.create(
                input=self.input_list,
                model=self.model,
                instructions=self.system_prompt,
                tools=self.tools,
                temperature=self.temperature,
                timeout=self.timeout,
                max_output_tokens=self.max_tokens,
                max_tool_calls=3,
                previous_response_id=self.history[-1] if self.history else None
            )

            # Add the models reasoning to the input list immediately so that it can be used in the next response if needed. This is important for tool calls as the model needs to know why it is calling the tool and what information it needs to get from the tool.
            has_tool_calls = False
            
            for item in response.output:
                if item.type == "function_call":
                    tool_name = item.name
                    has_tool_calls = True
                    # Execute your actual python function
                    args_dict = json.loads(item.arguments)
                    # Look up the function and unpack the dictionary as keyword arguments
                    if tool_name in tool_map:
                        # The ** unpacking handles whatever keys are inside args_dict
                        result = tool_map[tool_name](**args_dict) 
                    else:
                        result = f"Error: Tool {tool_name} not found."

                    # 5. Append the specific 'function_call_output' type
                    self.input_list.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": str(result),
                    })

        # Used if structured response is enabled and tools are not enabled
        elif use_structured_response == True and use_tools == False:
            response = self.client.responses.parse(
                input=self.input_list,
                model=self.model,
                instructions=self.system_prompt,
                temperature=self.temperature,
                timeout=self.timeout,
                max_output_tokens=self.max_tokens,
                max_tool_calls=3,
                text_format=self.response_format,
                previous_response_id=self.history[-1] if self.history else None
            )
        else:
            response = self.client.responses.create(
                input=[{"role":"user","content":user_prompt}],
                model=self.model,
                instructions=self.system_prompt,
                temperature=self.temperature,
                timeout=self.timeout,
                max_output_tokens=self.max_tokens,
                previous_response_id=self.history[-1] if self.history else None
            )

        try:
            
            self.tokens_used += response.usage.total_tokens # add total tokens to agent for tracking
            if len(self.history) > 1: 
                self.history.pop(0) # Keep only the last responses in history to manage context

            self.history.append(response.id) # Add the response ID to history for context management in future calls

            paresed_response = response.output[0].content[0].parsed if response.output and response.output[0].content and response.output[0].content[0].parsed else None
            return response,paresed_response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            print(f"[ERROR] in agent.py ask function: Error generating response: {e}")
            return f"[ERROR] in agent.py ask function: Error generating response: {e}"
        



# class CalendarEvent(BaseModel):
#     name: str
#     date: str
#     participants: list[str]

# client = AIAgent(response_format=CalendarEvent)
# response,parsed_response = client.ask(
#     user_prompt=

#              "Alice and Bob are going to a science fair on Friday.",
 
#     use_structured_response=True
# )

# print("Raw Response:", response)
# print("-----------------------------------")
# print("Parsed Response:", parsed_response)
