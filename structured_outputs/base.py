"""
structured_outputs/base.py

Shared types used across multiple agents.
Import from here to avoid circular dependencies.
"""

from pydantic import BaseModel, Field
from enum import Enum


class AgentType(str, Enum):
    """
    The specialist agents the planner can assign work to.
    Using str as base class means AgentType.CODER == "coder" — 
    works cleanly in JSON serialisation and string comparisons.
    """
    CODER      = "coder"
    VISUALIZER = "visualizer"
    STATS      = "stats"
    REPORTER   = "reporter"


class SupervisorAction(str, Enum):
    """Possible actions the supervisor can take."""
    CLARIFY = "CLARIFY"
    HANDOFF = "HANDOFF"

class PlannerAction(str, Enum):
    """Possible actions the planner can take."""
    PLAN = "PLAN"
    CLARIFY = "CLARIFY"