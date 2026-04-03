# Import Libraries
from app.agent import AIAgent
from app.prompt_templates.supervisor_prompt_template import supervisor_prompt_template
from app.structured_outputs.supervisor_structured_output import AnalysisPlan

class Supervisor(AIAgent):
    """Supervisor agent that takes in user questions and produces a structured analysis plan, asking for clarifications as needed."""
    def __init__(self, context_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.context_data = context_data
        self.system_prompt = supervisor_prompt_template.render(
            dataset_context=context_data
        )
        self.user_formatted_questions = None  # Store the formatted questions for use in follow-up prompts if clarification is needed

    def run_task(self, user_questions: list[str]) -> tuple[AnalysisPlan, str]:
        """
        Accept a list of questions, return a finalized AnalysisPlan.
        Blocks internally until ambiguity is resolved via console/Streamlit callback.
        Returns: raw response, parsed AnalysisPlan, and the final response that led to the plan (useful for logging and debugging).
        """
        self.reset()  # ← replaces self.input_list = []; self.history = None

        self.user_formatted_questions = self._format_questions(user_questions)
        self.input_list.append({"role": "user", "content": self.user_formatted_questions})

        while True:
            raw, plan, content = self.ask(
                response_model=AnalysisPlan
            )

            if plan.status == "plan":
                print("""[Supervisor]\nHere is my plan:""")
                for i,task in enumerate(plan.tasks):
                    print(f"  - {task.agent} task: {task.task_description} (depends on {task.depends_on})")
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
    
