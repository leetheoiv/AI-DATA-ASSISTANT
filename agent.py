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
from langchain import OpenAI
from langchain.agents import create_agent
from langchain.agents import AgentType
from langchain.agents import initialize_agent
from langchain.agents import load_tools
from langchain.tools import Tool
from langchain import PromptTemplate
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from langchain.messages import SystemMessage, HumanMessage, AIMessage

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Load AI Key                                                                                                                                                                 
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
load_dotenv()  # Load environment variables from .env file

AI_client = OpenAI(os.getenv("OPENAI_API_KEY"))

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

    def __init__(self, api_key: str | None = None, model: str = "gpt-3.5-turbo", timeout: int = 30,llm=None, tools: list=[]):
        load_dotenv()
        import openai as _openai
        from langchain import OpenAI as LC_OpenAI

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
        self.model_name = model
        self.llm = llm or globals().get("AI_client")
        if self.llm is None:
            # attempt to construct a LangChain OpenAI instance
            try:
                self.llm = LC_OpenAI(openai_api_key=self.key, model_name=self.model_name, temperature=0.0)
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
        parts = []
        for m in messages:
            role = m.get("role", "user").capitalize()
            parts.append(f"{role}: {m.get('content','')}")
        return "\n\n".join(parts)
        
        
    def create_agent(self,temperature=0.6,response_format=None, system_prompt: str | None = None):
        """
        Create a LangChain agent. Prefer explicit llm, then module-level self.llm, then api_key -> construct.
        Raises ValueError if no usable LLM is available.
        """
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=SystemMessage(system_prompt) if system_prompt else None,
            temperature=temperature,
            response_format=response_format,
            context_schema=None,
            checkpointer=InMemorySaver(keep_last=10)
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
            if response_format == "raw":
                return resp
            try:
                return getattr(resp, "output_text", None) or (resp.get("output_text") if isinstance(resp, dict) else None) or str(resp)
            except Exception:
                return str(resp)

        # no agent: prefer LangChain LLM
        use_lc = (use_langchain if use_langchain is not None else True) and (self.llm is not None)
        if use_lc and self.llm is not None:
            prompt = self._messages_to_prompt(msgs)
            try:
                lc_out = self.llm(prompt)
                assistant_text = str(lc_out)
            except TypeError:
                try:
                    gen = self.llm.generate([prompt])
                    assistant_text = ""
                    if hasattr(gen, "generations"):
                        for r in gen.generations:
                            for g in r:
                                assistant_text += getattr(g, "text", "") or str(g)
                    else:
                        assistant_text = str(gen)
                except Exception as e:
                    raise RuntimeError("LLM call failed") from e
            raw_resp = lc_out if 'lc_out' in locals() else gen
            if response_format == "text":
                return assistant_text
            if response_format == "raw":
                return raw_resp
            if response_format == "full":
                return {"text": assistant_text, "raw": raw_resp}
            if response_format == "json":
                try:
                    return json.loads(assistant_text)
                except Exception as e:
                    raise ValueError(f"Failed to parse assistant text as JSON: {e}\nassistant_text={assistant_text!r}") from e
            return assistant_text

        # final fallback: OpenAI REST ChatCompletion
        params = {"model": self.model_name, "messages": msgs, "temperature": temperature, "timeout": self.timeout}
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        resp = self._openai.ChatCompletion.create(**params)
        try:
            assistant_text = resp["choices"][0]["message"]["content"]
        except Exception:
            try:
                choice = resp.choices[0]
                assistant_text = getattr(choice, "message", {}).get("content", "") or getattr(choice, "text", "") or str(resp)
            except Exception:
                assistant_text = str(resp)
        if response_format == "text":
            return assistant_text
        if response_format == "raw":
            return resp
        if response_format == "full":
            return {"text": assistant_text, "raw": resp}
        if response_format == "json":
            try:
                return json.loads(assistant_text)
            except Exception as e:
                raise ValueError(f"Failed to parse assistant text as JSON: {e}\nassistant_text={assistant_text!r}") from e
        return assistant_text
    
    
