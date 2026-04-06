from app.agent import AIAgent
from app.prompt_templates.reporter_prompt_template import reporter_prompt_template
from app.structured_outputs.reporter_structured_output import *
from app.structured_outputs.supervisor_structured_output import AnalysisPlan
from app.tools.pdf_builder import create_executive_pdf

class Reporter(AIAgent):
    """
    The 'Editor-in-Chief' agent. 
    Synthesizes raw technical results into a professional, goal-oriented executive report.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = [create_executive_pdf]


    def run_task(self, overall_goal: str,task_results: dict,context_data: dict) -> FinalReportSchema:
        """Main method to generate the final report PDF and its structured data."""
        # 1. Get the structured data (the "Draft")
        report_data = self.generate_report(overall_goal,  task_results,context_data)
        
        # 2. Use the tool to build the PDF (the "Publishing")
        pdf_path = create_executive_pdf(report_data)

        return pdf_path, report_data

    def generate_report(self, overall_goal: str,  task_results: dict,context_data: dict) -> FinalReportSchema:
        """
        Takes the strategic goal, the original plan, and the execution results 
        to produce the structured Pydantic model for the PDF.
        """
        # Prepare the narrative context for the LLM
        formatted_results = self._format_results_for_prompt( task_results=task_results)
        
        # Render the prompt with the specific goal and results
        prompt = reporter_prompt_template.render(
            overall_goal=overall_goal,
            task_results=formatted_results,
            dataset_context=context_data
        )


        # Execute the LLM call with the structured schema
        raw, report_obj, content = self.ask(
            user_prompt=prompt,
            response_model=FinalReportSchema
        )
        
        return report_obj

    def _format_results_for_prompt(self, task_results: dict) -> str:
        """
        Directly parses the enriched task_results dictionary for the Reporter.
        """
        context_blocks = []

        # Sort keys to ensure the report follows the logical execution order
        for i in sorted(task_results.keys()):
            entry = task_results[i]
            
            # 1. Pull metadata directly from the entry
            user_q = entry.get("user_question", "General Inquiry")
            agent_name = entry.get("agent", "Unknown Agent").upper()
            instruction = entry.get("instruction", "No instruction provided.")
            
            # 2. Extract interpretation from the execution_output tuple
            execution_data = entry.get("execution_output")
            
            if isinstance(execution_data, tuple) and len(execution_data) > 1:
                # We want the 'results_interpretation' string
                interpretation = execution_data
            else:
                interpretation = "No result produced."

            # 3. Clean up the interpretation (remove raw code blocks if present)
            if "```" in interpretation:
                # Splits the code block out and keeps only the textual summary
                interpretation = interpretation.split("```")[-1].strip()

            # 4. Format the block for the Reporter's LLM prompt
            block = (
                f"### ANALYSIS SECTION: {user_q}\n"
                f"Executed By: {agent_name}\n"
                f"Instruction: {instruction}\n"
                f"Findings: {interpretation}\n"
            )
            context_blocks.append(block)
        
        return "\n---\n".join(context_blocks)