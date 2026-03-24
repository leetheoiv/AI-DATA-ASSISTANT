"""
tools/coder_tools.py

Tools used exclusively by the coder agent.

  run_code      — executes pandas code against a loaded DataFrame
  format_result — cleans up raw execution output for downstream agents
"""

import traceback
from io import StringIO
from contextlib import redirect_stdout

import pandas as pd
import numpy as np
from langchain.tools import tool


# ─────────────────────────────────────────────────────────────────────────────
#  Shared execution scope — persists the DataFrame between tool calls
#  within a single agent invocation
# ─────────────────────────────────────────────────────────────────────────────

_EXEC_STATE: dict = {
    "df":        None,
    "file_path": None,
}


def load_dataframe(file_path: str) -> pd.DataFrame:
    """Load a CSV or Excel file into the shared exec scope."""
    if file_path.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    _EXEC_STATE["df"] = df
    _EXEC_STATE["file_path"] = file_path
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Tool: run_code
# ─────────────────────────────────────────────────────────────────────────────

@tool("run_code", description=(
    "Execute Python/pandas/numpy code against the loaded dataset. "
    "The DataFrame is available as `df`. pandas is `pd`, numpy is `np`. "
    "You MUST assign your final answer to a variable called `result`. "
    "If the code raises an error, read the traceback carefully, fix the issue, "
    "and call this tool again with corrected code. You may retry up to 3 times."
))
def run_code(code: str) -> dict:
    """
    Execute pandas code and return the result.

    Args:
        code: Valid Python/pandas/numpy code. Must assign final answer to `result`.

    Returns:
        {
            "success": bool,
            "result":  the value of `result` (serialised if DataFrame/Series),
            "stdout":  any print() output from the code,
            "error":   traceback string if execution failed
        }
    """
    df = _EXEC_STATE.get("df")
    if df is None:
        return {
            "success": False,
            "error": (
                "No dataset loaded. The dataset should have been loaded "
                "automatically — check that file_path in context is correct."
            )
        }

    # Capture stdout
    stdout_capture = StringIO()

    exec_globals = {
        "df": df,
        "pd": pd,
        "np": np,
    }
    exec_locals = {}

    try:
        with redirect_stdout(stdout_capture):
            exec(code, exec_globals, exec_locals)  # noqa: S102

        if "result" not in exec_locals:
            return {
                "success": False,
                "stdout":  stdout_capture.getvalue(),
                "error": (
                    "Code executed but `result` was never assigned. "
                    "Make sure your code ends with: result = <your answer>"
                )
            }

        raw = exec_locals["result"]

        # Serialise pandas objects
        if isinstance(raw, pd.DataFrame):
            output = raw.to_dict(orient="records")
        elif isinstance(raw, pd.Series):
            output = raw.to_dict()
        else:
            output = raw

        return {
            "success": True,
            "result":  output,
            "stdout":  stdout_capture.getvalue(),
            "error":   None,
        }

    except Exception:
        return {
            "success": False,
            "result":  None,
            "stdout":  stdout_capture.getvalue(),
            "error":   traceback.format_exc(),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Tool: format_result
# ─────────────────────────────────────────────────────────────────────────────

@tool("format_result", description=(
    "Format the raw result from run_code into a clean, human-readable summary. "
    "Always call this as the final step after getting a successful result. "
    "Include relevant business rule interpretations in the summary."
))
def format_result(
    step_title: str,
    raw_result: str,
    business_rule_notes: str = "",
) -> dict:
    """
    Produce a clean summary of the computation result.

    Args:
        step_title:          The title of the analysis step being completed.
        raw_result:          The result from run_code as a string.
        business_rule_notes: Any business rules that affect interpretation.

    Returns:
        {
            "success": bool,
            "summary": clean formatted string ready for the reporter
        }
    """
    try:
        result_str = str(raw_result)
        if len(result_str) > 3000:
            result_str = result_str[:3000] + "\n... [truncated]"

        summary = f"**{step_title}**\n\n{result_str}"

        if business_rule_notes and business_rule_notes.strip():
            summary += f"\n\n*Interpretation note: {business_rule_notes.strip()}*"

        return {"success": True, "summary": summary}

    except Exception as e:
        return {"success": False, "error": str(e)}