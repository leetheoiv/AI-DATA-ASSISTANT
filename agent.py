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
    LangChain-first AI agent wrapper. Prefer passing an explicit `llm` (langchain.OpenAI).
    If none provided, the class will construct one from api_key or use module-level AI_client.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-3.5-turbo", timeout: int = 30, tools: list=[]):
        load_dotenv("config/.env")
        import openai as _openai


        self._openai = _openai
        self.timeout = timeout
        self.key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.key:
            raise ValueError("OPENAI_API_KEY not set")
        
        # set openai client key for REST fallback
        self._openai.api_key = self.key

        # avoid mutable default
        self.tools = list(tools) if tools is not None else []

        # model name and langchain llm resolution
        self.model = model
    
        try:
            self.llm = ChatOpenAI(api_key=self.key, model_name=self.model, temperature=0.6,timeout=timeout,max_tokens=10,verbose=True)
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
        
        
    def create_agent(self,model_name=None,temperature=0.6,response_format=None, system_prompt: str | None = None,context_schema: str | None = None):
        """
        Create a LangChain agent. Prefer explicit llm, then module-level self.llm, then api_key -> construct.
        Raises ValueError if no usable LLM is available.
        """
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            response_format=response_format,
            context_schema=context_schema,
            # checkpointer=InMemorySaver(),
            name=model_name
        )
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
        
    def send(self, messages: list[dict] | None = None, response_format: str = "text", temperature: float = 0.0, max_tokens: int | None = None, use_langchain: bool | None = None):
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
            resp = self.agent.invoke({"messages": msgs})
            
            return resp
            

    
        
    
    
