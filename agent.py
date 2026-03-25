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
        
        # set openai client key for REST fallback
        self._openai.api_key = self.key

        # model name and langchain llm resolution
        self.model = model
    
        try:
            self.llm = ChatOpenAI(api_key=self.key, model_name=self.model, temperature=self.temperature,timeout=timeout,max_tokens=max_tokens,verbose=True,max_retries=max_retries)
        except Exception:
            # keep None and let create_agent decide fallback
            self.llm = None

        # agent instance (created by create_agent)
        self.agent = None

    def add_system(self, content: str):
        self.messages.append({"role": "system", "content": content})

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def set_messages(self, messages: list[dict]):
        if not isinstance(messages, list):
            raise ValueError("messages must be a list of {'role','content'} dicts")
        self.messages = list(messages)

    def clear_messages(self):
        self.messages = []

    def _messages_to_prompt(self, messages: list[dict]) -> str:
        """Convert list of {'role','content'} dicts to a single string prompt for LLM input."""
        parts = []
        for m in messages:
            role = m.get("role", "user").capitalize()
            parts.append(f"{role}: {m.get('content','')}")
        return "\n\n".join(parts)
        
        
    def create_agent(self,model_name=None,tools: list=[],middleware: list=[],temperature=0.6,response_format=None, system_prompt: str | None = None,context_schema: str | None = None):
        """
        Create a LangChain agent. Prefer explicit llm, then module-level self.llm, then api_key -> construct.
        Raises ValueError if no usable LLM is available.
        """
        self.agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=system_prompt,
            response_format=response_format,
            context_schema=context_schema,
            # checkpointer=InMemorySaver(),
            name=model_name,
            middleware=middleware
        )
        logger.info(f"Created agent with model {self.model} and tools {[t.name for t in tools]}")
        return self.agent
    
    def chat(self,messages: list[dict] = []):
        """
        messages: optional list of dicts with keys 'role' and 'content'.
        If None, uses messages expected by your LangChain agent's internal state (if any).
        """
        if self.agent is None:
            raise ValueError("Agent not created. Call create_agent() first.")
        msgs = messages or []
        if not isinstance(msgs, list):
            raise ValueError("messages must be a list of {'role','content'} dicts")
        response = self.agent.invoke({'messages': msgs})
        return response
        
    def send(self ,messages: list[dict] | None = None, context=None,config=None) -> str:
        """
        Send a turn. Default behavior:
         - use the created LangChain agent if available (agent.invoke({'messages': msgs}))
         - else use the resolved LangChain LLM (self.llm) by flattening messages to a prompt
         - else fall back to OpenAI REST client (self._openai.ChatCompletion)
        response_format: 'text'|'raw'|'full'|'json'
        """
        
        msgs = messages if messages is not None else list(self.messages)
        if not isinstance(msgs, list):
            raise ValueError("messages must be a list of {'role','content'} dicts")

        # prefer explicit agent
        if self.agent is not None:
            resp = self.agent.invoke({"messages": msgs},context=context,config=config)
            # DEBUG: log the raw agent response
            print(resp)
            
            return resp
            

    
        
    
    
