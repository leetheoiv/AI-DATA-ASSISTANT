"""
core/state.py

Shared state passed between all nodes in the LangGraph workflow.

Uses TypedDict as recommended by LangGraph docs for performance.
Every node receives the full state as input and returns a dict
containing only the keys it updated.

State flow:
  supervisor  → writes: messages, improved_question
  planner     → writes: messages, plan
  human_approval → writes: plan (modified steps), human_approved
  coder       → writes: messages, step_results
  visualizer  → writes: messages, step_results
  stats       → writes: messages, step_results
  reporter    → writes: messages, final_report
"""

from typing import Annotated, Any, Optional, List
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

from structured_outputs.planner_output import PlannerOutput
 
 
class AgentState(TypedDict):
    """
    Shared state passed between all nodes in the graph.
 
    add_messages on `messages` appends rather than replaces.
    All other fields use last-write-wins.
    """
 
    # Full conversation history
    messages: Annotated[list, add_messages]
 
    # All improved questions from the supervisor (one per user question)
    # The planner receives this list and builds one unified plan
    improved_questions: Optional[List[str]]
 
    # The unified analysis plan covering all questions
    plan: Optional[PlannerOutput]
 
    # Whether the human approved the plan
    human_approved: Optional[bool]
 
    # Index of the current step being executed (1-based)
    current_step: Optional[int]
 
    # Accumulated results from each completed step
    # Key = step id, value = specialist agent output
    step_results: Optional[dict]
 
    # The reporter's final compiled output covering all questions
    final_report: Optional[str]