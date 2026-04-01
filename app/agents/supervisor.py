# Import Libraries
from app.agent import AIAgent
from app.prompt_templates.supervisor_prompt_template import supervisor_prompt_template

class Supervisor(AIAgent):
    def __init__(self,context_data: dict, **kwargs):
        # Initialize the base AIAgent
        super().__init__(**kwargs)
        self.system_prompt = supervisor_prompt_template.render(
            dataset_context=context_data
        )
        self.template_name = "supervisor_prompt.j2"

    def run_task(self, user_query: str,**kwargs):
        # 1. Render the 'Instructions + Context' for the System Role
        
        # 2. Pass them into your existing 'ask' method
        raw,parsed_response,content = self.ask(
            user_prompt=user_query,           # The User Input
            **kwargs
        )
        
        return raw,parsed_response,content
        
