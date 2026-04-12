from app.agents.coder import Coder
from app.agents.visualizer import Visualizer
import logging
from app.agents.supervisor import Supervisor
from app.agents.auditor import Evaluator
from app.agents.reporter import Reporter
from app.structured_outputs.context import DatasetContext
import pandas as pd
from app.support_functions.human_in_the_loop import HITL

# Set up logging to track the "Engine" performance
logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    def __init__(self, supervisor:Supervisor,evaluator:Evaluator,reporter:Reporter,coder:Coder,visualizer:Visualizer, api_key,dataset_context:DatasetContext,max_retries:int,model='gpt-4o-mini'):
        """
        The Engine that manages the flow of data between the Brain (Supervisor) 
        and the Hands (Agents).
        """
        self.supervisor = supervisor
        self.reporter = reporter
        self.coder = coder
        self.visualizer = visualizer
        self.evaluator = evaluator
        self.dataset_context = dataset_context  # Static facts about the data
        self.agents = {"coder": self.coder,
                       "visualizer": self.visualizer}      # e.g., {"coder": Coder(...), "reporter": Reporter(...)}
        self.task_results = {}                  # Stores output of each task index
        self.shared_namespace = {
        "pd": pd,
        "df": pd.read_csv(self.dataset_context.file_path)} # This persists across all tasks and can be used for any purpose (e.g., storing a DataFrame summary that multiple agents can reference)
        self.user_questions = []    # Store the original questions for reference in follow-up prompts if needed
        self.analysis_goal = None  # Store the user's overall analysis goal for use in follow-up prompts if clarification is needed
        self.plan = None           # Store the finalized plan for potential use in follow-up prompts if needed
        self.enriched_task_results = []  # Store the enriched task results for the Reporter to use in its final synthesis
        self.prereq_data = {}  # This dictionary will hold the specific outputs from prerequisite tasks, keyed by their index (e.g., {0: "Coder found a correlation of 0.04 between X and Y", ...})
        self.human_in_the_loop = HITL()  # Initialize the Human-in-the-loop

    def generate_initial_plan(self,user_questions: list[str]):
        # [PHASE 1] : Logical Planning
        # The supervisor blocks here for user clarification if needed.
        self.user_questions.extend(user_questions)  # Store for potential use in follow-up prompts

        # 1. Get the Supervisor's Plan
        print("[Orchestrator] Sending user questions to Supervisor for planning...")
        raw, plan, final_content = self.supervisor.run_task(user_questions,context_data=self.dataset_context)

        return plan
    
    def run_execution_loop(self,finalized_plan):
        # [PHASE 2] : Execution Loop
        self.plan = finalized_plan
    
        for i, task in enumerate(self.plan.tasks):
            print(f"\n--- [Task {i}] Agent: {task.agent} ---")
            
            # 1. Fetch the physical agent object
            agent = self.agents.get(task.agent)
            if not agent:
                logger.error(f"Agent '{task.agent}' missing from registry. Aborting.")
                break
            

            # 2. Gather outputs from prerequisite tasks (Dynamic Context)
            # This ensures 'visualizer' gets the actual data from 'coder'
 
            
            for idx in task.depends_on:
                if idx in self.task_results.keys():
                    # 1. Get the tuple: (raw_str, pydantic_obj, content_str)
                    task_output = self.task_results[idx]
                    
                    pydantic_obj = task_output
                    
    
                    # 2. Access the Pydantic object at index 0 and get the 'results_interpretation' field
                    raw_text = pydantic_obj['execution_output'][0].results_interpretation
                    clean_text = raw_text.replace("\n", " ").replace("\\", "").replace("'", "").strip()
                    self.prereq_data[idx] = clean_text
                else:
                    logger.warning(f"Prerequisite task {idx} has no recorded output. Agent '{task.agent}' may hallucinate or fail.")
                    self.prereq_data[idx] = "No data from prerequisite task"
            
            print(f"[Orchestrator] Prerequisite data for Task {i}: {self.prereq_data}")

            # 3. Invoke the Agent
            # We pass: 1. The specific task, 2. The Static Rules, 3. The Dynamic Data
            try:
                result = agent.run_task(
                    current_task=task.task_description,
                    dataset_context=self.dataset_context,       # The 'core/context.py' object
                    dependencies=self.prereq_data,              # The outputs of previous tasks
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
    
    def plan_evaluation(self,HITL:bool=False):
        # [PHASE 3] : Evaluation
        print("\n[Orchestrator] All tasks executed. Sending results to Evaluator for auditing...")
        # Send the entire plan and all task results to the Evaluator for a comprehensive audit
        evaluation_result = self.evaluator.audit(
            context_data=self.dataset_context,
            user_questions=self.user_questions,
            task_results=self.task_results
        )

        if HITL == True:
            evaluation_result = self.human_in_the_loop.human_evaluation_review(evaluation_result)
        
        print(f"\n[Orchestrator] Evaluation completed. Passed: {evaluation_result.is_passed}")
        if evaluation_result.is_passed == False:

            print(f"Logical Conflicts: {evaluation_result.logical_conflicts}")
            print(f"Technical Errors: {evaluation_result.technical_errors}")
            print(f"Missing Answers: {evaluation_result.missing_answers}")
            print(f"Recommendation for Supervisor: {evaluation_result.recommendation_for_supervisor}")
            # Generate a correction plan based on the evaluation feedback
            revised_plan = self.supervisor.generate_correction_plan(
                previous_results=self.task_results,
                evaluation_result=evaluation_result
            )  

            return revised_plan
        else:
            return self.plan
        
    
    def apply_evaluator_plan_corrections(self,revised_plan):
        #[PHASE 3]: Plan Corrections

        if revised_plan:
            # Execute only the tasks that the Supervisor flagged as needing correction
            self.execute_corrections(revised_plan)

            print('[DEBUG]: CHECKING FOR UPDATED TASKS AFTER CORRECTIONS', self.task_results)

         # [PHASE 4] : Reporting 
        # Get Reporter's output (the final PDF path and the structured report data)
        self.reporter.run_task(
            overall_goal=self.analysis_goal,
            task_results=self.task_results,
            context_data=self.dataset_context
        )

        # Return the final task's output (usually the Reporter's summary)
        final_idx = len(self.plan.tasks) - 1
        return self.task_results.get(final_idx, "Analysis failed or was incomplete.")


            


        # Return the final task's output (usually the Reporter's summary)
        final_idx = len(self.plan.tasks) - 1
        return self.task_results.get(final_idx, "Analysis failed or was incomplete.")

    def execute_plan(self, user_questions: list[str]):
        """
        Implements entire agent orchestration in one go
        """
        # [PHASE 1] : Logical Planning
        # The supervisor blocks here for user clarification if needed.
        self.user_questions.extend(user_questions)  # Store for potential use in follow-up prompts

        # 1. Get the Supervisor's Plan
        print("[Orchestrator] Sending user questions to Supervisor for planning...")
        raw, plan, final_content = self.supervisor.run_task(user_questions,context_data=self.dataset_context)

        # 2. Humnan-in-the-loop checkpoint for plan review and logging
        # --- [HUMAN IN THE LOOP START] ---
        plan = self.human_in_the_loop.human_review_step(plan)
        if not plan:
            print("🚫 Plan rejected by human. Aborting.")
            return
        # --- [HUMAN IN THE LOOP END] ---
      
        # 3. Store analysis goal
        self.analysis_goal = self.supervisor.analysis_goal
        # 4. Store the finalized plan for potential use in follow-up prompts if needed
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
 
            
            for idx in task.depends_on:
                if idx in self.task_results.keys():
                    # 1. Get the tuple: (raw_str, pydantic_obj, content_str)
                    task_output = self.task_results[idx]
                    
                    pydantic_obj = task_output
                    
    
                    # 2. Access the Pydantic object at index 0 and get the 'results_interpretation' field
                    raw_text = pydantic_obj['execution_output'][0].results_interpretation
                    clean_text = raw_text.replace("\n", " ").replace("\\", "").replace("'", "").strip()
                    self.prereq_data[idx] = clean_text
                else:
                    logger.warning(f"Prerequisite task {idx} has no recorded output. Agent '{task.agent}' may hallucinate or fail.")
                    self.prereq_data[idx] = "No data from prerequisite task"
            
            print(f"[Orchestrator] Prerequisite data for Task {i}: {self.prereq_data}")

            # 3. Invoke the Agent
            # We pass: 1. The specific task, 2. The Static Rules, 3. The Dynamic Data
            try:
                result = agent.run_task(
                    current_task=task.task_description,
                    dataset_context=self.dataset_context,       # The 'core/context.py' object
                    dependencies=self.prereq_data,              # The outputs of previous tasks
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
        

        # [PHASE 3] : Evaluation
        print("\n[Orchestrator] All tasks executed. Sending results to Evaluator for auditing...")
        # Send the entire plan and all task results to the Evaluator for a comprehensive audit
        evaluation_result = self.evaluator.audit(
            context_data=self.dataset_context,
            user_questions=self.user_questions,
            task_results=self.task_results
        )

        evaluation_result = self.human_in_the_loop.human_evaluation_review(evaluation_result)
        
        print(f"\n[Orchestrator] Evaluation completed. Passed: {evaluation_result.is_passed}")
        if evaluation_result.is_passed == False:

            print(f"Logical Conflicts: {evaluation_result.logical_conflicts}")
            print(f"Technical Errors: {evaluation_result.technical_errors}")
            print(f"Missing Answers: {evaluation_result.missing_answers}")
            print(f"Recommendation for Supervisor: {evaluation_result.recommendation_for_supervisor}")
            # Generate a correction plan based on the evaluation feedback
            revised_plan = self.supervisor.generate_correction_plan(
                previous_results=self.task_results,
                evaluation_result=evaluation_result
            )  

    
            # Execute only the tasks that the Supervisor flagged as needing correction
            self.execute_corrections(revised_plan)

            print('[DEBUG]: CHECKING FOR UPDATED TASKS AFTER CORRECTIONS', self.task_results)

            # [PHASE 3] : Reporting 
            # After corrections, we could loop back to the Reporter for a revised synthesis if needed, but for now we return the final report.
            self.reporter.run_task(
                overall_goal=self.analysis_goal,
                task_results=self.task_results,
                context_data=self.dataset_context
            )
        else:
            print("\n[Orchestrator] All tasks executed. Sending results to Reporter for synthesis...")
            
            # [PHASE 3] : Reporting 
            # Get Reporter's output (the final PDF path and the structured report data)
            self.reporter.run_task(
                overall_goal=self.analysis_goal,
                task_results=self.task_results,
                context_data=self.dataset_context
            )

        # Return the final task's output (usually the Reporter's summary)
        final_idx = len(plan.tasks) - 1
        return self.task_results.get(final_idx, "Analysis failed or was incomplete.")
    
    def execute_corrections(self, revised_plan):
        """
        Only executes tasks that the Supervisor flagged as corrections.
        """
        for task in revised_plan.tasks:
            target_idx = task.original_index  # This is the index of the task in the original plan that this correction corresponds to
  
            if task.is_correction:
                print(f"🔧 Correcting Task {target_idx} ({task.agent})...")
                
                # Re-run the specific agent with the updated instructions
                result = self.agents[task.agent].run_task(
                    current_task=task.task_description,
                    dataset_context=self.dataset_context,
                    dependencies=self._get_prereqs(task.depends_on),
                    namespace=self.shared_namespace
                )
                
                # Overwrite the old failed result with the corrected one
                self.task_results[target_idx] = {
                    "user_question": task.user_question,
                    "agent": task.agent,
                    "instruction": task.task_description,
                    "execution_output": result
                }
            else:
                print(f"✅ Skipping Task {target_idx} (Already passed/valid).")
                
        # After the scalpel pass, send the whole thing back to the Reporter
        print("\n[Orchestrator] Corrections executed. Sending updated results to Reporter for revised synthesis...")

    def _get_prereqs(self, indices):
        """
        Returns a dictionary mapping task indices to their string interpretations.
        This is what the Jinja template expects for the 'dependencies' variable.
        """
        context = {}
        for i in indices:
            if i in self.task_results:
                out = self.task_results[i]["execution_output"]
                # Extract the interpretation string safely
                text = out if isinstance(out, tuple) else getattr(out, 'results_interpretation', str(out))
                context[i] = text
        return context  