from app.agents.coder import Coder
from app.agents.visualizer import Visualizer
import logging
from app.agents.supervisor import Supervisor
from app.agents.auditor import Evaluator
from app.agents.reporter import Reporter
from app.structured_outputs.context import DatasetContext
import pandas as pd

# Set up logging to track the "Engine" performance
logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    def __init__(self, supervisor:Supervisor,evaluator:Evaluator,reporter:Reporter, api_key,dataset_context:DatasetContext,max_retries:int,model='gpt-4o-mini'):
        """
        The Engine that manages the flow of data between the Brain (Supervisor) 
        and the Hands (Agents).
        """
        self.supervisor = supervisor
        self.reporter = reporter
        self.evaluator = evaluator
        self.dataset_context = dataset_context  # Static facts about the data
        self.agents = {"coder": Coder(api_key=api_key,model=model,max_retries=max_retries),
                       "visualizer":Visualizer(api_key=api_key,model=model,max_retries=max_retries)}      # e.g., {"coder": Coder(...), "reporter": Reporter(...)}
        self.task_results = {}                  # Stores output of each task index
        self.shared_namespace = {
        "pd": pd,
        "df": pd.read_csv(self.dataset_context.file_path)} # This persists across all tasks and can be used for any purpose (e.g., storing a DataFrame summary that multiple agents can reference)
        self.user_questions = []    # Store the original questions for reference in follow-up prompts if needed
        self.analysis_goal = None  # Store the user's overall analysis goal for use in follow-up prompts if clarification is needed
        self.plan = None           # Store the finalized plan for potential use in follow-up prompts if needed
        self.enriched_task_results = []  # Store the enriched task results for the Reporter to use in its final synthesis
        

    def execute_plan(self, user_questions: list[str]):
        # [PHASE 1] : Logical Planning
        # The supervisor blocks here for user clarification if needed.
        self.user_questions.extend(user_questions)  # Store for potential use in follow-up prompts

        # 1. Get the Supervisor's Plan
        print("[Orchestrator] Sending user questions to Supervisor for planning...")
        raw, plan, final_content = self.supervisor.run_task(user_questions,context_data=self.dataset_context)
        # Store analysis goal
        self.analysis_goal = self.supervisor.analysis_goal
        # Store the finalized plan for potential use in follow-up prompts if needed
        self.plan = self.supervisor.finalized_plan
        
        print(f"\n[Orchestrator] Plan finalized. Executing {len(plan.tasks)} tasks.")

        # [PHASE 2] : Execution Loop
        for i, task in enumerate(plan.tasks):
            print(f"\n--- [Task {i}] Agent: {task.agent} ---")
            
            # 1. Fetch the physical agent object
            agent = self.agents.get(task.agent)
            if not agent:
                logger.error(f"Agent '{task.agent}' missing from registry. Aborting.")
                break
            

            # 2. Gather outputs from prerequisite tasks (Dynamic Context)
            # This ensures 'visualizer' gets the actual data from 'coder'
 
            prereq_data = {}
            for idx in task.depends_on:
                if idx in self.task_results.keys():
                    # 1. Get the tuple: (raw_str, pydantic_obj, content_str)
                    task_output = self.task_results[idx]
                    
                    pydantic_obj = task_output
                    
    
                    # 2. Access the Pydantic object at index 0 and get the 'results_interpretation' field
                    raw_text = pydantic_obj['execution_output'][0].results_interpretation
                    clean_text = raw_text.replace("\n", " ").replace("\\", "").replace("'", "").strip()
                    prereq_data[idx] = clean_text
                else:
                    logger.warning(f"Prerequisite task {idx} has no recorded output. Agent '{task.agent}' may hallucinate or fail.")
                    prereq_data[idx] = "No data from prerequisite task"
            

            # 3. Invoke the Agent
            # We pass: 1. The specific task, 2. The Static Rules, 3. The Dynamic Data
            try:
                result = agent.run_task(
                    current_task=task.task_description,
                    dataset_context=self.dataset_context, # The 'core/context.py' object
                    dependencies=prereq_data,              # The outputs of previous tasks
                    namespace=self.shared_namespace
                )
                
                # Update the namespace with whatever the agent just created
                if result and "namespace" in result:
                    self.shared_namespace.update(result["namespace"])
                # 2. STORE THE UNIFIED RESULT (The Fix)
                # We pair the execution 'result' with the 'task' metadata
                self.task_results[i] = {
                    "user_question": task.user_question, # Captured from Supervisor
                    "agent": task.agent,
                    "instruction": task.task_description,
                    "execution_output": result # The (Pydantic, Interpretation) tuple
                }
                
                
            except Exception as e:
                logger.error(f"Task {i} ({task.agent}) failed: {e}")
                print(f'[Phase 2 Error]: Task {i} ({task.agent}) failed: {e}')
                # We stop the loop because downstream tasks depend on this success
                break
        # [PHASE 3] : Final Synthesis by Reporter
        # We enrich the raw task results with the Supervisor's original intent to give the Reporter full
        self.enriched_task_results = self._enrich_task_results()

        # Return the final task's output (usually the Reporter's summary)
        final_idx = len(plan.tasks) - 1
        return self.task_results.get(final_idx, "Analysis failed or was incomplete.")
    
    def _enrich_task_results(self) -> list[dict]:
        """
        Pairs raw execution data with the Supervisor's original intent.
        This ensures the Reporter knows 'Why' a piece of data exists.
        """
        enriched_context = []
        
        for i, task in enumerate(self.plan.tasks):
            # 1. Safely fetch the result from the execution dictionary
            raw_result = self.task_results.get(i)
            
            # 2. Extract the interpretation string (Handling potential agent failures)
            if isinstance(raw_result, tuple) and len(raw_result) > 1:
                # result is the Pydantic object, result is the string interpretation
                interpretation = raw_result
            elif isinstance(raw_result, str):
                interpretation = raw_result
            else:
                interpretation = "No result produced due to execution error."

            # 3. Build the enriched object
            enriched_context.append({
                "task_index": i,
                "agent": task.agent,
                "original_question": getattr(task, 'revised_question', "General Analysis"),
                "instruction": task.task_description,
                "result": interpretation,
                "was_successful": "No result produced" not in interpretation
            })
            
        return enriched_context