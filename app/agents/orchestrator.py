from app.agents.coder import Coder
from app.agents.visualizer import Visualizer
import logging
from app.agents.supervisor import Supervisor
from app.structured_outputs.context import DatasetContext
import pandas as pd

# Set up logging to track the "Engine" performance
logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    def __init__(self, supervisor:Supervisor,api_key,dataset_context:DatasetContext,max_retries:int,model='gpt-4o-mini'):
        """
        The Engine that manages the flow of data between the Brain (Supervisor) 
        and the Hands (Agents).
        """
        self.supervisor = supervisor
        self.dataset_context = dataset_context  # Static facts about the data
        self.agents = {"coder": Coder(api_key=api_key,model=model,max_retries=max_retries),
                       "visualizer":Visualizer(api_key=api_key,model=model,max_retries=max_retries)}      # e.g., {"coder": Coder(...), "reporter": Reporter(...)}
        self.task_results = {}                  # Stores output of each task index
        self.shared_namespace = {
        "pd": pd,
        "df": pd.read_csv(self.dataset_context.file_path)} # This persists across all tasks and can be used for any purpose (e.g., storing a DataFrame summary that multiple agents can reference)
        self.user_questions = []    # Store the original questions for reference in follow-up prompts if needed
        

    def execute_plan(self, user_questions: list[str]):
        # PHASE 1: Logical Planning
        # The supervisor blocks here for user clarification if needed.
        self.user_questions.extend(user_questions)  # Store for potential use in follow-up prompts

        print("[Orchestrator] Sending user questions to Supervisor for planning...")
        raw, plan, final_content = self.supervisor.run_task(user_questions)
        
        print(f"\n[Orchestrator] Plan finalized. Executing {len(plan.tasks)} tasks.")

        # PHASE 2: Execution Loop
        for i, task in enumerate(plan.tasks):
            print(f"\n--- [Task {i}] Agent: {task.agent} ---")
            
            # 1. Fetch the physical agent object
            agent = self.agents.get(task.agent)
            if not agent:
                logger.error(f"Agent '{task.agent}' missing from registry. Aborting.")
                break

            # 2. Gather outputs from prerequisite tasks (Dynamic Context)
            # This ensures 'visualizer' gets the actual data from 'coder'
            prereq_data = {idx: self.task_results[idx] for idx in task.depends_on if idx in self.task_results}

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
                # Store result for the next agent in the chain
                self.task_results[i] = result
                
            except Exception as e:
                logger.error(f"Task {i} ({task.agent}) failed: {e}")
                print(f'[Phase 2 Error]: Task {i} ({task.agent}) failed: {e}')
                # We stop the loop because downstream tasks depend on this success
                break

        # Return the final task's output (usually the Reporter's summary)
        final_idx = len(plan.tasks) - 1
        return self.task_results.get(final_idx, "Analysis failed or was incomplete.")