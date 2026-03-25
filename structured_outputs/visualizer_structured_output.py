from typing import Optional, Union, Dict, Any, List
from pydantic import BaseModel, Field

class VisualizerOutput(BaseModel):
    """The visualizer agent's result for one analysis step."""
    
    step_id: int = Field(description="The id of the analysis step.")
    success: bool = Field(description="Whether the step completed.")
    
    # Accept any serializable result (plotly dict, table rows, or plain text).
    raw_result: Optional[Any] = Field(
        default=None,
        description=(
            "The structured data from the tool. "
            "For Plotly: a dict with 'data'/'layout'. For tables: a list of row dicts. "
            "Large/non-serializable objects should be stored elsewhere and only a small "
            "sentinel or metadata returned here."
        ),
    )
    
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64 string for Matplotlib/Seaborn output."
    )
    
    # Make these optional with explicit defaults so validation won't require them
    summary: Optional[str] = Field(default=None, description="Business summary of the chart.")
    code_used: Optional[str] = Field(default=None, description="The Python code that generated this.")
    error: Optional[str] = Field(default=None)
    