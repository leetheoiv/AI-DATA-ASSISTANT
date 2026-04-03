from pydantic import BaseModel, Field

class AuditResult(BaseModel):
    is_passed: bool = Field(description="True if the analysis is accurate and consistent. False if there are any errors.")
    logical_conflicts: list[str] = Field(description="List of contradictions between agents (e.g., Math vs Visuals).")
    technical_errors: list[str] = Field(description="List of code failures like NameError or missing files.")
    missing_answers: list[str] = Field(description="Questions from the original list that were not addressed.")
    recommendation_for_supervisor: str = Field(description="Specific feedback telling the Supervisor how to fix the plan.")