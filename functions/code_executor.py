import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from structured_outputs.visualizer_structured_output import VisualizerOutput

def execute_ai_code(spec: VisualizerOutput, df: pd.DataFrame):
    # Setup the environment for the code
    local_vars = {
        "df": df,
        "plt": plt,
        "sns": sns,
        "np": np,
        "chart_path": spec.chart_path,
        "plotly":px
    }
    
    try:
        # Execute the AI's custom creative code
        exec(spec.visualizer_code, {}, local_vars)
        return True, None
    except Exception as e:
        return False, str(e)