# Import Libraries
from app.agent import AIAgent


class Supervisor(AIAgent):
    def __init__(self, **kwargs):
        # Initialize the base AIAgent
        super().__init__(**kwargs)
        self.template_name = "supervisor_prompt.j2"

def run_task(self, user_query: str, context_data: dict,**kwargs):
    # 1. Render the 'Instructions + Context' for the System Role
    system_instructions = self.render_template(
        "supervisor_instructions.j2", 
        context=context_data
    )
    
    # 2. Pass them into your existing 'ask' method
    raw,parsed_response,content = self.ask(
        input_text=user_query,           # The User Input
        instructions=system_instructions,  # The System Prompt
        **kwargs
    )
    
    return raw,parsed_response,content
        
