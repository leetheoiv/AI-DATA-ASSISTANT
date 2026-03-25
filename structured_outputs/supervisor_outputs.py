"""
structured_outputs/supervisor.py

Pydantic models for the Supervisor agent's output.

The supervisor has two possible output types:
  - CLARIFY  — more information needed from the user
  - HANDOFF  — question is clear and ready for the planner

SupervisorOutput is a single Pydantic model with optional fields.
The action field tells you which type it is.

Note: We originally wanted a union type (SupervisorClarify | SupervisorHandoff)
but create_agent only accepts a single Pydantic model as response_format.
Optional fields with a discriminator action field is the correct workaround.
"""


from typing import Optional, List
from pydantic import BaseModel, Field
from structured_outputs.base import SupervisorAction
 
 
class SupervisorOutput(BaseModel):
    """
    The supervisor's response. Check the action field first:
      action == 'CLARIFY'  → show clarifying_question to the user
      action == 'HANDOFF'  → pass improved_questions to the planner
    """
 
    action: SupervisorAction = Field(
        description=(
            "'CLARIFY' if any question is too vague to act on. "
            "'HANDOFF' if all questions are clear and ready for the planner."
        )
    )
 
    reasoning: str = Field(
        description=(
            "1-2 sentences explaining the decision. "
            "If CLARIFY: explain which question is unclear and why. "
            "If HANDOFF: confirm all questions are clear."
        )
    )
 
    clarifying_question: Optional[str] = Field(
        default=None,
        description=(
            "Only populated when action is CLARIFY. "
            "One focused question about the most ambiguous part. "
            "Only ask about the user's GOAL — never ask about the dataset "
            "since that context is already provided."
        )
    )
 
    improved_questions: Optional[List[str]] = Field(
        default=None,
        description=(
            "Only populated when action is HANDOFF. "
            "One improved question per user question, in the same order. "
            "Each improved question must: "
            "(1) reference actual column names from the dataset, "
            "(2) state clearly what output is expected, "
            "(3) weave in relevant business rules, "
            "(4) remove vague or filler language."
        )
    )
 
    def is_clarify(self) -> bool:
        return self.action == SupervisorAction.CLARIFY
 
    def is_handoff(self) -> bool:
        return self.action == SupervisorAction.HANDOFF