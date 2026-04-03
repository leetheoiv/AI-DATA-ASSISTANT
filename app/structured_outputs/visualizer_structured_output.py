
from pydantic import BaseModel, Field,ConfigDict,model_validator
from typing import List, Optional, Dict, Any

class VisualizerOutput(BaseModel):
    executable_code: str
    results_interpretation: str
    # Note: No thought_process field here