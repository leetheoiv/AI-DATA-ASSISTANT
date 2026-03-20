import os
from dotenv import load_dotenv
load_dotenv("config/.env")

from agent import AIAgent

PROMPTS = [
    "Say hello.",
    "What is 2+2?",
    "Give a short haiku about testing.",
]

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set; set it and re-run.")
        raise SystemExit(1)
    agent = AIAgent(api_key=api_key)
    agent.create_agent(model_name='test')
    for prompt in PROMPTS:
        resp = agent.send(messages=[{"role": "user", "content": prompt}], response_format="text")
        print("PROMPT:", prompt)
        print("RESPONSE:", resp)
        print("---")