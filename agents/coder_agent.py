
"""
agents/coder.py

The Coder agent — receives one AnalysisStep from the plan and
executes it by writing and running pandas code against the dataset.

Uses ReAct pattern:
  1. Reason about what code to write based on the step description
  2. Call run_code to execute it
  3. Observe the result or error
  4. Fix and retry if needed (up to 3 times)
  5. Call format_result to produce a clean summary
  6. Return CoderOutput
"""

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
from structured_outputs.planner_output import AnalysisStep
from tools.dataset_tools import get_dataset_structure, get_dataset_statistics
from langchain_core.prompts import PromptTemplate
from tools.coder_tools import run_code, format_result, load_dataframe
from prompt_templates.coder import CODER_PROMPT_TEMPLATE
from structured_outputs.coder_structured_output import CoderOutput





CODER_TOOLS = [
    get_dataset_structure,
    get_dataset_statistics,
    run_code,
    format_result,
]


def run_coder(
    step: AnalysisStep,
    context: DatasetContext,
    previous_step_results: dict = None,
) -> CoderOutput:
    """
    Execute one analysis step by writing and running pandas code.

    Args:
        step:                 The AnalysisStep to execute.
        context:              Dataset context — file path, columns, business rules.
        previous_step_results: Results from prior steps keyed by step id.
                              The coder reads these when step.depends_on is set.

    Returns:
        CoderOutput with success status, summary, and raw result.
    """
    # Load the dataset into the shared exec scope so run_code can access it
    try:
        load_dataframe(context.file_path)
    except Exception as e:
        return CoderOutput(
            step_id=step.id,
            success=False,
            error=f"Failed to load dataset from {context.file_path}: {e}",
        )

    # Format previous results for prompt injection
    prev_results = previous_step_results or {}
    if prev_results:
        prev_text = "\n".join(
            f"Step {sid} result: {result}"
            for sid, result in prev_results.items()
        )
    else:
        prev_text = "No previous steps completed yet."

    # Build system prompt with all context injected
    system_prompt = CODER_PROMPT_TEMPLATE.format(
        file_path=context.file_path,
        dataset_description=context.dataset_description,
        column_descriptions=context.column_descriptions,
        business_rules=context.business_rules,
        known_issues=context.known_issues,
        step_id=step.id,
        step_title=step.title,
        step_description=step.description,
        step_inputs=step.inputs,
        step_expected_output=step.expected_output,
        step_business_rule_notes=step.business_rule_notes or "None",
        previous_step_results=prev_text,
    )

    agent = AIAgent(model="gpt-4o-mini")
    agent.create_agent(
        model_name="coder",
        system_prompt=system_prompt,
        response_format=CoderOutput,
        tools=CODER_TOOLS,
    )

    # The human message is the step instruction
    message = (
        f"Execute step {step.id}: {step.title}\n"
        f"Goal: {step.description}\n"
        f"Expected output: {step.expected_output}"
    )

    raw = agent.send(messages=[HumanMessage(content=message)])

    return _parse(raw, step.id)


# ─────────────────────────────────────────────────────────────────────────────
#  Output parsing
# ─────────────────────────────────────────────────────────────────────────────

def _parse(raw, step_id: int) -> CoderOutput:
    """Parse create_agent result into a CoderOutput."""

    if isinstance(raw, CoderOutput):
        return raw

    if isinstance(raw, dict):
        structured = raw.get("structured_response")
        if isinstance(structured, CoderOutput):
            return structured

        # structured_response missing — return failure with context
        if "messages" in raw and raw["messages"]:
            last = raw["messages"][-1]
            content = getattr(last, "content", "") or ""
            return CoderOutput(
                step_id=step_id,
                success=False,
                error=(
                    f"structured_response not found in coder result.\n"
                    f"Last message: {content[:300]}"
                )
            )

    return CoderOutput(
        step_id=step_id,
        success=False,
        error=f"Unexpected result type: {type(raw)}"
    )