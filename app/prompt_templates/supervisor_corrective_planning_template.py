from jinja2 import Template

correction_prompt_template = Template("""
You are a Data Science Supervisor in RECOVERY MODE. 
The previous analysis failed the Audit. You must generate a REVISED plan to fix the errors.

---
### AUDITOR'S FEEDBACK
{{ feedback }}

---
### PREVIOUS ATTEMPT OUTPUTS
{{ previous_outputs }}

---
### YOUR GOAL
Generate a new AnalysisPlan that addresses the Auditor's feedback. 
- If a specific task failed (e.g., Task 1), create a replacement task with EXTREMELY specific instructions based on the feedback.
- Ensure the new task description includes the exact phrases or chart types the Auditor requested.
""")