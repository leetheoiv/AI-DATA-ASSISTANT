# Import Libraries
from app.agent import AIAgent
import io
import contextlib
import traceback
from app.prompt_templates.coder_prompt_template import coder_prompt_template
from app.tools.execute_code import execute_code 
from app.structured_outputs.coder_structured_output import CoderResponse    

class Coder(AIAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run_task(self, current_task: str, dataset_context,dependencies: dict = None) -> tuple:
        """
        Execute a single analysis task with automatic retry on failure.
        
        Args:
            task: The specific task description from the AnalysisPlan
            context_data: Dataset context object with schema, file path, known issues
            
        Returns:
            (parsed_response, output) on success
            (None, error_message) on failure after max retries
        """
        self.reset()

        # Set system prompt after reset so it isn't wiped
        self.system_prompt = coder_prompt_template.render(
            current_task=current_task,
            dataset_context=dataset_context
        )

        current_prompt = current_task

        for attempt in range(1, self.max_retries + 1):
            print(f"\n🔄 Attempt {attempt}/{self.max_retries}")

            # Generate code
            _, parsed_response, _ = self.ask(
                user_prompt=current_prompt,
                response_model=CoderResponse
            )

            if not parsed_response or not parsed_response.executable_code:
                print("⚠️  No executable code returned — retrying.")
                current_prompt = "You did not return executable code. Try again and ensure the 'executable_code' field is populated."
                continue

            # Execute code
            result = execute_code(parsed_response.executable_code)

            if result["status"] == "error":
                error_msg = result.get("message", "Unknown error")
                stdout_before_crash = result.get("output", "")
                print(f"❌ Attempt {attempt} failed:\n{error_msg.splitlines()[-1]}")

                # REFINED FEEDBACK FOR THE AGENT
                # This becomes the 'user_prompt' for the NEXT iteration of the loop
                current_prompt = (
                    f"Your code failed on attempt {attempt}.\n\n"
                    f"ERROR:\n{error_msg}\n\n"
                    f"STDOUT BEFORE CRASH:\n{stdout_before_crash or 'None'}\n\n"
                    "CRITICAL: Identify the root cause (check for unterminated strings or missing files), "
                    "fix the logic, and return the corrected code block."
                )
                continue

            # Success — get interpretation via a fresh isolated call
            print(f"✅ Attempt {attempt} succeeded.")
            output = result["output"]
            parsed_response.results_interpretation = self._interpret(current_task, output)
            print(f"""[Coder]\nHere are my results:\n{output}\n{parsed_response.results_interpretation} """)
            return parsed_response, output

        print(f"💀 Task failed after {self.max_retries} attempts.")
        return None, f"Execution failed after {self.max_retries} attempts."

    def _interpret(self, task: str, output: str) -> str:
        """
        Isolated one-shot call to interpret execution output.
        Does not affect the coder's conversation history.
        """
        # Temporarily snapshot and clear state so this call is isolated
        saved_input_list = self.input_list.copy()
        saved_history = self.history

        self.input_list = []
        self.history = None

        _, _, interpretation = self.ask(
            user_prompt=(
                f"Task: {task}\n\n"
                f"Execution output:\n{output}\n\n"
                "In one concise sentence, interpret what these results mean in business terms."
            )
        )

        # Restore coder state so retry loop isn't disrupted
        self.input_list = saved_input_list
        self.history = saved_history

        return interpretation or "No interpretation available."
