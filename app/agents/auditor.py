# Import Libraries
from app.agent import AIAgent
import io
import contextlib
import traceback
from app.prompt_templates.evaluator_prompt_template import evaluator_prompt_template
from app.tools.execute_code import execute_code 
from app.structured_outputs.evaluator_structured_output import AuditResult    


class Evaluator(AIAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # The Auditor uses a "Checklist" prompt, not a planning prompt
        

    def audit(self, user_questions, context_data: dict,task_outputs):
        # The Auditor returns a Simple Boolean + Feedback string
        # You don't even necessarily need a full AnalysisPlan Pydantic model here, 
        # just a "Pass/Fail" check.

        self.system_prompt = evaluator_prompt_template.render(
            dataset_context=context_data,
            user_questions=user_questions,
            task_outputs=task_outputs
        )

        # 2. ASK with a simple trigger
        # Since the system prompt now has all the data, the user prompt can be minimal
        raw, audit_result, content = self.ask(
            user_prompt="Commence the audit based on the provided results and questions.",
            response_model=AuditResult
        )
            
        return audit_result