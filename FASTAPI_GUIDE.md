# How to Use the AI Data Assistant via FastAPI

This guide provides step-by-step instructions for using the AI Data Assistant through its FastAPI endpoints. The assistant uses an AI-powered agent orchestration system to analyze datasets, generate execution plans, and produce insights.

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [API Endpoints](#api-endpoints)
4. [Step-by-Step Workflow](#step-by-step-workflow)
5. [Request/Response Examples](#requestresponse-examples)
6. [Session Management](#session-management)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Data Assistant operates through a **Human-in-the-Loop (HITL)** workflow:

1. **Start**: Submit your dataset context and questions
2. **Plan**: The Supervisor agent creates an analysis plan
3. **Review**: You review and optionally modify the plan
4. **Execute**: The orchestrator runs all planned analyses
5. **Audit**: Results are evaluated for quality
6. **Finalize**: Corrections are applied and a final report is generated

### Key Components

- **Supervisor**: Creates the initial analysis plan
- **Coder**: Executes Python analyses on the data
- **Visualizer**: Generates plots and visualizations
- **Reporter**: Compiles findings into a structured report
- **Auditor/Evaluator**: Validates results and suggests corrections

---

## Setup

### Prerequisites

- Python 3.8+
- FastAPI installed (`pip install fastapi`)
- Uvicorn installed (`pip install uvicorn`)
- OpenAI API key set in `.env` file

### Starting the Server

```bash
# Navigate to the repository root
cd /path/to/AI-DATA-ASSISTANT

# Activate virtual environment (if using one)
source venv/bin/activate

# Start the FastAPI server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The server will start at `http://127.0.0.1:8000`

### API Documentation

FastAPI automatically generates interactive API documentation at:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## API Endpoints

All endpoints are prefixed with `/analysis/`

### 1. Start Analysis

**Endpoint**: `POST /analysis/start-analysis`

Initiates a new analysis session and generates an initial plan.

**Request Body**:

```json
{
  "dataset_context": {
    "file_path": "path/to/dataset.csv",
    "dataset_description": "Description of what the dataset contains",
    "column_descriptions": {
      "column_name": "Description of this column",
      "another_column": "What this column represents"
    },
    "business_rules": [
      "Rule 1: how to interpret certain metrics",
      "Rule 2: domain-specific constraints"
    ],
    "sensitivity": "internal",
    "known_issues": ["Any known data quality issues"]
  },
  "user_questions": [
    "Your first analysis question",
    "Your second analysis question"
  ],
  "overall_goal": "High-level objective for the analysis"
}
```

**Response**: An `AnalysisPlan` object with:

- `session_id`: Unique identifier for this analysis session
- `tasks`: List of planned analysis tasks
- `task_descriptions`: Description of each task
- Other plan metadata

**Status Code**: 200 (if successful), 500 (if error)

---

### 2. Approve Plan

**Endpoint**: `POST /analysis/approve-plan/{session_id}`

Approves the generated plan and starts execution in the background.

**Path Parameters**:

- `session_id` (string): The session ID returned from `/start-analysis`

**Request Body**:

```json
{
  "plan": {
    "session_id": "uuid-from-start-analysis",
    "tasks": ["Task 1", "Task 2", ...],
    "task_descriptions": ["Description 1", "Description 2", ...],
    // ... other plan fields
  }
}
```

**Response**:

```json
{
  "status": "success",
  "message": "Plan approved. Agents are now executing tasks in the background.",
  "session_id": "your-session-id"
}
```

**Status Code**: 200 (if successful), 404 (if session not found)

---

### 3. Audit Results

**Endpoint**: `POST /analysis/audit-results/{session_id}`

Evaluates the completed analysis results for quality and identifies any issues.

**Path Parameters**:

- `session_id` (string): The session ID from your analysis

**Request Body**: Empty `{}`

**Response**:

```json
{
  "is_passed": true,
  "plan": {
    // Updated plan with audit results and any corrections
  }
}
```

**Status Code**: 200 (if successful), 404 (if session not found)

---

### 4. Finalize

**Endpoint**: `POST /analysis/finalize/{session_id}`

Applies evaluator corrections (if needed) and generates the final report.

**Path Parameters**:

- `session_id` (string): The session ID from your analysis

**Request Body**:

```json
{
  "is_passed": true,
  "plan": {
    // The (possibly corrected) plan from audit-results
  }
}
```

**Response**:

```json
{
  "message": "Applying corrections and generating final report..."
}
```

**Status Code**: 200, 404 (if session not found)

---

## Step-by-Step Workflow

### Complete Example Workflow

#### Step 1: Start a New Analysis

```bash
curl -X POST "http://127.0.0.1:8000/analysis/start-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_context": {
      "file_path": "app/tests/test_datasets/churn.csv",
      "dataset_description": "Monthly churn snapshot for Q3 2024.",
      "column_descriptions": {
        "churn": "1 = churned (bad), 0 = retained",
        "credits": "Billing credits — high values indicate disputes",
        "plan_type": "Subscription tier: prepaid, postpaid, enterprise"
      },
      "business_rules": [
        "credits: high = bad — indicates billing disputes or failures",
        "churn: 1 = bad outcome, 0 = good",
        "arpu: higher = better"
      ],
      "sensitivity": "internal",
      "known_issues": []
    },
    "user_questions": [
      "What is the correlation between billing credits and churn?",
      "How does churn differ between plan types?"
    ],
    "overall_goal": "Provide data-driven insights into churn drivers"
  }'
```

**Save the returned `session_id`** — you'll need it for the next steps.

Example response:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "tasks": ["Exploratory Data Analysis", "Correlation Analysis", ...],
  "task_descriptions": ["Examine basic statistics...", "Calculate correlations..."],
  // ... other plan fields
}
```

#### Step 2: Review and Approve the Plan

The plan returned in Step 1 shows what the Supervisor agent intends to do. You can:

- Review it in your application UI
- Modify task descriptions or order if needed
- Approve it to begin execution

```bash
curl -X POST "http://127.0.0.1:8000/analysis/approve-plan/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "tasks": ["Exploratory Data Analysis", "Correlation Analysis", ...],
    "task_descriptions": ["...", "...", ...],
    // ... include all plan fields from Step 1 response
  }'
```

Response indicates execution has started in the background:

```json
{
  "status": "success",
  "message": "Plan approved. Agents are now executing tasks in the background.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Step 3: Wait for Execution to Complete

The agents run in the background. In a real application, you would:

- Poll the session status at intervals
- Use WebSockets or push notifications to alert when ready
- Display a progress indicator to the user

Execution time depends on:

- Dataset size
- Number and complexity of questions
- API response times

#### Step 4: Audit the Results

Once execution is complete, evaluate the quality of results:

```bash
curl -X POST "http://127.0.0.1:8000/analysis/audit-results/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response:

```json
{
  "is_passed": true,
  "plan": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "audit_notes": "Results are high quality...",
    "tasks": [...],
    // ... updated plan with audit feedback
  }
}
```

If `is_passed` is `false`, the plan will include suggested corrections.

#### Step 5: Finalize and Generate Report

Apply any corrections and create the final report:

```bash
curl -X POST "http://127.0.0.1:8000/analysis/finalize/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "is_passed": true,
    "plan": {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "tasks": [...],
      "task_descriptions": [...],
      // ... include the complete plan from Step 4
    }
  }'
```

Response:

```json
{
  "message": "Applying corrections and generating final report..."
}
```

The final report will be available in the orchestrator's `report` attribute.

---

## Request/Response Examples

### Example: Using Python Requests

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000/analysis"

# Step 1: Start Analysis
start_payload = {
    "dataset_context": {
        "file_path": "app/tests/test_datasets/churn.csv",
        "dataset_description": "Monthly churn snapshot for Q3 2024.",
        "column_descriptions": {
            "churn": "1 = churned (bad), 0 = retained",
            "credits": "Billing credits — high values indicate disputes",
            "plan_type": "Subscription tier: prepaid, postpaid, enterprise"
        },
        "business_rules": [
            "credits: high = bad — indicates billing disputes or failures",
            "churn: 1 = bad outcome, 0 = good",
            "arpu: higher = better"
        ],
        "sensitivity": "internal",
        "known_issues": []
    },
    "user_questions": [
        "What is the correlation between billing credits and churn?",
        "How does churn differ between plan types?"
    ],
    "overall_goal": "Provide data-driven insights"
}

response = requests.post(f"{BASE_URL}/start-analysis", json=start_payload)
print(f"Status: {response.status_code}")
plan = response.json()
session_id = plan["session_id"]
print(f"Session ID: {session_id}")

# Step 2: Approve Plan
approve_payload = {**plan}  # Use the plan returned from start-analysis
response = requests.post(f"{BASE_URL}/approve-plan/{session_id}", json=approve_payload)
print(f"Approval Status: {response.status_code}")
print(response.json())

# Step 3: Wait for execution
# In a production app, implement polling or event-based notification
import time
time.sleep(10)  # Wait for agents to process

# Step 4: Audit Results
response = requests.post(f"{BASE_URL}/audit-results/{session_id}", json={})
print(f"Audit Status: {response.status_code}")
audit_result = response.json()
print(json.dumps(audit_result, indent=2))

# Step 5: Finalize
finalize_payload = {
    "is_passed": audit_result["is_passed"],
    "plan": audit_result["plan"]
}
response = requests.post(f"{BASE_URL}/finalize/{session_id}", json=finalize_payload)
print(f"Finalize Status: {response.status_code}")
print(response.json())
```

### Example: Using JavaScript/Fetch

```javascript
const BASE_URL = "http://127.0.0.1:8000/analysis";

async function runAnalysis() {
  // Step 1: Start Analysis
  const startPayload = {
    dataset_context: {
      file_path: "app/tests/test_datasets/churn.csv",
      dataset_description: "Monthly churn snapshot for Q3 2024.",
      column_descriptions: {
        churn: "1 = churned (bad), 0 = retained",
        credits: "Billing credits — high values indicate disputes",
        plan_type: "Subscription tier: prepaid, postpaid, enterprise",
      },
      business_rules: [
        "credits: high = bad — indicates billing disputes or failures",
        "churn: 1 = bad outcome, 0 = good",
        "arpu: higher = better",
      ],
      sensitivity: "internal",
      known_issues: [],
    },
    user_questions: [
      "What is the correlation between billing credits and churn?",
      "How does churn differ between plan types?",
    ],
    overall_goal: "Provide data-driven insights",
  };

  const startResponse = await fetch(`${BASE_URL}/start-analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(startPayload),
  });

  const plan = await startResponse.json();
  const sessionId = plan.session_id;
  console.log("Session ID:", sessionId);

  // Step 2: Approve Plan
  const approveResponse = await fetch(`${BASE_URL}/approve-plan/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(plan),
  });

  const approveResult = await approveResponse.json();
  console.log("Approve Result:", approveResult);

  // Step 3: Wait for execution
  await new Promise((resolve) => setTimeout(resolve, 10000));

  // Step 4: Audit Results
  const auditResponse = await fetch(`${BASE_URL}/audit-results/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });

  const auditResult = await auditResponse.json();
  console.log("Audit Result:", auditResult);

  // Step 5: Finalize
  const finalizeResponse = await fetch(`${BASE_URL}/finalize/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      is_passed: auditResult.is_passed,
      plan: auditResult.plan,
    }),
  });

  const finalizeResult = await finalizeResponse.json();
  console.log("Finalize Result:", finalizeResult);
}

runAnalysis();
```

---

## Session Management

### Session Storage

Currently, sessions are stored in-memory in the `active_orchestrators` dictionary. This means:

- Sessions are lost when the server restarts
- Only one instance of the application can be run

### Production Considerations

For production, consider:

1. **Persistent Storage**: Move sessions to Redis or a database

```python
# Example: Using Redis
import redis
redis_client = redis.Redis(host='localhost', port=6379)
active_orchestrators = redis_client  # Store orchestrator objects
```

2. **Session Timeout**: Add expiration for long-running sessions

```python
@router.get("/session/{session_id}")
def get_session_status(session_id: str):
    orchestrator = active_orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "status": "planning" | "executing" | "auditing" | "finalizing" | "complete",
        "created_at": "...",
        "last_updated": "..."
    }
```

3. **Authentication**: Add API key or OAuth authentication

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/start-analysis")
async def start_analysis(request: AnalysisRequest, credentials = Depends(security)):
    # Validate credentials
    pass
```

---

## Troubleshooting

### Common Issues

#### 1. Session Not Found (404 Error)

**Problem**: `"detail": "Analysis session not found."`

**Causes**:

- Server was restarted (sessions are lost)
- Session ID is incorrect
- Session expired

**Solution**:

- Verify the session ID is correct
- Start a new analysis if the server was restarted

#### 2. Timeout Errors

**Problem**: Request times out waiting for response

**Causes**:

- Large dataset taking too long to process
- API rate limits hit
- Network connectivity issues

**Solution**:

- Use background tasks (already implemented in `/approve-plan`)
- Monitor agent execution logs in `logs/agent.log`
- Increase request timeout in your client

#### 3. API Key Error

**Problem**: `"Error: OPENAI_API_KEY not found"`

**Causes**:

- `.env` file not created or not in root directory
- `OPENAI_API_KEY` not set in environment

**Solution**:

```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=sk-..." > .env
```

#### 4. File Not Found Error

**Problem**: `"FileNotFoundError: dataset file not found"`

**Causes**:

- `dataset_context.file_path` is incorrect
- File doesn't exist at the specified path

**Solution**:

- Use absolute paths or paths relative to the project root
- Verify the file exists:
  ```bash
  ls -la app/tests/test_datasets/churn.csv
  ```

#### 5. Invalid Request Format

**Problem**: `"validation error"`

**Causes**:

- Missing required fields in request body
- Incorrect data types

**Solution**:

- Check the request schema in the API docs at `/docs`
- Ensure all required fields are present
- Use the examples provided in this guide

### Debugging Tips

1. **Check Server Logs**:

```bash
# Watch for errors in real-time
tail -f logs/agent.log
```

2. **Enable Debug Mode** (in your client):

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

3. **Use API Docs**:

- Visit `http://127.0.0.1:8000/docs` to test endpoints interactively
- Try requests directly in Swagger UI

4. **Inspect Agent Output**:

- Check `app/logs/` directory for detailed agent logs
- Check `app/ai_output_imgs/` for generated visualizations

---

## Best Practices

1. **Validate Input Data**
   - Ensure dataset paths are correct
   - Provide clear, specific questions
   - Include relevant business rules and column descriptions

2. **Handle Long-Running Tasks**
   - Always use `/approve-plan` endpoint (not just direct execution)
   - Implement polling or event notifications for execution status
   - Set appropriate request timeouts in your client

3. **Error Handling**
   - Wrap API calls in try-catch blocks
   - Log all responses for debugging
   - Provide user feedback on errors

4. **Session Management**
   - Store session IDs for later reference
   - Consider implementing a session dashboard
   - Clean up old sessions periodically (for future persistence)

5. **Testing**
   - Use the included test datasets in `app/tests/test_datasets/`
   - Start with simple questions before complex analyses
   - Validate results independently

---

## Additional Resources

- **OpenAI Documentation**: https://platform.openai.com/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Project Repository**: See `README.md` and `agent_developer_guide.md`

---

## Support

For issues or questions:

1. Check this guide's Troubleshooting section
2. Review logs in `app/logs/agent.log`
3. Check FastAPI docs at `/docs` endpoint
4. Refer to `agent_developer_guide.md` for internal architecture
