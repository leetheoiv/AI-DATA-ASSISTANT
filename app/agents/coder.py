# Import Libraries
from app.agent import AIAgent
import io
import contextlib
import traceback
from app.prompt_templates.coder_prompt_template import coder_prompt_template
from app.tools.execute_code import execute_code 

class Coder(AIAgent):
    def __init__(self, max_retries, **kwargs):
        super().__init__(**kwargs)
        self.max_retries = max_retries


    def run_task(self, current_task: str, context_data: dict, **kwargs):
        runtime_state = {} 

        output = None
        self.system_prompt = coder_prompt_template.render(
            current_task=current_task,
            dataset_context=context_data 
        )

        current_prompt = current_task

        for attempt in range(self.max_retries):
            # 1. Get response (might contain chat + code)
            raw, parsed_response, content = self.ask(
                user_prompt=current_prompt,
                **kwargs
            )
            
            executable_code = getattr(parsed_response, 'executable_code', None)
         
            
   
            
            stdout_capture = io.StringIO()
            try:
                
                # 2. Execution
                execution_results = execute_code(executable_code)
                
                print(f"✅ Attempt {attempt + 1} succeeded. Code Output:\n{execution_results['output']}")

                # Now we ask the agent to look at the REAL logs it just produced
                interpretation_prompt = (
                f"The code ran successfully. Here are the actual logs from the execution:\n\n"
                f"{execution_results['output']}\n\n"
                f"Based ONLY on these logs, provide a 1-sentence professional interpretation of the results."
                )

                # We call .ask() again, but this time we want a plain string or updated model
                _, _, final_interpretation = self.ask(
                    user_prompt=interpretation_prompt,
                    use_structured_response=False # Get a clean sentence back
                )

                # Update the parsed_response object with the REAL truth
                if hasattr(parsed_response, 'results_interpretation'):
                    parsed_response.results_interpretation = final_interpretation
                 

                # If the code ran but produced NO output, the LLM won't know what happened.
                if not output:
                    output = "Code executed successfully, but produced no output. Did you forget to print() your results?"

                # 4. Final Verification: Does the output actually answer the task?
                # We return the output so the Supervisor/Interpreter can see it.
                return raw, parsed_response, execution_results['output']

            except Exception as e:
                error_msg = traceback.format_exc()
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                
                # Feed the REAL error back to the LLM
                # Feed the error back for the next iteration of the loop
                current_prompt = (
                    f"Your code failed. \nERROR:\n{error_msg.splitlines()[-1]}\n"
                    f"STDOUT BEFORE CRASH:\n{stdout_capture.getvalue()}\n"
                    "Fix the error and provide the updated code."
            )
  

        return None, None, "Execution failed after maximum retries."
        
