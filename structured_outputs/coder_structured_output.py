"""
structured_outputs/coder.py

Pydantic model for the Coder agent's output.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CoderOutput(BaseModel):
    """The coder agent's result for one analysis step."""

    step_id: int = Field(
        description="The id of the analysis step that was executed."
    )

    success: bool = Field(
        description="Whether the step completed successfully."
    )

    summary: Optional[str] = Field(
        default=None,
        description=(
            "Clean formatted summary of the result, ready for the reporter. "
            "Include business rule interpretations where relevant. "
            "Only populated when success is True."
        )
    )

    raw_result: Optional[str] = Field(
        default=None,
        description=(
            "The raw value of the `result` variable from code execution. "
            "Used by downstream agents (e.g. visualizer reads this to chart it)."
        )
    )

    error: Optional[str] = Field(
        default=None,
        description=(
            "Description of what went wrong if success is False. "
            "Include the last error message and what was tried."
        )
    )

    code_used: Optional[str] = Field(
        default=None,
        description="The final pandas code that was executed successfully."
    )