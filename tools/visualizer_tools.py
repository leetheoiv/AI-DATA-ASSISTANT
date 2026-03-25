import traceback
from io import StringIO
from contextlib import redirect_stdout

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go   
import seaborn as sns
from langchain.tools import tool
import seaborn as sns
import base64
from io import BytesIO


# ─────────────────────────────────────────────────────────────────────────────
#  Shared execution scope — persists the DataFrame between tool calls
#  within a single agent invocation
# ─────────────────────────────────────────────────────────────────────────────

_EXEC_STATE: dict = {
    "df":        None,
    "file_path": None,
}


def load_dataframe(file_path: str) -> pd.DataFrame:
    """Load a CSV or Excel file into the shared exec scope."""
    if file_path.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    _EXEC_STATE["df"] = df
    _EXEC_STATE["file_path"] = file_path
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Tool: create_visualization
# ─────────────────────────────────────────────────────────────────────────────
_LAST_PLOT_DATA = {
    "image_base64": None,
    "plotly_dict": None
}
@tool("create_chart", description=(
    "Use this tool to create a given chart. "
    "You MUST provide chart_type, x_label, and y_label. Do not attempt to write code without calling this tool."
))
def create_chart(
    chart_type: str = None, 
    x_label: str = None, 
    y_label: str = None, 
    title: str = "Visualization", 
    caption: str = ""
) -> dict:
    global _LAST_PLOT_DATA
    print(f"--- [DEBUG] create_chart called: {chart_type} ---")
    
    df = _EXEC_STATE.get("df")
    if df is None:
        return {"success": False, "error": "No dataset loaded."}

    plt.close('all')
    stdout_capture = StringIO()
    raw = None

    try:
        # 1. Logic for generating 'raw' (px, sns, or plt)
        if chart_type:
            ct = chart_type.lower()
            x = x_label.lower().replace(" ", "_") if x_label else None
            y = y_label.lower().replace(" ", "_") if y_label else None
            
            if ct == "bar": raw = px.bar(df, x=x_label, y=y_label, title=title)
            elif ct == "line": raw = px.line(df, x=x_label, y=y_label, title=title)
            elif ct == "scatter": raw = px.scatter(df, x=x_label, y=y_label, title=title)
            elif ct == "histogram": raw = px.histogram(df, x=x_label, title=title)
            elif ct == "violin": raw = px.violin(df, x=x, y=y, title=title, box=True, points="all")
            elif ct == "box": raw = px.box(df, x=x, y=y, title=title)
            elif ct == "heatmap":
                plt.figure(figsize=(10, 8))
                sns.heatmap(df.select_dtypes(include=[np.number]).corr(), annot=True, cmap="vlag")
                plt.title(title)
                raw = plt.gcf()

        if raw is None:
            return {"success": False, "error": f"Unsupported chart type: {chart_type}"}

        # 2. SEPARATE THE PAYLOAD
        # Reset cache for new plot
        _LAST_PLOT_DATA = {"image_base64": None, "plotly_dict": None}

        if isinstance(raw, (go.Figure, dict)):
            # Store Plotly data IN CACHE, not in the return dict
            _LAST_PLOT_DATA["plotly_dict"] = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw)
            msg = "PLOTLY_CHART_READY"
        else:
            # Store Matplotlib Base64 IN CACHE
            fig = raw.fig if hasattr(raw, "fig") else raw
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            _LAST_PLOT_DATA["image_base64"] = base64.b64encode(buf.read()).decode("utf-8")
            msg = "STATIC_IMAGE_READY"

        # 3. RETURN MINI-RESPONSE TO LLM
        # We tell the LLM the plot is ready, but we DON'T give it the bytes.
        return {
            "success": True,
            "result": f"Successfully generated {chart_type}. Metadata: {msg}",
            "title": title,
            "caption": caption,
            "storage_status": "DATA_HELD_IN_CACHE" # Sentinel for our Python code
        }

    except Exception:
        return {"success": False, "error": traceback.format_exc()}