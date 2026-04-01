from pydantic import BaseModel, Field,ConfigDict,model_validator
from typing import List, Optional, Dict, Any



#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Supervisor Structured Output Schema
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class StepDetail(BaseModel):
    """Defines the structure for an individual step."""
    agent: str = Field(..., description="The agent assigned to this step.")
    description: str = Field(..., description="Detailed description of what the agent needs to do.")

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
    
    # The dictionary keys will be your step identifiers (e.g., "Step 1", "Step 2")
    steps: Optional[Dict[str, StepDetail]] = Field(
        default=None,
        description="The step-by-step analysis plan. Required if status is 'ANALYSIS PLAN'."
    )

    @model_validator(mode="after")
    def check_status_dependencies(self) -> "SupervisorOutput":
        """
        Enforces that 'steps' is present for an ANALYSIS PLAN 
        and 'question' is present for CLARIFICATION REQUIRED.
        """
        if self.status == "ANALYSIS PLAN" and not self.steps:
            raise ValueError(
                "When status is 'ANALYSIS PLAN', the 'steps' field cannot be empty or None."
            )
            
        if self.status == "CLARIFICATION REQUIRED" and not self.question:
            raise ValueError(
                "When status is 'CLARIFICATION REQUIRED', the 'question' field cannot be empty or None."
            )
            
        return self