from app.agent import AIAgent
from app.prompt_templates.supervisor_prompt_template import supervisor_prompt_template
from pydantic import BaseModel,Field
from typing import Literal,Optional,List



#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Supervisor Structured Output Schema
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class AnalysisTask(BaseModel):
    agent: Literal["coder", "visualizer", "reporter"]
    user_question: str = Field(description="The original user question this task helps answer.")
    task_description: str
    depends_on: List[int]
    # Optional: Keep revised_question if the Supervisor wants to 'Technical-ize' it
    revised_question: Optional[str] = None

class AnalysisPlan(BaseModel):
    status: Literal["plan", "clarification"]
    user_questions: list[str] = Field(..., description="The original user questions that the supervisor is analyzing.") 
    clarification_questions: list[str] = Field(...,description='Is populated with questions to the user to clarify the users inital question')      # populated when status == "clarification"
    overall_goal: Optional[str] = Field(None, description="The high-level business objective.")
    tasks: list[AnalysisTask] = []   # populated when status == "plan"
    reasoning: str                   # supervisor's internal reasoning

# ── Supervisor ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 