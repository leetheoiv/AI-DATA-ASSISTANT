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
from app.settings import AGENT_API_KEY
import instructor

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
class AIAgent:
    """"
    AIAgent is a general-purpose wrapper around the OpenAI API, designed to manage conversation state and support various interaction patterns:
  - Plain text responses
  - Structured outputs via Pydantic models
  - Tool use with function calls and result integration"""
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        system_prompt: str = None,
        tools: list = None,
        temperature: float = 0.6,
        timeout: int = 30,
        max_tokens: int = 4000,
        max_retries: int = 3,
    ):
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools
        self.temperature = temperature
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Conversation state
        self.input_list = []
        self.history = None       # previous_response_id (string or None)
        self.tokens_used = 0

        self.client = OpenAI(api_key=api_key, max_retries=max_retries)

    def reset(self):
        """Clear conversation state between sessions."""
        self.input_list = []
        self.history = None

    def _append_user(self, user_prompt: str):
        if user_prompt is not None:
            self.input_list.append({"role": "user", "content": user_prompt})

    def _base_params(self) -> dict:
        """Shared params across all API calls."""
        return dict(
            model=self.model,
            instructions=self.system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            previous_response_id=self.history,
        )

    def _finalize(self, raw) -> None:
        """Track tokens and update history after every call."""
        self.tokens_used += raw.usage.total_tokens
        self.history = raw.id

    def ask(self, user_prompt: str = None, response_model=None, tool_map: dict = None) -> tuple:
        """
        Single entry point for all call types:
          - Plain text:            ask(user_prompt="...")
          - Structured output:     ask(user_prompt="...", response_model=MyModel)
          - Tool use:              ask(user_prompt="...", tool_map={"fn_name": fn})
        """
        self._append_user(user_prompt)

        raw = parsed = content = None # Initialize all to None for consistent return type, even if some calls don't populate them

        if tool_map:
            raw, content = self._ask_with_tools(tool_map)
        elif response_model:
            raw, parsed, content = self._ask_structured(response_model)
        else:
            raw, content = self._ask_plain()

        self._finalize(raw)
        return raw, parsed, content

    # ── Private call handlers ─────────────────────────────────────────────────

    def _ask_plain(self) -> tuple:
        """Plain text response without parsing or tools."""
        raw = self.client.responses.create(
            input=self.input_list,
            timeout=self.timeout,
            **self._base_params()
        )
        return raw, raw.output[0].content[0].text

    def _ask_structured(self, response_model) -> tuple:
        """Parse response into structured format using provided Pydantic model."""
        raw = self.client.responses.parse(
            input=self.input_list,
            text_format=response_model,
            timeout=self.timeout,
            **self._base_params()
        )
        parsed = raw.output[0].content[0].parsed if raw.output else None
        content = raw.output[0].content[0].text if raw.output else None
        return raw, parsed, content

    def _ask_with_tools(self, tool_map: dict) -> tuple:
        """Handle tool calls in a loop until the model produces a final answer."""
        params = self._base_params()

        raw = self.client.responses.create(
            input=self.input_list,
            tools=self.tools,
            max_tool_calls=3,
            **params
        )

        # Append model's tool call turn, execute tools, append results
        self.input_list += raw.output
        for item in raw.output:
            if item.type == "function_call":
                args = json.loads(item.arguments)
                result = tool_map.get(item.name, lambda **k: f"Tool {item.name} not found")(**args)
                self.input_list.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": str(result),
                })

        # Second call — model writes final answer with tool results in context
        raw = self.client.responses.create(
            input=self.input_list,
            tools=self.tools,
            **params
        )
        return raw, raw.output_text



