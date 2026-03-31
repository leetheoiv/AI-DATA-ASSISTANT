🏗️ The AI Data Agent Lifecycle 0. Context Mapping (The "Grounding")
Before writing a single line of code, identify the Dataset Context requirements.

Action: Map out which specific columns, business rules, and known data issues from your DatasetContext Pydantic model this agent needs to "know" to be successful.

Goal: Prevent "Context Bloat" by only passing the metadata relevant to this specific agent's task.

1. Data Contract (The "Schema")
   Define a Pydantic Model for the agent's expected output in app/structured_outputs.py.

   Action: Create a strict schema (e.g., AnalysisPlan, ClarificationRequest).

   Goal: Use Pydantic to force the LLM to return valid JSON, preventing your pipeline from crashing on a "hallucinated" string.

2. Prompt Orchestration (The "Blueprint")
   Draft a Jinja2 Template (.j2) in app/prompt_templates/.

   Action: Use Jinja logic ({% if %}, {% for %}) to inject the DatasetContext dynamically.

   Goal: Keep your "System Instructions" clean and modular, separate from your Python code.

3. Agent Implementation (The "Brain")
   Build the Specialized Agent Class in app/agents/.

   Action: Create a class that inherits from your base AIAgent, pre-configured with the correct model (e.g., GPT-4o), temperature, and the Jinja template from Step 2.

   Goal: Encapsulate the "personality" and technical settings of the agent.

4. Pipeline Integration (The "Routing")
   Register the agent within your Main Orchestrator (the Supervisor).

   Action: Update the Supervisor's logic so it knows when to "hand off" a task to this new agent based on the user's query.

   Goal: Enable multi-agent collaboration where the Supervisor acts as the project manager.

5. Evaluation & Audit (The "Feedback Loop")
   Implement automated logging in your /logs folder.

   Action: Save the Prompt, Raw LLM Output, and Validation Status for every run.

   Goal: Review these logs to identify where the agent is failing—allowing you to go back to Step 2 and refine the prompt.
