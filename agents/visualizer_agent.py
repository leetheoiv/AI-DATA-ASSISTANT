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
from tools.dataset_tools import _load_dataframe
from tools.visualizer_tools import create_chart,format_chart_result
import time
from functions.code_executor import execute_ai_code
from tools.coder_tools import _EXEC_STATE # Use your existing shared state
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
 
 
def run_visualizer(
    step: AnalysisStep,
    context: DatasetContext,
    previous_step_results: dict = None,
) -> VisualizerOutput:
    """
    Generate a chart for one analysis step.
 
    Args:
        step:                 The AnalysisStep to execute.
        context:              Dataset context — file path, columns, business rules.
        previous_step_results: Results from prior steps. The visualizer reads
                              the coder's raw_result from here.
 
    Returns:
        VisualizerOutput with chart_path and description.
    """
    # Load the dataset so create_chart has access to df
    try:
        _load_dataframe(context.file_path)
    except Exception as e:
        return VisualizerOutput(
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
 
    # Build system prompt
    system_prompt = VISUALIZER_PROMPT_TEMPLATE.format(
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
 
    agent = AIAgent(model="gpt-4o-mini",max_retries=1)
    agent.create_agent(
        model_name="visualizer",
        system_prompt=system_prompt,
        response_format=VisualizerOutput
    )
 
    message = (
        f"Execute step {step.id}: {step.title}\n"
        f"Goal: {step.description}\n"
        f"Expected output: {step.expected_output}\n"
        f"Read the coder's output from previous_step_results and use it to create the chart."
    )
    print(f"[DEBUG] Sending message to visualizer agent for step {step.id}:\n{message}\n")

    raw = agent.send(messages=[HumanMessage(content=message)])

    print(f"[DEBUG] Raw visualizer output for step {step.id}:\n{raw}\n")
    result =  _parse(raw, step.id)

   # Ensure step_id is set
    result.step_id = step.id

    # The LLM says the code is ready, so now WE run it
    if result.visualizer_code: 
        try:
            df = _EXEC_STATE.get("df")
            chart_filename = f"charts/step_{step.id}.png"
            os.makedirs("charts", exist_ok=True)

            exec_globals = {
                "plt": plt, "sns": sns, "df": df, "pd": pd, "np": np,
                "chart_path": chart_filename
            }
            
            plt.close('all') 
            exec(result.visualizer_code, exec_globals)
            
            if os.path.exists(chart_filename):
                result.chart_path = chart_filename
                result.success = True # Set success to True only after file exists
            else:
                raise FileNotFoundError("Chart file was not saved by the generated code.")

        except Exception as e:
            result.success = False
            result.error = f"Execution Error: {str(e)}"
    
    return result
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Output parsing
# ─────────────────────────────────────────────────────────────────────────────
 
def _parse(raw, step_id: int) -> VisualizerOutput:
    # 1. If it's already an object, just ensure it has the step_id
    if isinstance(raw, VisualizerOutput):
        raw.step_id = step_id
        return raw
 
    # 2. Extract from dictionary
    if isinstance(raw, dict):
        structured = raw.get("structured_response")
        
        # If the agent correctly produced the Pydantic object
        if isinstance(structured, VisualizerOutput):
            structured.step_id = step_id
            return structured
        
        # Fallback if the agent returned a dict instead of an object
        if isinstance(structured, dict):
            return VisualizerOutput(**{**structured, "step_id": step_id})

    # 3. Error Fallback
    return VisualizerOutput(
        step_id=step_id,
        success=False,
        error="Agent failed to return a structured response."
    )