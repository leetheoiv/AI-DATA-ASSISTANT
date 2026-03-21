import os
import json
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1])) # Ensure the repo root is on sys.path so sibling packages like `prompt_templates` can be imported
from langchain_core.messages import HumanMessage

from agent import AIAgent
from context import DatasetContext
from structured_outputs import SupervisorOutput, SupervisorAction
from prompt_templates.supervisor import SYSTEM_PROMPT

"""
agents/supervisor.py

The Supervisor — the user-facing entry point of the system.

Responsibilities:
  1. Clarify vague or incomplete questions
  2. Improve the question (weave in column names + business rules)
  3. Hand off to the planner

Uses AIAgent directly — no separate wrapper class needed.
"""




def run_supervisor(
    user_message: str,
    context: DatasetContext,
    conversation_history: list = None,
) -> SupervisorOutput:
    """
    Process a user message and return a SupervisorOutput.
 
    Check result.action to know what happened:
      SupervisorAction.CLARIFY → show result.clarifying_question to the user
      SupervisorAction.HANDOFF → pass result.improved_question to the planner
    """
    agent = AIAgent(model="gpt-4o-mini")
    agent.create_agent(
        model_name="supervisor",
        system_prompt=SYSTEM_PROMPT,
        response_format=SupervisorOutput,
        context_schema=DatasetContext,
        temperature=0.3 # low temperature for more deterministic output from the supervisor
    )
 
    messages = [
        *(conversation_history or []),
        HumanMessage(content=user_message),
    ]
 
    raw = agent.send(messages=messages, context=context)
 
    return _parse(raw)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Output parsing
# ─────────────────────────────────────────────────────────────────────────────
 
def _parse(raw) -> SupervisorOutput:
    """
    Parse create_agent's return value into a SupervisorOutput.
 
    Per the LangChain docs, when response_format is set the parsed
    Pydantic object is returned in result["structured_response"].
    """
 
    # Case 1: already a SupervisorOutput
    if isinstance(raw, SupervisorOutput):
        return raw
 
    # Case 2: dict — check structured_response first (correct location per docs)
    if isinstance(raw, dict):
        structured = raw.get("structured_response")
        if isinstance(structured, SupervisorOutput):
            return structured
 
        # Fallback — last message content (previous behaviour)
        if "messages" in raw and raw["messages"]:
            last = raw["messages"][-1]
            content = getattr(last, "content", None)
            if content:
                raise ValueError(
                    f"structured_response not found in result.\n"
                    f"Got messages[-1].content instead:\n{content}\n\n"
                    f"Check that response_format is being passed correctly "
                    f"to create_agent and that agent.send() returns the full "
                    f"result dict without modification."
                )
 
    raise ValueError(
        f"Could not find structured_response in result.\n"
        f"Result type: {type(raw)}\n"
        f"Result: {raw}"
    )