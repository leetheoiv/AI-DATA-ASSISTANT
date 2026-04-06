
from pydantic import BaseModel, Field,ConfigDict,model_validator
from typing import List, Optional, Dict, Any

class VisualizerOutput(BaseModel):
    executable_code: str = Field(...,description='Python code that creates and saves a visualization as a PNG file. Must include code to save the figure to disk (e.g., plt.savefig("output.png"))') 
    results_interpretation: str = Field(...,description='interpretation of the visual trends, to be passed to the Reporter for synthesis') 
    created_image_path: str = Field(None,description='Path to the saved visualization image (e.g., output.png)')

    # Note: No thought_process field here