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

from typing import Optional
from pydantic import BaseModel, Field
from structured_outputs.base import SupervisorAction


class SupervisorOutput(BaseModel):
    """
    The supervisor's response. Check the action field to know what happened:
      - action == 'CLARIFY'  → read clarifying_question, show it to the user
      - action == 'HANDOFF'  → read improved_question, pass it to the planner
    """

    action: SupervisorAction = Field(
        description=(
            "What the supervisor decided to do. "
            "'CLARIFY' means more information is needed from the user. "
            "'HANDOFF' means the question is clear and ready for the planner."
        )
    )

    reasoning: str = Field(
        description=(
            "1-2 sentences explaining the decision. "
            "If CLARIFY: explain what is missing or ambiguous. "
            "If HANDOFF: explain what the user wants."
        )
    )

    clarifying_question: Optional[str] = Field(
        default=None,
        description=(
            "Only populated when action is CLARIFY. "
            "A single focused question to ask the user. "
            "Ask only the most important missing piece."
        )
    )

    improved_question: Optional[str] = Field(
        default=None,
        description=(
            "Only populated when action is HANDOFF. "
            "The rewritten, precise version of the user's question. Must: "
            "(1) reference actual column names from the dataset profile, "
            "(2) state clearly what output is expected, "
            "(3) weave in relevant business rules by name, "
            "(4) remove all vague or filler language."
        )
    )

    def is_clarify(self) -> bool:
        return self.action == SupervisorAction.CLARIFY

    def is_handoff(self) -> bool:
        return self.action == SupervisorAction.HANDOFF