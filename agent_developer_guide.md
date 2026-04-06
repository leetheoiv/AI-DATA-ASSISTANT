# AI Data Agent Framework
### Developer Guide: Adding New Agents

> Follow these steps sequentially. Each step depends on the one before it.

---

## Step 0 — Context Mapping *(The Grounding)*

Before writing a single line of code, identify exactly what your new agent needs to know from the `DatasetContext` object.

**Action:**
- Open `app/context/dataset_context.py` and review all available fields.
- List only the fields this agent actually needs (file path, column names, known issues, business rules).
- Avoid passing the full context object if the agent only needs two fields — this reduces prompt bloat and token cost.

> **Goal:** Prevent context bloat. Only ground the agent in the metadata it will actually use.

---

## Step 1 — Data Contract *(The Schema)*

Define a Pydantic model for your agent's structured output. This is the contract between your agent and the rest of the pipeline.

**Action:** Create your output model inside `app/agents/your_agent.py`

```python
from pydantic import BaseModel

class YourAgentResponse(BaseModel):
    thought_process: str        # Why this approach was chosen
    executable_code: str        # Raw output (no markdown fences)
    results_interpretation: str # What the output means in business terms
```

- Keep the model co-located with the agent class — it is that agent's contract, not a global schema.
- Use strict types. Avoid `Optional` fields unless genuinely optional.
- Every field must be specific enough that the LLM cannot misinterpret it.

> **Goal:** Force the LLM to return valid, parseable JSON. A hallucinated string crashes the pipeline — a Pydantic model does not.

---

## Step 2 — Prompt Orchestration *(The Blueprint)*

Draft a Jinja2 template in `app/prompt_templates/`. The prompt is the agent's personality and operating instructions — keep it separate from Python logic.

**Action:** Create `app/prompt_templates/your_agent_prompt_template.py`

```python
from jinja2 import Template

your_agent_prompt_template = Template("""
You are an expert [ROLE]. Your job is to [OBJECTIVE].

---
### DATASET CONTEXT
{{ dataset_context.to_prompt_block() }}

---
### YOUR CURRENT TASK
{{ current_task }}

{% if dataset_context.known_issues -%}
### KNOWN DATA QUALITY ISSUES
{% for issue in dataset_context.known_issues -%}
- {{ issue }}
{% endfor %}
{%- endif %}

---
### STRICT RULES
- Never reference columns not in the Dataset Context.
- Never leave output fields empty.
""")
```

- Use `{% if %}` blocks to conditionally inject context — don't always dump everything.
- Put hard rules at the bottom of the prompt. The model attends to them most strongly when they appear last.
- Be specific in task descriptions — vague instructions produce vague outputs.

> **Goal:** Keep system instructions modular and testable. A prompt in a template is easy to version, edit, and A/B test without touching agent logic.

---

## Step 3 — Agent Implementation *(The Brain)*

Build the specialized agent class in `app/agents/`. It inherits `AIAgent` and adds its own `run_task()` method with the appropriate lifecycle.

**Action:** Create `app/agents/your_agent.py`

```python
from app.agent import AIAgent
from app.prompt_templates.your_agent_prompt_template import your_agent_prompt_template
from pydantic import BaseModel

class YourAgentResponse(BaseModel):
    thought_process: str
    result: str

class YourAgent(AIAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run_task(self, task: str, context_data) -> tuple:
        self.reset()  # Always reset before a new task

        # Set system prompt after reset
        self.system_prompt = your_agent_prompt_template.render(
            current_task=task,
            dataset_context=context_data
        )

        _, parsed_response, _ = self.ask(
            user_prompt=task,
            response_model=YourAgentResponse
        )

        return parsed_response
```

- Always call `self.reset()` at the top of `run_task()` — this clears `input_list` and `history` to prevent state bleed between tasks.
- Set `self.system_prompt` after `reset()`, not before.
- **Stateless agents** (one-shot): reset at the top of every `run_task()`. **Stateful agents** (retry loops): reset per task, not per retry.

> **Goal:** Encapsulate the agent's personality, settings, and lifecycle in one class. The Orchestrator should not need to know how an agent works internally.

---

## Step 4 — Pipeline Integration *(The Routing)*

Register the new agent in the Orchestrator so the Supervisor can route tasks to it.

**Action:** Update `app/orchestrator.py`

```python
from app.agents.your_agent import YourAgent

class Orchestrator:
    def __init__(self, context_data, api_key):
        self.supervisor  = Supervisor(context_data=context_data, api_key=api_key, ...)
        self.coder       = Coder(api_key=api_key, ...)
        self.visualizer  = Visualizer(api_key=api_key, ...)
        self.your_agent  = YourAgent(api_key=api_key, ...)  # ← Register here

    def _route(self, task: AnalysisTask):
        if task.agent == "coder":      return self.coder.run_task(task.task_description, ...)
        if task.agent == "visualizer": return self.visualizer.run_task(task.task_description, ...)
        if task.agent == "your_agent": return self.your_agent.run_task(task.task_description, ...)
        raise ValueError(f"Unknown agent: {task.agent}")
```

**Action:** Add the new agent name to the `Literal` type in `app/agents/supervisor.py`

```python
class AnalysisTask(BaseModel):
    agent: Literal["coder", "visualizer", "reporter", "your_agent"]  # ← Add here
```

**Action:** Update the Supervisor prompt to describe what the new agent does and when to use it.

> **Goal:** The Supervisor acts as project manager — it should know the agent exists and what it does. The Orchestrator handles the actual handoff.

---

## Step 5 — Evaluation & Audit *(The Feedback Loop)*

Every agent run should produce a log entry. This is how you diagnose failures, refine prompts, and track token costs over time.

**Action:** Add logging to `run_task()` in your agent

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def _log_run(self, task, parsed_response, output, status):
    logger.info(json.dumps({
        "agent":         self.__class__.__name__,
        "timestamp":     datetime.utcnow().isoformat(),
        "task":          task,
        "status":        status,            # "success" | "failure"
        "tokens_used":   self.tokens_used,
        "output_preview": str(output)[:300] if output else None
    }, indent=2))
```

- Log at minimum: agent name, task, status, tokens used, and a truncated output preview.
- On failure, log the full error message and the prompt that caused it — this is how you trace back to Step 2 and fix the template.
- Review logs after every new agent's first 5–10 runs before trusting it in production.

> **Goal:** The feedback loop closes here. Bad output → trace back to the prompt template (Step 2) or the schema (Step 1) and iterate.

---

## Quick Reference

| Step | Action | File |
|------|--------|------|
| 0 | Map DatasetContext fields needed | `app/context/dataset_context.py` |
| 1 | Define Pydantic output model | `app/agents/your_agent.py` |
| 2 | Write Jinja2 prompt template | `app/prompt_templates/your_agent_prompt_template.py` |
| 3 | Implement agent class with `run_task()` | `app/agents/your_agent.py` |
| 4 | Register in Orchestrator + update Supervisor `Literal` + update Supervisor prompt | `app/orchestrator.py` + `app/agents/supervisor.py` |
| 5 | Add logging to `run_task()` | `app/agents/your_agent.py` + `/logs/` |
