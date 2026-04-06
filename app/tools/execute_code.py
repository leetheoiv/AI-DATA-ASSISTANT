import sys
import io
import traceback
import contextlib

import regex as re
#-----------------------------------------------------------------------------------------------------------------#
#   Execute code                                                                                       #
#-----------------------------------------------------------------------------------------------------------------#

def execute_code(code: str, language: str = "python", namespace: dict = None):
    if language != "python":
        return {
            "status": "error", 
            "message": f"Language {language} not supported."
        }
    
    # Use existing namespace if provided (maintains state across calls), or create a new one
    if namespace is None:
        namespace = {}
        
    # Capture standard output (what the LLM prints)
    stdout_capture = io.StringIO()
    
    sanitized = re.sub(r'\\\s*\n', ' ', code)
    # 3. Strip leading/trailing whitespace that might hide invisible chars
    sanitized = sanitized.strip()
    try:
        # Redirect stdout to our StringIO buffer
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, {"__builtins__": __builtins__}, namespace)
            
        return {
            "status": "success",
            "output": stdout_capture.getvalue(),
            "namespace": namespace  # Keep state intact
        }
        
    except Exception as e:
        # Capture the full traceback if it fails
        error_msg = traceback.format_exc()
        print(f"[Execution Error]: {e}", file=sys.stderr)
        return {
            "status": "error",
            "output": stdout_capture.getvalue(), # Show what ran before it broke
            "message": error_msg
        }