"""
graph.py

LangGraph workflow for the multi-agent data analysis system.

Current nodes:
  supervisor      — clarifies and improves the user's question
  planner         — inspects data and produces an analysis plan
  human_approval  — pauses for the user to approve/modify/delete steps
  execute_steps   — routes to the correct specialist agent for each step
  END             — workflow complete

Specialist agent nodes (coder, visualizer, stats, reporter) will be
added as they are built.

Usage:
    from graph import build_graph
    from workflow.state import AgentState
    from workflow.context import DatasetContext

    graph = build_graph()

    context = DatasetContext(
        file_path="data/churn.csv",
        dataset_description="Monthly churn snapshot Q3 2024.",
        column_descriptions={"churn": "1 = churned (bad), 0 = retained"},
        business_rules=["credits: high = bad"],
    )

    config = {"configurable": {"thread_id": "thread-1"}}

    # First invocation — runs until interrupt at human_approval
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": "What is the churn rate by plan type?"}],
            "improved_question": None,
            "plan": None,
            "human_approved": None,
            "current_step": None,
            "step_results": {},
            "final_report": None,
        },
        config=config,
        context=context,
    )

    # Show the plan to the user
    print(result.value["plan"])

    # Resume after human approves
    from langgraph.types import Command
    graph.invoke(Command(resume={"approved": True, "plan": result.value["plan"]}), config=config)
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage, AIMessage

from workflow.state import AgentState
from context import DatasetContext
from structured_outputs import SupervisorAction, PlannerAction, PlannerOutput
from agents.supervisor import run_supervisor
from agents.dataplanner import run_planner
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Node functions
# ─────────────────────────────────────────────────────────────────────────────
 
def supervisor_node(state: AgentState, context: DatasetContext) -> dict:
    """
    Parse all user questions, clarify if needed, improve and hand off.
    """
    messages = state.get("messages", [])
 
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
 
    # All questions clear — pass improved list to planner
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
    """
    improved_questions = state.get("improved_questions", [])
 
    # Join all questions into one prompt for the planner
    combined = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(improved_questions)
    )
    print('\n[Planner] Planning Analysis...')
    result = run_planner(
        improved_question=combined,
        context=context,
    )
 
    if result.is_clarify():
        return {
            "messages": [AIMessage(content=result.clarifying_question)],
            "improved_questions": None,
        }
    print('\n[Planner] Analysis plan created:')
    return {
        "messages": [AIMessage(
            content=f"Analysis plan ready — {len(result.steps)} steps covering {len(improved_questions)} question(s)."
        )],
        "plan": result,
        "current_step": 1,
        "step_results": {},
    }
 
 
def human_approval_node(state: AgentState) -> dict:
    """
    Pause for human review of the plan.
    Resume with Command(resume={"approved": True/False, "plan": ...})
    """
    plan = state.get("plan")
    
    print("\n[Planner] Pausing for human review of the plan...")
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
 
 
def placeholder_executor_node(state: AgentState) -> dict:
    """
    Placeholder for step execution.
    Will route to real coder/visualizer/stats/reporter agents.
    """
    plan = state.get("plan")
    current_step = state.get("current_step", 1)
    step_results = dict(state.get("step_results") or {})
 
    if not plan or not plan.steps:
        return {"final_report": "No steps to execute."}
 
    step = next((s for s in plan.steps if s.id == current_step), None)
    if step is None:
        return {"final_report": "All steps complete."}
 
    step_results[current_step] = (
        f"[Placeholder] Step {current_step} '{step.title}' "
        f"executed by {step.agent.value}"
    )
 
    next_step = current_step + 1
    is_last = next_step > len(plan.steps)
 
    return {
        "messages": [AIMessage(content=f"Step {current_step} complete: {step.title}")],
        "step_results": step_results,
        "current_step": next_step if not is_last else current_step,
        "final_report": "Analysis complete." if is_last else None,
    }
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Routing functions
# ─────────────────────────────────────────────────────────────────────────────
 
def route_supervisor(state: AgentState) -> str:
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
 
    Context is bound to nodes via closures so it doesn't need
    to live in the graph state.
    """
    def _supervisor(state): return supervisor_node(state, context)
    def _planner(state):    return planner_node(state, context)
 
    builder = StateGraph(AgentState)
 
    builder.add_node("supervisor",     _supervisor)
    builder.add_node("planner",        _planner)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("executor",       placeholder_executor_node)
 
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