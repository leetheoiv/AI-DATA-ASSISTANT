# Import Libraries
from app.agent import AIAgent
from app.prompt_templates.visualizer_prompt_template import visualizer_prompt_template
from app.tools.execute_code import execute_code 
from app.structured_outputs.coder_structured_output import CoderResponse # Reusing the structured schema
from app.structured_outputs.visualizer_structured_output import VisualizerOutput
class Visualizer(AIAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run_task(self, current_task: str, dataset_context, dependencies: dict = None,namespace:dict=None) -> tuple:
        """
        Execute a visualization task, generating and saving high-quality charts.
        
        Args:
            current_task: The specific visualization instruction
            dataset_context: Static metadata about the dataset
            dependencies: Dynamic dictionary of outputs from previous tasks (e.g. {0: df_summary})
            
        Returns:
            (parsed_response, output) on success
        """
        self.reset()

        # Render the specialized visualizer prompt with design best practices
        self.system_prompt = visualizer_prompt_template.render(
            current_task=current_task,
            dataset_context=dataset_context,
            dependencies=dependencies
        )

        current_prompt = current_task
  

        for attempt in range(1, self.max_retries + 1):
            print(f"\n--- [Visualizer] Attempt {attempt}/{self.max_retries} ---")

            # 1. Generate Visualization Code
            _, parsed_response, _ = self.ask(
                user_prompt=current_prompt,
                response_model=VisualizerOutput
            )

            if not parsed_response or not parsed_response.executable_code:
                current_prompt = "No code provided. You must provide Python code to create and save the chart."
                continue

            # 2. Execute Code (Saves PNG to disk)
            result = execute_code(parsed_response.executable_code,namespace=namespace)

            if result["status"] == "error":
                error_msg = result.get("message", "Unknown error")
                last_line = error_msg.splitlines()[-1] if error_msg else "No error message provided"
                print(f"❌ Visualization failed: {last_line}")

                current_prompt = (
                    f"Your visualization code failed: {last_line}.\n\n"
                    "CRITICAL FIXES REQUIRED:\n"
                    "1. DO NOT use backslashes (\) for line continuations. Use parentheses () instead.\n"
                    "2. Check for stray characters at the end of lines or inside f-strings.\n"
                    "3. Simplify the code: Remove complex custom titles if they are causing issues.\n"
                    "Please provide the full corrected Python code block."
                )
                continue

            if result["status"] == "success":
                print(f"✅ Visualization saved successfully.")
                
                # NEW LOGIC: Pass the dependency data (Coder's math) 
                # to the interpreter so it doesn't hallucinate a trend.
                coder_math = dependencies.get(0, "No previous math provided")
                
                # We pass the Coder's actual output to the interpretation prompt
                parsed_response.results_interpretation = self._interpret_visual(
                    task=current_task, 
                    output=result["output"], 
                    coder_results=coder_math # <--- Pass this in!
                )
            
            print(f"[Visualizer]\nInsight: {parsed_response.results_interpretation}\n")
            
            # Return the interpretation as the 'output' for the Reporter to synthesize
            return parsed_response, parsed_response.results_interpretation

        print(f"💀 Visualizer failed after {self.max_retries} attempts.")
        return None, "Visualization execution failed."

    def _interpret_visual(self, task: str, output: str,coder_results: str) -> str:
        """
        Interprets the visual trends.
        """
        saved_input_list = self.input_list.copy()
        saved_history = self.history
        self.input_list = []
        self.history = None

        _, _, interpretation = self.ask(
            user_prompt=(
                f"Task: {task}\n\n"
                f"The Coder previously found these statistics: {coder_results}\n\n"
                f"Your code execution logs: {output}\n\n"
                "Based on the visual you created AND the statistics above, "
                "provide a one-sentence business insight. "
                "CRITICAL: If the statistics show no correlation, the visual interpretation "
                "must explicitly state that no clear relationship was found."
            )
        )

        self.input_list = saved_input_list
        self.history = saved_history
        return interpretation or "Visual generated successfully."