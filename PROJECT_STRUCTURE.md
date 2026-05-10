# Project Overview & Architecture Guide

This document describes the AI Data Assistant project structure, purpose of each folder and file, and how the system works end-to-end.

## Table of Contents

1. [Project Purpose](#project-purpose)
2. [How to Use This Project](#how-to-use-this-project)
3. [System Architecture](#system-architecture)
4. [Directory Structure](#directory-structure)
5. [Key Components Explained](#key-components-explained)
6. [Data Flow](#data-flow)
7. [Configuration & Setup](#configuration--setup)

---

## Project Purpose

The **AI Data Assistant** is an AI-powered data analysis system that:

- **Accepts datasets** (CSV, JSON, etc.) from users
- **Automatically generates analysis plans** based on user questions
- **Executes analyses in the background** using AI agents
- **Produces audit-ready reports** with findings, visualizations, and recommendations
- **Maintains human control** throughout the process (Human-in-the-Loop design)

### Key Features

✅ **Agent-based architecture** — Multiple specialized AI agents work together  
✅ **Human-in-the-Loop** — Users review and approve plans before execution  
✅ **Structured outputs** — All responses follow Pydantic models for reliability  
✅ **Tool-use execution** — Agents can write and execute Python code independently  
✅ **Rich reporting** — Automatically generates PowerPoint reports with findings  
✅ **FastAPI integration** — RESTful API for programmatic access  
✅ **Extensible design** — Easy to add new agents and capabilities  

---

## How to Use This Project

### Use Case 1: As a Standalone API

Start the FastAPI server and make HTTP requests:

```bash
uvicorn main:app --reload --port 8000
```

Then use any HTTP client (curl, Postman, Python requests) to interact with the endpoints. See [FASTAPI_GUIDE.md](FASTAPI_GUIDE.md) for complete API documentation.

### Use Case 2: As a Streamlit Web Application

(When Streamlit components are fully integrated):

```bash
streamlit run main.py
```

This provides a user-friendly web interface for uploading datasets, asking questions, and reviewing results.

### Use Case 3: As a Python Library

Import and use the agents directly in your code:

```python
from app.agents.orchestrator import AnalysisOrchestrator
from app.agents.supervisor import Supervisor
from app.agents.coder import Coder
from app.structured_outputs.context import DatasetContext

# Create context
dataset_context = DatasetContext(
    file_path="data/churn.csv",
    dataset_description="Customer churn data",
    column_descriptions={...},
    business_rules=[...]
)

# Create agents and orchestrator
supervisor = Supervisor(api_key="sk-...", model="gpt-4o-mini")
coder = Coder(api_key="sk-...", model="gpt-4o-mini")
# ... (create other agents)

orchestrator = AnalysisOrchestrator(
    supervisor=supervisor,
    coder=coder,
    # ... other agents
    dataset_context=dataset_context
)

# Run analysis
plan = orchestrator.generate_initial_plan(["What drives churn?"])
# ... (approve plan, execute, audit, finalize)
```

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI / Streamlit                      │
│                    (User Interface)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌────────▼─────────┐
│  AnalysisRequest │    │ ApprovalRequest  │
│                  │    │                  │
│  - dataset_ctx   │    │  - session_id    │
│  - questions     │    │  - approved_plan │
└───────┬──────────┘    └────────┬────────┘
        │                        │
        └────────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │ AnalysisOrchestrator    │  ◄─ Core Engine
        │  (Main Coordinator)     │
        └────────────┬────────────┘
                     │
        ┌────────────┴──────────────────────┐
        │                                   │
    ┌───▼────┐  ┌─────────┐  ┌─────────┐  ┌▼──────────┐
    │Supervisor│  │Coder    │  │Visualizer│  │Reporter   │
    │(Planning)│  │(Execution)│ │(Charts) │  │(Synthesis)│
    └────────┘  └─────────┘  └─────────┘  └──────────┘
                     │
           ┌─────────▼─────────┐
           │ execute_code()    │
           │ (Python sandbox)  │
           └───────────────────┘
```

### The 5-Phase Workflow

```
Phase 1: PLANNING
  └─> Supervisor creates analysis plan from user questions

Phase 2: HUMAN APPROVAL
  └─> User reviews & approves plan (or modifies it)

Phase 3: EXECUTION
  └─> Coder & Visualizer agents execute planned tasks
  └─> Each task runs in a sandbox with access to the dataset

Phase 4: EVALUATION
  └─> Auditor evaluates results for quality & completeness
  └─> Suggests corrections if needed

Phase 5: FINALIZATION
  └─> Reporter synthesizes findings into a structured report
  └─> Report is formatted for export (PDF, PowerPoint)
```

---

## Directory Structure

Below is a detailed explanation of every folder and file in the project.

### Root Level

```
AI-DATA-ASSISTANT/
├── main.py                      # FastAPI application entry point
├── pyproject.toml               # Python package configuration
├── requirements.txt             # Project dependencies
├── README.md                    # Quick project overview
├── agent_developer_guide.md     # Guide for adding new agents
├── FASTAPI_GUIDE.md             # API usage documentation
├── MANUAL.md                    # This file
├── .env                         # Environment variables (API keys, etc.)
└── venv/                        # Python virtual environment
```

**Key Files:**

- **`main.py`** — FastAPI application factory. Creates the app instance and includes all routers. Start here if using the API.
- **`pyproject.toml`** — Defines project metadata (name, version) and setuptools configuration for package installation.
- **`requirements.txt`** — Lists all Python package dependencies (pandas, pydantic, openai, etc.).
- **`.env`** — Environment variables (not in version control). Must contain `OPENAI_API_KEY=sk-...`

---

### `/app` — Main Application Package

Contains all the core logic organized into logical modules.

```
app/
├── __init__.py                  # Package initialization
├── agent.py                     # Base AIAgent class (parent of all agents)
├── settings.py                  # Configuration management
├── examples.py                  # Example usage code
├── agents/                      # Individual agent implementations
├── api/                         # FastAPI routes & request/response schemas
├── database/                    # Database models (for storing logs, results)
├── logs/                        # Agent execution logs
├── prompt_templates/            # Jinja2 templates for agent system prompts
├── reports/                     # Generated analysis reports
├── structured_outputs/          # Pydantic models for agent responses
├── support_functions/           # Utility functions (dataset info, HITL)
├── tests/                       # Test files & datasets
└── tools/                       # Tools agents can use (code execution, PDF building)
```

---

### `/app/agents` — Specialized AI Agents

Each agent is a specialized worker that handles one aspect of the analysis pipeline.

```
app/agents/
├── __init__.py
├── supervisor.py                # Supervisor Agent - Creates analysis plans
├── coder.py                     # Coder Agent - Writes and executes Python code
├── visualizer.py                # Visualizer Agent - Creates charts & graphs
├── reporter.py                  # Reporter Agent - Synthesizes findings into reports
├── auditor.py                   # Auditor/Evaluator Agent - Validates results
└── orchestrator.py              # AnalysisOrchestrator - Coordinates all agents
```

**Agent Purposes:**

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| **Supervisor** | Creates a high-level analysis plan from user questions | User questions, dataset context | `AnalysisPlan` (list of tasks) |
| **Coder** | Writes Python code to analyze data and executes it | Task description, dataset context | `CoderResponse` (code, results) |
| **Visualizer** | Creates charts and plots from data | Task description, analysis results | `VisualizerResponse` (chart files) |
| **Reporter** | Synthesizes all findings into a polished report | All task results, visualizations | `ReporterResponse` (structured report) |
| **Auditor** | Evaluates result quality and suggests corrections | All task results, original plan | `AuditorResponse` (pass/fail + corrections) |
| **Orchestrator** | Directs the entire workflow | User input, orchestrates other agents | Coordinates all phases |

**Key Agent Files:**

- **`supervisor.py`** — Implemented in `Supervisor` class. Accepts user questions, produces structured analysis plan via LLM call.
- **`coder.py`** — Implemented in `Coder` class. Writes Python code, executes it in a sandbox, handles retries on failure.
- **`visualizer.py`** — Implemented in `Visualizer` class. Generates matplotlib/seaborn visualizations.
- **`orchestrator.py`** — Implemented in `AnalysisOrchestrator` class. Manages the 5-phase workflow. Main entry point after user input.

---

### `/app/api` — REST API Layer

Exposes agent functionality via FastAPI endpoints.

```
app/api/
├── __init__.py
├── router.py                    # Main router - combines all sub-routers
└── endpoint.py                  # Endpoint handlers for /analysis/* routes
```

**Key Files:**

- **`router.py`** — Creates an APIRouter and includes the endpoint router at `/analysis/` prefix.
- **`endpoint.py`** — Defines all endpoints:
  - `POST /analysis/start-analysis` — Kick off a new analysis session
  - `POST /analysis/approve-plan/{session_id}` — Approve and execute plan
  - `POST /analysis/audit-results/{session_id}` — Evaluate results
  - `POST /analysis/finalize/{session_id}` — Generate final report

**Request/Response Classes:**

- `EventSchema` — Generic event structure (for future extensibility)
- `AnalysisRequest` — Payload for `/start-analysis`
- `AnalysisSession` — In-memory session tracking

---

### `/app/prompt_templates` — LLM Prompts

Jinja2 templates defining system prompts for each agent. Separating prompts from code makes them easy to version and edit.

```
app/prompt_templates/
├── __init__.py
├── coder_prompt_template.py            # System prompt for Coder agent
├── evaluator_prompt_template.py        # System prompt for Auditor agent
├── reporter_prompt_template.py         # System prompt for Reporter agent
├── supervisor_prompt_template.py       # System prompt for Supervisor agent
├── supervisor_corrective_planning_template.py  # Follow-up prompt for plan corrections
└── visualizer_prompt_template.py       # System prompt for Visualizer agent
```

**How They Work:**

Each template is a Python file containing a Jinja2 `Template` object:

```python
# Example from coder_prompt_template.py
supervisor_prompt_template = Template("""
You are an expert data coder. Your job is to write Python code that answers the user's question.

---
### DATASET CONTEXT
{{ dataset_context.to_prompt_block() }}

---
### YOUR CURRENT TASK
{{ current_task }}

### STRICT RULES
- Never reference columns that don't exist in the dataset.
...
""")
```

The template is rendered at runtime with dynamic values (context, task description, etc.).

---

### `/app/structured_outputs` — Pydantic Response Models

Defines the contract between agents and the rest of the system. Each model ensures LLM outputs can be reliably parsed.

```
app/structured_outputs/
├── __init__.py
├── context.py                           # DatasetContext model
├── coder_structured_output.py           # CoderResponse model
├── evaluator_structured_output.py       # EvaluatorResponse model
├── reporter_structured_output.py        # ReporterResponse model
├── supervisor_structured_output.py      # AnalysisPlan model
└── visualizer_structured_output.py      # VisualizerResponse model
```

**Key Models:**

- **`DatasetContext`** — Metadata about the dataset (file path, column descriptions, business rules). Passed to all agents.
- **`AnalysisPlan`** — List of analysis tasks + descriptions. Output of Supervisor.
- **`CoderResponse`** — Python code + execution results. Output of Coder.
- **`VisualizerResponse`** — Chart files + descriptions. Output of Visualizer.
- **`ReporterResponse`** — Structured report with findings. Output of Reporter.
- **`EvaluatorResponse`** — Audit results + corrections. Output of Auditor.

**Why Pydantic?**

Pydantic models:
- Validate LLM output and raise structured errors if invalid
- Auto-convert JSON to Python objects
- Provide type hints for IDE support
- Prevent hallucinated fields from crashing the pipeline

---

### `/app/tools` — Executable Tools for Agents

Tools that agents can use to accomplish their tasks.

```
app/tools/
├── __init__.py
├── execute_code.py              # Safely executes Python code in a sandbox
├── create_tool.py               # (Placeholder for future tool creation)
└── pdf_builder.py               # Generates PDF reports
```

**Key Tools:**

- **`execute_code.py`** — `execute_code(code, language, file_path, namespace)` function. Runs Python code in an isolated namespace to prevent side effects. Used by Coder and Visualizer agents.
- **`pdf_builder.py`** — Generates PDF reports from analysis results. Used by Reporter agent.

---

### `/app/support_functions` — Utility Functions

Helper functions used throughout the system.

```
app/support_functions/
├── __init__.py
├── db_interaction.py            # Database operations (storing logs, results)
├── db_interactor.ipynb          # (Jupyter notebook for DB experiments)
├── get_dataset_info.py          # (Empty placeholder)
└── human_in_the_loop.py         # HITL implementation for interactive approvals
```

**Key Functions:**

- **`human_in_the_loop.py`** — `HITL` class that handles user interaction (approval, modifications) during the workflow.
- **`db_interaction.py`** — Database operations for logging errors and storing results.

---

### `/app/database` — Data Models for Storage

SQLAlchemy models for persistent storage.

```
app/database/
├── models/
│   ├── __init__.py
│   └── errors.py                # ErrorLog model - stores execution errors
```

**Key Models:**

- **`ErrorLog`** — Stores agent errors for debugging. Fields: `session_id`, `agent_name`, `error_snippet`, `created_at`.

---

### `/app/tests` — Test Files & Datasets

Test code and sample datasets for development and validation.

```
app/tests/
├── test_environment.py          # Tests to verify setup
├── testing.ipynb                # Jupyter notebook for manual testing
├── fastapi_server_tests/        # FastAPI endpoint tests
│   └── churn_dataset_tests.json # Example request payload
├── logs/                        # Test execution logs
└── test_datasets/
    ├── churn.csv                # Sample: Customer churn data
    ├── healthcare_synthesis.json # Sample: Healthcare data
    └── mock_healthcare_churn.csv # Sample: Health + churn combined
```

**How to Use:**

```bash
# Run the test environment check
python app/tests/test_environment.py

# Use test datasets in API requests
curl -X POST http://localhost:8000/analysis/start-analysis \
  -d @app/tests/fastapi_server_tests/churn_dataset_tests.json
```

---

### `/app/api_output_imgs` — Generated Visualizations

Directory where Coder and Visualizer agents save generated plots and charts.

```
app/ai_output_imgs/
└── (Dynamic) *.png, *.jpg files created during analysis
```

---

### `/app/reports` — Generated Reports

Directory where Reporter agent saves final analysis reports.

```
app/reports/
└── (Dynamic) *.pdf, *.pptx files created during analysis
```

---

### `/app/logs` — Execution Logs

Application logs for debugging and monitoring.

```
app/logs/
├── agent.log                    # Agent execution logs (appended continuously)
└── (Other logs as created)
```

**To view logs:**

```bash
tail -f app/logs/agent.log
```

---

### `/config` — Application Configuration

Configuration files and settings.

```
config/
└── streamlit_settings.py        # Settings for Streamlit UI (future)
```

---

### `/` — Root-Level Support Files

```
├── README.md                    # High-level project overview
├── agent_developer_guide.md     # How to add new agents
└── FASTAPI_GUIDE.md             # API usage guide
```

---

## Key Components Explained

### 1. The Base Agent Class (`agent.py`)

All agents inherit from `AIAgent`, which handles:

- **Conversation state** — Maintains message history for multi-turn interactions
- **LLM integration** — Calls OpenAI API with structured responses
- **Retry logic** — Automatically retries failed requests
- **Schema validation** — Uses Pydantic for output validation

```python
class AIAgent:
    def __init__(self, api_key, model="gpt-4o-mini", temperature=0.3, max_retries=3):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.input_list = []  # Conversation history
        
    def ask(self, response_model, user_prompt=None):
        """Call LLM and return structured response"""
        # ... (implementation details)
```

### 2. DatasetContext (`structured_outputs/context.py`)

Immutable metadata about the dataset passed to all agents.

**Fields:**

- `file_path` — Location of the CSV/JSON file
- `dataset_description` — What the data represents
- `column_descriptions` — Mapping of column names to meanings
- `business_rules` — Domain-specific rules (e.g., "high churn = bad")
- `sensitivity` — Data classification (public/internal/sensitive)
- `known_issues` — Known data quality problems

**Why separate context from data?**

Passing context to every agent:
- Ensures consistent understanding of the data
- Prevents agents from making bad assumptions
- Reduces token usage (context is pre-computed)
- Improves grounding and accuracy

### 3. The Orchestrator (`agents/orchestrator.py`)

The "brain" that coordinates all agents and manages state.

**Responsibilities:**

- **Phase 1:** Call Supervisor to create a plan
- **Phase 2:** Wait for user approval (HITL)
- **Phase 3:** Call Coder/Visualizer to execute tasks
- **Phase 4:** Call Auditor to evaluate results
- **Phase 5:** Call Reporter to synthesize findings

**State Management:**

```python
class AnalysisOrchestrator:
    def __init__(self, supervisor, coder, visualizer, reporter, evaluator, ...):
        self.task_results = {}          # Output from each task
        self.shared_namespace = {...}   # Python variables shared across tasks
        self.plan = None                # Current analysis plan
        self.enriched_task_results = [] # Results + business interpretation
```

### 4. Code Execution Sandbox (`tools/execute_code.py`)

Safely runs Python code without affecting the rest of the system.

**Key Features:**

- **Namespace isolation** — Code runs in a local namespace, not global scope
- **Library pre-loading** — pandas, matplotlib, seaborn available by default
- **Output capture** — Stdout/stderr captured and returned
- **Error handling** — Exceptions caught and reported

```python
def execute_code(code, language="python", file_path=None, namespace=None):
    """
    Execute Python code in an isolated namespace.
    
    Returns:
        {
            "status": "success" | "error",
            "output": "captured stdout",
            "namespace": {...}  # Updated namespace after execution
        }
    """
```

---

## Data Flow

### Request → Response Flow

```
1. User submits AnalysisRequest via FastAPI
   ↓
2. Orchestrator.generate_initial_plan() called
   ↓
3. Supervisor.run_task() creates AnalysisPlan
   ↓
4. Plan returned to user for approval
   ↓
5. User calls /approve-plan endpoint
   ↓
6. Orchestrator.run_execution_loop() runs in background
   ├─ Loop through tasks in plan
   ├─ Call appropriate agent (Coder, Visualizer)
   ├─ Store results in task_results dict
   └─ Pass prereq outputs to dependent tasks
   ↓
7. User calls /audit-results endpoint
   ↓
8. Auditor.run_task() evaluates completeness
   ↓
9. User calls /finalize endpoint
   ↓
10. Reporter.run_task() synthesizes findings
    ↓
11. Report saved to app/reports/
    Return to user
```

### Data Transformation in Tasks

```
Input Task:
  {
    "task_id": 0,
    "task": "Calculate correlation between billing credits and churn",
    "dependencies": [],
    "agent_type": "coder"
  }
  ↓
Coder executes with context:
  - Dataset loaded in namespace
  - Column descriptions available
  - Business rules known
  ↓
Output result:
  {
    "executable_code": "df.corr()[['churn', 'credits']]",
    "execution_output": "0.42",
    "interpretation": "Moderate positive correlation indicates..."
  }
  ↓
Stored in orchestrator.task_results[0]
  ↓
Prereq data passed to dependent tasks (if any)
```

---

## Configuration & Setup

### Environment Variables (`.env`)

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=sk-...your-api-key-here...
```

### Loading Configuration

The `app/settings.py` module handles all configuration loading:

```python
from app.settings import AGENT_API_KEY  # This loads from .env

# Or manually
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

### Dependencies

See `requirements.txt` for the full list. Key packages:

```
OpenAI (Claude API client)
FastAPI (REST API framework)
Pydantic (Data validation)
Pandas (Data manipulation)
Matplotlib/Seaborn (Plotting)
SQLAlchemy (Database ORM)
Instructor (Structured output parsing)
```

### Virtual Environment

```bash
# Create
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Extending the Project

### Adding a New Agent

1. Follow steps in `agent_developer_guide.md`
2. Create `app/agents/your_agent.py` inheriting from `AIAgent`
3. Create `app/prompt_templates/your_agent_prompt_template.py` with Jinja2 template
4. Create `app/structured_outputs/your_agent_structured_output.py` with Pydantic models
5. Add to orchestrator in `app/agents/orchestrator.py`

### Adding a New API Endpoint

1. Add route to `app/api/endpoint.py`
2. Define request/response classes in the same file or `structured_outputs/`
3. New route automatically included via router in `app/api/router.py`

### Adding a New Tool

1. Create function in `app/tools/your_tool.py`
2. Import in agent that needs it
3. Call function during `run_task()`

---

## Summary

| What | Where | Purpose |
|------|-------|---------|
| **FastAPI app** | `main.py` | Entry point for HTTP requests |
| **Agents** | `app/agents/` | Specialized workers (Plan, Code, Visualize, Report, Audit) |
| **Prompts** | `app/prompt_templates/` | LLM system prompts for each agent |
| **Models** | `app/structured_outputs/` | Pydantic validation for LLM outputs |
| **API routes** | `app/api/` | REST endpoints (start, approve, audit, finalize) |
| **Tools** | `app/tools/` | Capabilities agents can use (code execution, PDF) |
| **Context** | `app/structured_outputs/context.py` | Dataset metadata shared to all agents |
| **Orchestrator** | `app/agents/orchestrator.py` | Coordinates 5-phase workflow |
| **Tests** | `app/tests/` | Sample datasets and test code |
| **Config** | `app/settings.py` | Environment variables and setup |

---

## Next Steps

- Read [FASTAPI_GUIDE.md](FASTAPI_GUIDE.md) to use the API
- Read [agent_developer_guide.md](agent_developer_guide.md) to add new agents
- Check `app/tests/` for example usage
- Start the server: `uvicorn main:app --reload`
