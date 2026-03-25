import os
import json
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1])) # Ensure the repo root is on sys.path so sibling packages like `prompt_templates` can be imported
from langchain_core.messages import HumanMessage
import pandas as pd
from agent import AIAgent
from context import DatasetContext
from structured_outputs import PlannerOutput, PlannerAction
from structured_outputs.planner_output import AnalysisStep
from tools.dataset_tools import get_dataset_structure, get_dataset_statistics
from langchain_core.prompts import PromptTemplate
from prompt_templates.visualizer import VISUALIZER_PROMPT_TEMPLATE
from structured_outputs.visualizer_structured_output import VisualizerOutput
from tools.visualizer_tools import load_dataframe, create_chart
import time

VISUALIZER_TOOLS = [create_chart]

def run_visualizer(
    step: AnalysisStep,
    context: DatasetContext,
    previous_step_results: dict = None,
) -> VisualizerOutput:
    """
    Execute one analysis step by generating a visualization.

    Args:
        step:                 The AnalysisStep to execute.
        context:              Dataset context — file path, columns, business rules.
        previous_step_results: Results from prior steps keyed by step id.
                              The visualizer reads these when step.depends_on is set.

    Returns:
        VisualizerOutput with success status, summary, and raw result.
    """
    start = time.time()
    print(f"--- [Visualizer] Starting Step {step.id}  at {start})---")
    # Load the dataset into the shared exec scope so run_code can access it
    try:
        load_dataframe(context.file_path)
    except Exception as e:
        return VisualizerOutput(
            step_id=step.id,
            success=False,
            error=f"Failed to load dataset from {context.file_path}: {e}",
        )
    
    # Format previous results for prompt injection — keep short
    prev_results = previous_step_results or {}
    if prev_results:
        # Keep only one-line summaries and limit overall size
        lines = []
        for sid, result in prev_results.items():
            s = str(result)
            s = s.replace("\n", " ")[:250]  # single-line, truncated
            lines.append(f"Step {sid}: {s}")
        prev_text = "\n".join(lines)[:1500]
    else:
        prev_text = "No previous steps completed yet."
    
    # Build a concise columns summary (not full long descriptions)
    cols = getattr(context, "column_descriptions", {}) or {}
    col_summary = ", ".join(
        f"{k}" for k in list(cols.keys())[:20]
    )
    if len(cols) > 20:
        col_summary += f", +{len(cols)-20} more"

    # Build system prompt with all context injected
    system_prompt = VISUALIZER_PROMPT_TEMPLATE.format(
        file_path=context.file_path,
        dataset_description=context.dataset_description,
        column_descriptions=col_summary,
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
   
    # Limit model reply size to avoid large generations and set deterministic behavior
    agent = AIAgent(model="gpt-4o-mini", max_retries=1, max_tokens=4000, timeout=120)
    agent.create_agent(
        model_name="visualizer",
        system_prompt=system_prompt,
        response_format=VisualizerOutput,
        tools=VISUALIZER_TOOLS,
    )
    print(agent)

    # The human message is the step instruction
    message = (
        f"Execute step {step.id}: {step.title}\n"
        f"Goal: {step.description}\n"
        f"Expected output: {step.expected_output}"
    )
  

    # DEBUG: Calculate estimated tokens in the prompt
    total_chars = len(system_prompt) + len(message)
    print(f"DEBUG: Prompt character count: {total_chars}")
    if total_chars > 10000:
        print("WARNING: Prompt is unusually large. Printing first 500 chars:")
        print(system_prompt[:500])

    print('message',message)

    raw = agent.send(messages=[HumanMessage(content=message)])

    print("raw",raw)
    return _parse(raw, step.id,start=start)


# ─────────────────────────────────────────────────────────────────────────────
#  Output parsing
# ─────────────────────────────────────────────────────────────────────────────

def _parse(raw, step_id: int,start) -> VisualizerOutput:
    """
    Sanitizes and parses agent/tool results into a strict VisualizerOutput.
    """
    print(f"--- [Visualizer] LLM analyzing goals{time.time() - start:.2f}s ---")
    structured = raw.get("structured_response")
    
    # If the LLM just gave us a path, we are golden
    if structured and structured.image_base64:
        print(f"--- [Visualizer] Chart available at: {structured.image_base64} ---")
    
    # Final cleanup
    structured.step_id = step_id
    return structured



    # # 1. If it's already the correct object, return it
    # if isinstance(raw, VisualizerOutput):
    #     return raw

    # # 2. Extract the structured payload from the AIAgent response
    # # This assumes your AIAgent returns a dict with 'structured_response'
    # payload = {}
    # if isinstance(raw, dict):
    #     payload = raw.get("structured_response", {})
    #     if isinstance(payload, VisualizerOutput):
    #         return payload
        
    #     # Inside _parse in visualizer_agent.py
    #     tool_data = raw.get("result", {}) # This is the dict returned by the tool
    #     if isinstance(tool_data, dict):
    #         payload["image_base64"] = tool_data.get("image_base64")
            
    #         # Check our new internal key first, then fall back to result
    #         payload["raw_result"] = tool_data.get("data_internal") or tool_data.get("result")
            
    #         payload["summary"] = tool_data.get("caption") or payload.get("summary")

    # # 3. TYPE SANITIZATION (The critical part for Pydantic validation)
    # raw_val = payload.get("raw_result")

    # # Convert Plotly Figure to Dict
    # if hasattr(raw_val, "to_dict"):
    #     payload["raw_result"] = raw_val.to_dict()
    
    # # Convert Pandas DataFrame to List of Dicts
    # elif isinstance(raw_val, pd.DataFrame):
    #     payload["raw_result"] = raw_val.to_dict(orient="records")
    
    # # Convert Pandas Series to Dict
    # elif isinstance(raw_val, pd.Series):
    #     payload["raw_result"] = raw_val.to_dict()

    # # 4. Final Object Creation
    # try:
    #     # Ensure step_id is present
    #     if "step_id" not in payload:
    #         payload["step_id"] = step_id
        
    #     # Handle success flag (default to True if we have data)
    #     if "success" not in payload:
    #         payload["success"] = True if (payload.get("raw_result") or payload.get("image_base64")) else False

    #     return VisualizerOutput(**payload)
        
    # except Exception as e:
    #     return VisualizerOutput(
    #         step_id=step_id,
    #         success=False,
    #         error=f"Pydantic Validation Error: {str(e)}\nPayload received: {type(raw_val)}"
    #     )
