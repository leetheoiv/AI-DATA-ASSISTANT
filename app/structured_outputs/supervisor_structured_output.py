from app.agent import AIAgent
from app.prompt_templates.supervisor_prompt_template import supervisor_prompt_template
from pydantic import BaseModel,Field
from typing import Literal



#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Supervisor Structured Output Schema
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class AnalysisTask(BaseModel):
    agent: Literal["coder", "visualizer", "reporter"]
    task_description: str
    depends_on: list[int] = []  # indices of tasks that must complete first

class AnalysisPlan(BaseModel):
    status: Literal["plan", "clarification"]
    clarification_questions: list[str] = Field(...,description='Is populated with questions to the user to clarify the users inital question')      # populated when status == "clarification"
    tasks: list[AnalysisTask] = []   # populated when status == "plan"
    reasoning: str                   # supervisor's internal reasoning

# ── Supervisor ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 