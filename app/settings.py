# app/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Define the Root of your project (2 levels up from this file)
ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "config" / ".env"

def load_config():
    if CONFIG_PATH.exists():
        load_dotenv(CONFIG_PATH)
    else:
        # Fallback to current directory if not found in root
        load_dotenv() 

# Automatically load when this module is imported
load_config()

AGENT_API_KEY = os.getenv("OPENAI_API_KEY")