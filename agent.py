#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Import Libraries                                                                                                                                                                   
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import openai
import os
import json
import time 
import logging
import langchain
from langchain import OpenAI
from langchain.agents import create_csv_agent
from langchain.agents import AgentType
from langchain.agents import initialize_agent
from langchain.agents import load_tools
from langchain.tools import Tool
from langchain import PromptTemplate
from dotenv import load_dotenv
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Load AI Key                                                                                                                                                                 
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
load_dotenv()  # Load environment variables from .env file


openai.api_key = os.getenv("OPENAI_API_KEY")