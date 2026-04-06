# Import Libraries
from app.agent import AIAgent
from app.prompt_templates.supervisor_prompt_template import supervisor_prompt_template
from app.structured_outputs.supervisor_structured_output import AnalysisPlan

class Supervisor(AIAgent):
    """Supervisor agent that takes in user questions and produces a structured analysis plan, asking for clarifications as needed."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.user_formatted_questions = None  # Store the formatted questions for use in follow-up prompts if clarification is needed
        self.analysis_goal = None  # Store the user's overall analysis goal for use in follow-up prompts
        self.finalized_plan = None  # Store the finalized plan for potential use in follow-up prompts if needed 
        
    def run_task(self, user_questions: list[str],context_data: dict,analysis_goal: str=None,) -> tuple[AnalysisPlan, str]:
        """
        Accept a list of questions, return a finalized AnalysisPlan.
        Blocks internally until ambiguity is resolved via console/Streamlit callback.
        Returns: raw response, parsed AnalysisPlan, and the final response that led to the plan (useful for logging and debugging).
        """
        self.reset()  # ← replaces self.input_list = []; self.history = None
        
        # Step 1: Force the Goal Inquiry
        print("\n[Supervisor] Phase 1: Strategic Alignment")
        if analysis_goal:
            self.analysis_goal = analysis_goal
        else:
            self.analysis_goal = input("What is the overall goal of this analysis? (e.g., 'Reduce Churn'): ").strip()
        

        # Step 2: Format the questions and add to input list
        self.user_formatted_questions = self._format_questions(user_questions)
        self.input_list.append({"role": "user", "content": self.user_formatted_questions})

        # Step 3: Create Systen Prompt with context
        self.system_prompt = supervisor_prompt_template.render(
            dataset_context=context_data,
            analysis_goal=analysis_goal
        )


        while True:
            raw, plan, content = self.ask(
                response_model=AnalysisPlan
            )

            if plan.status == "plan":
                print("""[Supervisor]\nHere is my plan:""")
                for i,task in enumerate(plan.tasks):
                    print(f"  - {task.agent} task: {task.task_description} (depends on {task.depends_on} - Addresses question: '{task.user_question}')")
                self.finalized_plan = plan  # Store the finalized plan for potential use in follow-up prompts if needed
                self.finalized_plan.overall_goal = self.analysis_goal  # Add the overall goal to the finalized plan for potential use in follow-up prompts if needed

                return raw, plan, content

            elif plan.status == "clarification":
                print("\n[Supervisor]\nsupervisor needs clarification]")
                print(plan)
                for i, q in enumerate(plan.clarification_questions, 1):
                    print(f"  {i}. {q}")

                user_response = input("\nYour answer: ").strip() # will need to be replaced with Streamlit callback in production

                self.input_list.append({"role": "assistant", "content": content})
                self.input_list.append({"role": "user", "content": user_response})

    def _format_questions(self, questions: list[str]) -> str:
        """
        Format the user's questions into a prompt for the supervisor. If there's only one question, return it directly. 
        If there are multiple, number them and provide instructions for how to build an efficient analysis plan.
        """
        if len(questions) == 1:
            return questions[0]

        numbered = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
        return (
            f"Here are {len(questions)} analysis questions. "
            f"Build an efficient plan — consolidate steps where questions share common data or themes, "
            f"but keep distinct analyses separate. Track which questions each task addresses.\n\n"
            f"{numbered}"
        )
    
