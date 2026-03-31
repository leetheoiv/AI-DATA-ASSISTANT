from pydantic import BaseModel, Field,ConfigDict
from typing import List, Optional, Dict, Any



#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Supervisor Structured Output Schema
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class SupervisorOutput(BaseModel):
    """
    SupervisorOutput defines the structured output format for the Supervisor agent. 
    """
    model_config = ConfigDict(extra="forbid")
    status: str = Field(
        ..., 
        description="Must be 'CLARIFICATION REQUIRED' or 'ANALYSIS PLAN'."
    )
    
    #Flattening these out removes the need for a dynamic dictionary entirely
    question: Optional[str] = Field(
        default=None,
        description="The question to ask. Required if status is 'CLARIFICATION REQUIRED'."
    )
    
    steps: Optional[List[str]] = Field(
        default=None,
        description="The step-by-step analysis plan. Required if status is 'ANALYSIS PLAN'."
    )