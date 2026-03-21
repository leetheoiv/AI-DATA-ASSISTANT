import os
import json
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1])) # Ensure the repo root is on sys.path so sibling packages like `prompt_templates` can be imported
from langchain_core.messages import HumanMessage

from agent import AIAgent
from context import DatasetContext
from structured_outputs import PlannerOutput, PlannerAction
from prompt_templates.planner import SYSTEM_PROMPT
from tools.dataset_tools import get_dataset_structure, get_dataset_statistics
from langchain.agents.middleware import ModelRequest,dynamic_prompt
from langchain_core.prompts import PromptTemplate
"""
agents/planner.py

The Planner agent — receives an improved question from the supervisor
and produces a structured analysis plan.

Responsibilities:
  1. Inspect the real dataset using get_dataset_structure and
     get_dataset_statistics to ground the plan in actual data
  2. Produce a step-by-step analysis plan assigning each step
     to the correct specialist agent
  3. Ask a clarifying question back to the supervisor if something
     critical cannot be resolved by inspecting the data

Uses the ReAct pattern — the agent reasons, calls tools to inspect
the data, observes results, then produces the plan.
"""

from langchain_core.messages import HumanMessage




# Tools the planner has access to
PLANNER_TOOLS = [
    get_dataset_structure,
    get_dataset_statistics,
]

# @dynamic_prompt
def planner_prompt(request: ModelRequest) -> str:
    file_path = request.runtime.context.file_path
    dataset_description = request.runtime.context.dataset_description
    column_descriptions = request.runtime.context.column_descriptions
    business_rules = request.runtime.context.business_rules
    known_issues = request.runtime.context.known_issues

def run_planner(
    improved_question: str,
    context: DatasetContext,
    conversation_history: list = None,
) -> PlannerOutput:
    """
    Produce an analysis plan for the given question.

    The planner will:
      1. Call get_dataset_structure to confirm columns and types
      2. Call get_dataset_statistics to understand distributions
      3. Produce a PlannerOutput with either a full plan or a
         clarifying question if something critical is ambiguous

    Args:
        improved_question:    The refined question from the supervisor.
        context:              Dataset context — file path, column descriptions,
                              business rules. Also injected into the agent.
        conversation_history: Optional prior messages for multi-turn
                              conversations.

    Returns:
        PlannerOutput with action == PLAN or action == CLARIFY
    """
    system_prompt = SYSTEM_PROMPT.format(
        file_path=context.file_path,
        dataset_description=context.dataset_description,
        column_descriptions=context.column_descriptions,
        business_rules=context.business_rules,
        known_issues=context.known_issues,
    )
    
    agent = AIAgent(model="gpt-4o-mini") # gpt-3.5-turbo won't work here because it doesn't support tools + structured output simultaneously.
    agent.create_agent(
        model_name="planner",
        system_prompt=system_prompt,
        response_format=PlannerOutput,
        context_schema=DatasetContext,
        tools=PLANNER_TOOLS
        # middleware=[planner_prompt],    # dynamic prompt reads context at runtime
    )

    messages = [
        *(conversation_history or []),
        HumanMessage(content=improved_question),
    ]

    raw = agent.send(
        messages=messages,
        context=context
    )

  
    return _parse(raw)


# ─────────────────────────────────────────────────────────────────────────────
#  Output parsing
# ─────────────────────────────────────────────────────────────────────────────

def _parse(raw) -> PlannerOutput:
    """
    Parse create_agent's return value into a PlannerOutput.
    Per LangChain docs, structured_response holds the parsed Pydantic object.
    """
    
    # Case 1: already a PlannerOutput
    if isinstance(raw, PlannerOutput):
        return raw

    # Case 2: dict — structured_response is the correct location
    if isinstance(raw, dict):
        structured = raw.get("structured_response")
        if isinstance(structured, PlannerOutput):
            return structured

        # Helpful error if structured_response is missing
        if "messages" in raw and raw["messages"]:
            last = raw["messages"][-1]
            content = getattr(last, "content", None)
            raise ValueError(
                f"structured_response not found in planner result.\n"
                f"Last message content:\n{content}\n\n"
                f"Check that response_format=PlannerOutput is being passed "
                f"correctly to create_agent."
            )

    raise ValueError(
        f"Could not find structured_response in planner result.\n"
        f"Result type: {type(raw)}\n"
        f"Result: {raw}"
    )