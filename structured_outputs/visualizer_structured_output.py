from typing import Optional, Union, Dict, Any, List
from pydantic import BaseModel, Field

"""
structured_outputs/visualizer.py

Pydantic model for the Visualizer agent's output.
"""

from typing import Optional
from pydantic import BaseModel, Field


class VisualizerOutput(BaseModel):
    """The visualizer agent's result for one chart step."""

    step_id: int = Field(
        description="The id of the analysis step that was executed."
    )

    success: bool = Field(
        description="Whether the chart was created successfully."
    )
    # The AI writes the specific plotting logic here
    visualizer_code: str = Field(
        description="Python code using plt or sns. Assume 'df' is available. "
                    "End with plt.savefig(chart_path)."
    )

    chart_description: Optional[str] = Field(
        default=None,
        description=(
            "Plain-English description of what the chart shows, including "
            "any business rule interpretations. Used by the reporter agent. "
            "Only populated when success is True."
        )
    )

    chart_type: Optional[str] = Field(
        default=None,
        description="The type of chart that was created (e.g. 'bar', 'line', 'histogram')."
    )

    error: Optional[str] = Field(
        default=None,
        description=(
            "Description of what went wrong if success is False."
        )
    )