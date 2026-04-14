"""
**Defines data models and endpoint logic for processing events**

Defines a Pydantic model EventSchema that validates incoming data
Creates an endpoint router
Defines a POST handler at / (which becomes /events/ when mounted in router.py)
Accepts and validates incoming data against our schema
Returns a JSON response with HTTP status code 202 (Accepted)
"""
from dotenv import load_dotenv
import json
import os
import pandas as pd
import uuid
from http import HTTPStatus
from fastapi import APIRouter,Depends, HTTPException,BackgroundTasks,Body
from pydantic import BaseModel
from starlette.responses import Response
from typing import List,Dict
from app.structured_outputs.context import DatasetContext
from app.agents.supervisor import Supervisor
from app.agents.coder import Coder
from app.agents.visualizer import Visualizer
from app.agents.orchestrator import AnalysisOrchestrator
from app.agents.reporter import Reporter
from app.agents.auditor import Evaluator
from typing import Optional,Any
from app.structured_outputs.supervisor_structured_output import AnalysisPlan

load_dotenv()

# Creates a main router
router = APIRouter()


# --- SCHEMAS --- 
# Creates an EventSchema for incoming events
class EventSchema(BaseModel):
    """Event Schema"""

    event_id: str
    event_type: str
    event_data: dict

class AnalysisRequest(BaseModel):
# This stores the "DNA" of the dataset (columns, types, etc.)
    dataset_context: DatasetContext
    user_questions: List[str]
    # Optional: overall goal to give the Supervisor more "flavor"
    overall_goal: Optional[str] = "Provide data-driven insights"

class AnalysisSession(BaseModel):
    session_id: str
    status: str
    plan: Optional[Any] = None # Will store your AnalysisPlan object

# --- IN-MEMORY DATABASE ---
# In a real app, this would be Redis or PostgreSQL
sessions: Dict[str, AnalysisSession] = {}
# A dictionary to hold live orchestrator objects
active_orchestrators: Dict[str, AnalysisOrchestrator] = {}

#--- Functions ----
def get_orchestrator(dataset_context: DatasetContext):
    # 1. Initialize the individual pieces
    supervisor = Supervisor(api_key=os.getenv("OPENAI_API_KEY"),model='gpt-4o-mini',temperature=0.3)
    coder = Coder(api_key=os.getenv("OPENAI_API_KEY"),model='gpt-4o-mini',temperature=0.6)
    visualizer = Visualizer(api_key=os.getenv("OPENAI_API_KEY"),model='gpt-4o-mini',temperature=0.6)
    reporter = Reporter(api_key=os.getenv("OPENAI_API_KEY"),model='gpt-4o-mini',temperature=0.6)
    evaluator = Evaluator(api_key=os.getenv("OPENAI_API_KEY"),model='gpt-4o-mini',temperature=0.3)

    orchestrator = AnalysisOrchestrator(supervisor,reporter=reporter,evaluator=evaluator,coder=coder,visualizer=visualizer,api_key=os.getenv("OPENAI_API_KEY"),model='gpt-4o-mini',max_retries=3,dataset_context=dataset_context)
    
    # 2. Return a fresh instance
    return orchestrator

def get_current_orchestrator(session_id: str):
    orch = active_orchestrators.get(session_id)
    if not orch:
        raise HTTPException(status_code=404, detail="Analysis session not found.")
    return orch

# --- ROUTES ---
# Routes data using "/"
@router.post("/",dependencies=[])
def handle_event(data:EventSchema) -> Response:
    print(data)

    # Return acceptance response
    return Response(
        content=json.dumps({'message':'data recieved'}),
        status_code=HTTPStatus.ACCEPTED    
    )
# 1. Begin the analysis
@router.post("/start-analysis")
def start_analysis(request: AnalysisRequest):

    try:
        session_id = str(uuid.uuid4())
        
        # Create the fresh instance
        orch = get_orchestrator(request.dataset_context)
        
        # Phase 1: Planning
        plan = orch.generate_initial_plan(request.user_questions)
        
        # Save the WHOLE object so we don't lose the namespace/results
        active_orchestrators[session_id] = orch

        # Convert the Pydantic object to a dict and add the session_id
        response_data = plan.model_dump() 
        response_data["session_id"] = session_id
        
        return response_data
    
    except Exception as e:
        import traceback
        print("--- CRITICAL ERROR ---")
        traceback.print_exc() # This prints the WHOLE error stack
        raise HTTPException(status_code=500, detail=str(e))

# 2. Get Human Plan Approval and Execute the Plan
@router.post("/approve-plan/{session_id}")
async def approve_plan(
    session_id: str, 
    approved_plan: AnalysisPlan, # The Pydantic model of your plan
    background_tasks: BackgroundTasks, # This prevents the "Timeout"
    orch: AnalysisOrchestrator = Depends(get_current_orchestrator)
):
    # 1. Update the orchestrator with the human-approved version
    # (In case the human changed task descriptions or order)
    orch.plan = approved_plan
    
    # 2. Start the heavy lifting in the background
    # This returns an immediate "OK" to the user while the agents work
    background_tasks.add_task(orch.run_execution_loop, approved_plan)
    
    
    return {
        "status": "success",
        "message": "Plan approved. Agents are now executing tasks in the background.",
        "session_id": session_id
    }

@router.post("/audit-results/{session_id}")
def audit_results(orch: AnalysisOrchestrator = Depends(get_current_orchestrator)):
    # 1. Run evaluation (HITL is False here because the 'Human' is the web user)
    is_passed,final_plan = orch.plan_evaluation(HITL=False)
    

    return {
        "is_passed": is_passed, 
        "plan": final_plan  # Always return the plan so the UI can render it
    }

@router.post("/finalize/{session_id}")
async def finalize(
    is_passed:bool=Body(...),# looks inside the json data sent for the is_passed
    plan: AnalysisPlan =Body(...), 
    background_tasks: BackgroundTasks =None,
    orch: AnalysisOrchestrator = Depends(get_current_orchestrator)
):
    # Only add ONE task that handles the full sequence (Fix -> Report)
    background_tasks.add_task(orch.apply_evaluator_plan_corrections, is_passed,plan)
    
    return {"message": "Applying corrections and generating final report..."}