import sys
import io
import traceback
import contextlib
import pandas as pd
import regex as re
#-----------------------------------------------------------------------------------------------------------------#
#   Execute code                                                                                       #
#-----------------------------------------------------------------------------------------------------------------#

def execute_code(code: str, language: str = "python", file_path: str = None, namespace: dict = None):
    if language != "python":
        return {"status": "error", "message": f"Language {language} not supported."}
    
    if namespace is None:
        namespace = {}
    
    # 1. HYDRATION (Ensures it survives every attempt)
    try:
        import pandas as pd
        import matplotlib
        matplotlib.use('Agg') # This must come BEFORE importing pyplot
        import matplotlib.pyplot as plt
        import seaborn as sns
        namespace['pd'] = pd
        namespace['plt'] = plt
        namespace['sns'] = sns
        
        if 'df' not in namespace and file_path:
            namespace['df'] = pd.read_csv(file_path)
    except Exception as e:
        return {"status": "error", "message": f"Setup failed: {str(e)}"}
        
    stdout_capture = io.StringIO()
    
    # 2. SANITIZATION
    # Fix backslashes and strip invisible characters
    sanitized = re.sub(r'\\\s*\n', ' ', code).strip()
    
    try:
        with contextlib.redirect_stdout(stdout_capture):
            # 3. USE SANITIZED CODE & SHARED SCOPE
            # We pass namespace twice to make Globals == Locals
            exec(sanitized, namespace, namespace)
            
        return {
            "status": "success",
            "output": stdout_capture.getvalue(),
            "namespace": namespace  
        }
        
    except Exception as e:
        error_msg = traceback.format_exc()
        return {
            "status": "error",
            "output": stdout_capture.getvalue(),
            "message": error_msg
        }