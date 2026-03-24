"""
graph.py
 
LangGraph workflow for the multi-agent data analysis system.
 
Flow:
  START
    ↓
  supervisor  — parses + improves all user questions
    ↓ (if CLARIFY → END, wait for user response)
    ↓ (if HANDOFF)
  planner     — builds one unified plan for all questions
    ↓ (if CLARIFY → supervisor)
    ↓ (if PLAN)
  human_approval  — interrupt: user reviews/modifies/approves plan
    ↓ (if rejected → supervisor)
    ↓ (if approved)
  executor    — runs each step sequentially (placeholder for now)
    ↓ (loop until all steps done)
  END
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage, AIMessage

from workflow.state import AgentState
from context import DatasetContext
from structured_outputs import SupervisorAction, PlannerAction, PlannerOutput
from agents.supervisor_agent import run_supervisor
from agents.planner_agent import run_planner
from agents.coder_agent import run_coder
from structured_outputs.base import AgentType
# ─────────────────────────────────────────────────────────────────────────────
#  Node functions
# ─────────────────────────────────────────────────────────────────────────────
 
def supervisor_node(state: AgentState, context: DatasetContext) -> dict:
    """
    Parse all user questions, clarify if needed, improve and hand off.
    Also handles clarifying questions coming back from the planner.
    """
    messages = state.get("messages", [])
    planner_clarification = state.get("planner_clarification")
 
    # Get last human message
    last_human = next(
        (m for m in reversed(messages) if
         (hasattr(m, "type") and m.type == "human") or
         (isinstance(m, dict) and m.get("role") == "user")),
        None
    )
 
    if last_human is None:
        return {"messages": [AIMessage(content="No message found.")]}
 
    content = (
        last_human.content
        if hasattr(last_human, "content")
        else last_human.get("content", "")
    )
 
    # If the planner sent a clarifying question, show it to the user
    # and wait for their response before re-running the supervisor
    if planner_clarification:
        print(f"[Supervisor] Forwarding planner clarification to user: {planner_clarification}")
        return {
            "messages": [AIMessage(content=planner_clarification)],
            "planner_clarification": None,  # clear it — we've shown it
        }
 
    print(f"\n[Supervisor] Original question: {content}")
 
    result = run_supervisor(
        user_message=content,
        context=context,
        conversation_history=messages[:-1],
    )
 
    if result.is_clarify():
        print(f"[Supervisor] Needs clarification: {result.clarifying_question}")
        return {
            "messages": [AIMessage(content=result.clarifying_question)],
        }
 
    print(f"[Supervisor] Improved questions:")
    for i, q in enumerate(result.improved_questions or [], 1):
        print(f"  {i}. {q}")
 
    questions_preview = "\n".join(
        f"  {i+1}. {q}" for i, q in enumerate(result.improved_questions or [])
    )
    return {
        "messages": [AIMessage(
            content=f"Got it — I'll analyse these questions:\n{questions_preview}"
        )],
        "improved_questions": result.improved_questions,
    }
 
 
def planner_node(state: AgentState, context: DatasetContext) -> dict:
    """
    Build one unified analysis plan covering all improved questions.
    If something is ambiguous, store a clarifying question in state
    and route back to the supervisor to ask the user.
    """
    improved_questions = state.get("improved_questions", [])
 
    combined = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(improved_questions)
    )
 
    result = run_planner(
        improved_question=combined,
        context=context,
    )
 
    if result.is_clarify():
        print(f"[Planner] Needs clarification: {result.clarifying_question}")
        return {
            "messages": [AIMessage(content=f"[Planner needs clarification] {result.clarifying_question}")],
            "planner_clarification": result.clarifying_question,
            "improved_questions": None,
        }
 
    print(f"[Planner] Plan ready — {len(result.steps)} steps")
    return {
        "messages": [AIMessage(
            content=f"Analysis plan ready — {len(result.steps)} steps covering {len(improved_questions)} question(s)."
        )],
        "plan": result,
        "planner_clarification": None,
        "current_step": 1,
        "step_results": {},
    }
 
 
def human_approval_node(state: AgentState) -> dict:
    """
    Pause for human review of the plan.
    Resume with Command(resume={"approved": True/False, "plan": ...})
    """
    plan = state.get("plan")
 
    human_input = interrupt({
        "message": "Please review the analysis plan.",
        "plan": plan.model_dump() if plan else None,
    })
 
    approved = human_input.get("approved", False)
    updated_plan_data = human_input.get("plan")
 
    if not approved:
        return {
            "messages": [AIMessage(content="Plan rejected — please clarify your questions.")],
            "plan": None,
            "improved_questions": None,
        }
 
    if updated_plan_data and isinstance(updated_plan_data, dict):
        updated_plan = PlannerOutput(**updated_plan_data)
        return {
            "messages": [AIMessage(content="Plan approved. Starting analysis.")],
            "plan": updated_plan,
            "human_approved": True,
            "current_step": 1,
        }
 
    return {
        "messages": [AIMessage(content="Plan approved. Starting analysis.")],
        "human_approved": True,
        "current_step": 1,
    }
 
 
def executor_node(state: AgentState, context: DatasetContext) -> dict:
    """
    Execute the current step by routing to the correct specialist agent.
 
    Currently handles: coder
    Placeholder for: visualizer, stats, reporter
    """
    plan         = state.get("plan")
    current_step = state.get("current_step", 1)
    step_results = dict(state.get("step_results") or {})
 
    if not plan or not plan.steps:
        return {"final_report": "No steps to execute."}
 
    step = next((s for s in plan.steps if s.id == current_step), None)
    if step is None:
        return {"final_report": "All steps complete."}
 
    print(f"\n[Executor] Running step {current_step}/{len(plan.steps)}: "
          f"{step.title} [{step.agent.value}]")
 
    # ── Route to the correct specialist agent ────────────────────────────────
    if step.agent == AgentType.CODER:
        result = run_coder(
            step=step,
            context=context,
            previous_step_results=step_results,
        )
        step_output = result.summary if result.success else f"[Error] {result.error}"
        step_results[current_step] = {
            "summary":    result.summary,
            "raw_result": result.raw_result,
            "success":    result.success,
            "error":      result.error,
        }
        status_msg = (
            f"Step {current_step} ✓ {step.title}"
            if result.success
            else f"Step {current_step} ✗ {step.title}: {result.error}"
        )
 
    elif step.agent == AgentType.VISUALIZER:
        # Placeholder — visualizer agent not built yet
        step_results[current_step] = {
            "summary": f"[Placeholder] Visualizer step: {step.title}",
            "success": True,
        }
        status_msg = f"Step {current_step} [Placeholder] {step.title}"
 
    elif step.agent == AgentType.STATS:
        # Placeholder — stats agent not built yet
        step_results[current_step] = {
            "summary": f"[Placeholder] Stats step: {step.title}",
            "success": True,
        }
        status_msg = f"Step {current_step} [Placeholder] {step.title}"
 
    elif step.agent == AgentType.REPORTER:
        # Placeholder — reporter agent not built yet
        step_results[current_step] = {
            "summary": f"[Placeholder] Reporter step: {step.title}",
            "success": True,
        }
        status_msg = f"Step {current_step} [Placeholder] {step.title}"
 
    else:
        step_results[current_step] = {
            "summary": f"Unknown agent type: {step.agent}",
            "success": False,
        }
        status_msg = f"Step {current_step} unknown agent: {step.agent}"
 
    # ── Advance to next step ─────────────────────────────────────────────────
    next_step = current_step + 1
    is_last   = next_step > len(plan.steps)
 
    # Build final report when all steps are done
    final_report = None
    if is_last:
        final_report = _compile_interim_report(plan, step_results)
 
    return {
        "messages":    [AIMessage(content=status_msg)],
        "step_results": step_results,
        "current_step": next_step if not is_last else current_step,
        "final_report": final_report,
    }
 
 
def _compile_interim_report(plan, step_results: dict) -> str:
    """
    Build a simple interim report from step results.
    Will be replaced by the reporter agent once built.
    """
    lines = [f"# Analysis Complete\n\n**Goal:** {plan.goal}\n"]
    for step in plan.steps:
        result = step_results.get(step.id, {})
        lines.append(f"## Step {step.id}: {step.title}")
        summary = result.get("summary", "No output.")
        lines.append(summary or "No output.")
        lines.append("")
    if plan.risks:
        lines.append("## Risks noted")
        for risk in plan.risks:
            lines.append(f"- {risk}")
    return "\n".join(lines)
 
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Routing functions
# ─────────────────────────────────────────────────────────────────────────────
 
def route_supervisor(state: AgentState) -> str:
    """
    After supervisor runs:
      - If planner_clarification was just shown → END, wait for user response
      - If improved_questions set → go to planner
      - Otherwise → END, wait for user clarification response
    """
    # planner_clarification was cleared after being shown — means we
    # just forwarded it to the user, so wait for their response
    if not state.get("planner_clarification") and not state.get("improved_questions"):
        return END
    if state.get("improved_questions"):
        return "planner"
    return END
 
 
def route_planner(state: AgentState) -> str:
    if state.get("plan"):
        return "human_approval"
    return "supervisor"
 
 
def route_after_approval(state: AgentState) -> str:
    if state.get("human_approved"):
        return "executor"
    return "supervisor"
 
 
def route_executor(state: AgentState) -> str:
    if state.get("final_report"):
        return END
    return "executor"
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Graph builder
# ─────────────────────────────────────────────────────────────────────────────
 
def build_graph(context: DatasetContext):
    """
    Build and compile the LangGraph workflow.
    Context is bound to nodes via closures.
    """
    def _supervisor(state): return supervisor_node(state, context)
    def _planner(state):    return planner_node(state, context)
    def _executor(state):   return executor_node(state, context)
 
    builder = StateGraph(AgentState)
 
    builder.add_node("supervisor",     _supervisor)
    builder.add_node("planner",        _planner)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("executor",       _executor)
 
    builder.add_edge(START, "supervisor")
 
    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {"planner": "planner", END: END}
    )
    builder.add_conditional_edges(
        "planner",
        route_planner,
        {"human_approval": "human_approval", "supervisor": "supervisor"}
    )
    builder.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {"executor": "executor", "supervisor": "supervisor"}
    )
    builder.add_conditional_edges(
        "executor",
        route_executor,
        {"executor": "executor", END: END}
    )
 
    return builder.compile(checkpointer=InMemorySaver())