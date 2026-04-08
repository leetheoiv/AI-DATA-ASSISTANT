



from app.structured_outputs.supervisor_structured_output import AnalysisPlan, AnalysisTask


class HITL:
    """
    Human-in-the-loop checkpoint for plan review and logging.
    This class can be expanded in the future to include more sophisticated logging, user interfaces for review, etc.
    For now, it serves as a placeholder to indicate where human review would occur in the process.
    """
    def __init__(self):
        pass

    def give_feedback(self, sup_plan):
        feedback = input("Give feedback or type 'OK' to proceed: ")
        if feedback.lower() != 'ok':
            # Send the plan AND the human feedback back to the Supervisor for a 'Version 2'
            sup_plan = self.supervisor.replan_with_feedback(sup_plan, feedback)

    def human_review_step(self, sup_plan: AnalysisPlan):
        # In a real implementation, this method would present the plan to a human user for review and feedback.
        # For this simplified version, we'll just print the plan and assume it's approved.
        print("\n--- 🛡️ HUMAN REVIEW REQUIRED: PROPOSED ANALYSIS PLAN ---")
        while True:
            for task in sup_plan.tasks:
                print(f"--- Step {task.original_index} ---")
                print(f"Agent: {task.agent.upper()}")
                print(f"Task: {task.task_description}")
                
                # This pulls the specific logic for THIS step
                print(f"Step Logic: {task.step_reasoning}") 
                print("-" * 20)

            choice = input("\nActions: [A]pprove, [C]reate, [M]odify, [D]elete, [R]eject: ").lower()

            
            if choice == 'a':
                print("🚀 Plan approved. Starting execution...")
                return sup_plan  # Break loop and return the final plan

            elif choice == 'r':
                print("🛑 Plan rejected.")
                return None      # Break loop and return None to stop the Orchestrator
            
            elif choice == 'd':
                idx_to_del = int(input("Enter Task Index to DELETE: "))
                
                # Check if other tasks depend on this one
                dependents = [i for i, t in enumerate(sup_plan.tasks) if idx_to_del in t.depends_on]
                if dependents:
                    confirm = input(f"⚠️ Warning: Tasks {dependents} depend on this! Delete anyway? (y/n): ")
                    if confirm.lower() != 'y':
                        return self.human_review_step(sup_plan)

                # Remove the task
                deleted_task = sup_plan.tasks.pop(idx_to_del)
                print(f"🗑️ Deleted Task {idx_to_del}: {deleted_task.agent}")

                # Re-map dependencies (Optional but recommended)
                # If you delete Task 0, Task 1's "depends_on:" needs to be handled
                for task in sup_plan.tasks:
                    if idx_to_del in task.depends_on:
                        task.depends_on.remove(idx_to_del)

                return self.human_review_step(sup_plan) # Show updated plan

            elif choice == 'm':
                task_idx = int(input("Enter Task Index to modify: "))
                print(f"Modifying Task {task_idx}. Leave blank to keep current value.")
                
                # 1. Update Agent
                new_agent = input(f"Current Agent ({sup_plan.tasks[task_idx].agent}). New Agent: ").strip()
                if new_agent:
                    sup_plan.tasks[task_idx].agent = new_agent.lower()
                    
                # 2. Update Description
                new_desc = input("New instructions: ").strip()
                if new_desc:
                    sup_plan.tasks[task_idx].task_description = new_desc
                    
                return self.human_review_step(sup_plan)
            
            elif choice == 'c':
                print("\n--- ➕ ADDING NEW TASK ---")
                # Calculate the next index automatically
                next_idx = len(sup_plan.tasks)
                
                new_task = AnalysisTask(
                    agent=input("Agent (coder/visualizer/reporter): ").lower().strip(),
                    user_question=input("User Question: "),
                    task_description=input("Task Description: "),
                    # Add the missing required fields here:
                    step_reasoning=input("Why are you adding this step? (Reasoning): "),
                    original_index=next_idx,
                    depends_on=[int(x) for x in input("Depends on (indices): ").split(',') if x.strip()],
                    is_correction=False
                )
                sup_plan.tasks.append(new_task)
                return self.human_review_step(sup_plan)
            
    def human_evaluation_review(self, evaluation_result):
        """
        Allows the human to override the Evaluator's automated pass/fail decision.
        """
        print("\n" + "🔍" * 20)
        print("🛡️  HUMAN EVALUATOR CHECKPOINT")
        print("🔍" * 20)
        
        # Show what the AI found
        print(f"AI Verdict: {'✅ PASSED' if evaluation_result.is_passed else '❌ FAILED'}")
        print(f"Logical Conflicts: {evaluation_result.logical_conflicts}")
        print(f"Technical Errors: {evaluation_result.technical_errors}")
        print(f"Missing Answers: {evaluation_result.missing_answers}")
        print(f"AI Recommendation: {evaluation_result.recommendation_for_supervisor}")
        
        print("\n[P] Accept AI Answer | [F] Force 'Fail' (Trigger Correction) | [O] Override AI 'Fail' (Force Pass)")
        choice = input("Your decision: ").lower().strip()

        if choice == 'p' and evaluation_result.is_passed:
            return evaluation_result # Keep original Pass
        
        elif choice == 'f':
            print("🛠️  Human forced a FAIL. Triggering correction cycle...")
            evaluation_result.is_passed = False
            # Allow user to add a custom note for the Supervisor
            human_note = input("Add specific feedback for the Supervisor (optional): ")
            if human_note:
                evaluation_result.recommendation_for_supervisor += f" | HUMAN NOTE: {human_note}"
            return evaluation_result

        elif choice == 'o':
            print("🔓 Human forced a PASS. Proceeding to Reporting...")
            evaluation_result.is_passed = True
            return evaluation_result

        return evaluation_result