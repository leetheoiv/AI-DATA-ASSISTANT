"""
structured_outputs/planner.py

Pydantic models for the Planner agent's output.

The planner produces a full structured analysis plan with ordered steps,
each assigned to a specific specialist agent.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from structured_outputs.base import AgentType,PlannerAction


class AnalysisStep(BaseModel):
    """A single step in the analysis plan assigned to one specialist agent."""
 
    id: int = Field(
        description="Step number starting from 1."
    )
 
    title: str = Field(
        description=(
            "Short name for this step, 5 words or fewer. "
            "Example: 'Compute churn rate by segment'."
        )
    )
 
    description: str = Field(
        description=(
            "1-2 sentences explaining what this step does and why it is "
            "needed to answer the question. Reference specific column names."
        )
    )
 
    agent: AgentType = Field(
        description=(
            "The specialist agent responsible for this step. "
            "Must be one of: coder, visualizer, stats, reporter. "
            "Assign exactly one agent per step. If a task needs more than one agent (e.g. both a coder and visualizer), "
            "break it into multiple steps. "
        )
    )
 
    inputs: List[str] = Field(
        description=(
            "Column names or outputs from previous steps this step needs. "
            "Be specific — name exact columns or reference prior steps "
            "by id (e.g. 'output of step 2')."
        )
    )
 
    expected_output: str = Field(
        description=(
            "Concrete description of what this step produces. "
            "Examples: 'Dict mapping plan_type to churn rate', "
            "'Bar chart of churn rate by segment', "
            "'p-value and interpretation for two-sample t-test'."
        )
    )
 
    depends_on: List[int] = Field(
        default=[],
        description=(
            "Step ids that must complete before this step can run. "
            "Empty means this step can run immediately. "
            "Steps with no dependencies can run in parallel."
        )
    )
 
    business_rule_notes: Optional[str] = Field(
        default=None,
        description=(
            "Business rules from the dataset context that the assigned "
            "agent must apply when executing this step. "
            "Example: 'credits is a negative signal — high values indicate "
            "billing disputes, not positive performance.' "
            "Null if no business rules apply to this step."
        )
    )
 
 
class PlannerOutput(BaseModel):
    """
    The planner's response. Check the action field first:
      action == 'PLAN'    → a full analysis plan is ready, read the steps
      action == 'CLARIFY' → something is ambiguous, read clarifying_question
    """
 
    action: PlannerAction = Field(
        description=(
            "What the planner decided to do. "
            "'PLAN' means a full analysis plan was produced. "
            "'CLARIFY' means something critical is ambiguous and needs "
            "clarification before a reliable plan can be created."
        )
    )
 
    # ── PLAN fields ───────────────────────────────────────────────────────────
 
    goal: Optional[str] = Field(
        default=None,
        description=(
            "Only populated when action is PLAN. "
            "One sentence restating what this analysis will answer. "
            "Should reference the actual question and dataset."
        )
    )
 
    dataset_summary: Optional[str] = Field(
        default=None,
        description=(
            "Only populated when action is PLAN. "
            "2-3 sentences summarising the dataset characteristics most "
            "relevant to answering the question. Include actual column "
            "names, data types, and anything from the data inspection "
            "that affects the approach."
        )
    )
 
    steps: Optional[List[AnalysisStep]] = Field(
        default=None,
        description=(
            "Only populated when action is PLAN. "
            "Ordered list of analysis steps. Use the minimum number of "
            "steps needed to fully answer the question. "
            "Always end with a reporter step if more than one other "
            "agent contributes."
        )
    )
 
    risks: List[str] = Field(
        default=[],
        description=(
            "Data quality, privacy, or interpretability concerns. "
            "Always populate this — even small issues are worth noting. "
            "Examples: 'churn has 3 percent nulls — verify handling', "
            "'enterprise segment only has 45 rows — comparisons unreliable'."
        )
    )
 
    # ── CLARIFY fields ────────────────────────────────────────────────────────
 
    clarifying_question: Optional[str] = Field(
        default=None,
        description=(
            "Only populated when action is CLARIFY. "
            "A single focused question for the supervisor to pass back "
            "to the user. Only use CLARIFY when the ambiguity cannot "
            "be resolved by inspecting the data or noting it as a risk."
        )
    )
 
    # ── Helpers ───────────────────────────────────────────────────────────────
 
    def is_plan(self) -> bool:
        return self.action == PlannerAction.PLAN
 
    def is_clarify(self) -> bool:
        return self.action == PlannerAction.CLARIFY