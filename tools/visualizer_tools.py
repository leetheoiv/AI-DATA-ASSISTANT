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
import ast
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — no display required
import matplotlib.pyplot as plt
from langchain.tools import tool
 
# Import optional charting libs — graceful fallback if not installed
try:
    import plotly.express as px
    import plotly.graph_objs as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
 
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Shared exec scope — same one used by coder_tools
#  Import it so the DataFrame loaded by the coder is available here too
# ─────────────────────────────────────────────────────────────────────────────
 
from tools.coder_tools import _EXEC_STATE
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Tool: create_chart
# ─────────────────────────────────────────────────────────────────────────────
 
@tool("create_chart", description=(
    "Generate a chart from the coder's raw result and save it to disk. "
    "Pass the coder's raw_result string, choose a chart_type "
    "(bar, line, scatter, histogram, heatmap, box, pie, violin), "
    "and provide axis labels and a title. "
    "Returns the file path of the saved chart."
))
def create_chart(
    coders_raw_result: str,
    chart_type: str,
    x_label: str,
    y_label: str,
    title: str,
    caption: str = "",
) -> dict:
    """
    Generate a chart from the coder's output and save it as a PNG.
 
    Args:
        coders_raw_result: The raw_result string from the coder step.
                           Can be a dict, list, or DataFrame records string.
        chart_type:        Chart type: bar, line, scatter, histogram,
                           heatmap, box, pie, violin, kde.
        x_label:           Column name or label for the x axis.
        y_label:           Column name or label for the y axis.
        title:             Chart title.
        caption:           Optional caption / description of what the chart shows.
 
    Returns:
        {
            "success":    bool,
            "chart_path": path to saved PNG,
            "chart_type": chart type used,
            "title":      chart title,
            "caption":    caption,
            "error":      error message if failed
        }
    """
    df = _EXEC_STATE.get("df")
    if df is None:
        return {
            "success": False,
            "error": "No dataset loaded. Ensure the coder step ran first.",
        }
 
    # ── Parse coder's raw result ──────────────────────────────────────────────
    chart_df = None

 
    # ── Ensure output directory exists ───────────────────────────────────────
    os.makedirs("charts", exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in "_- " else "_" for c in title)
    chart_path = f"charts/{safe_title.replace(' ', '_')}.png"
 
    # ── Generate chart ───────────────────────────────────────────────────────
    try:
        ct = (chart_type or "bar").lower()
        plt.close("all")
 
        if ct == "bar":
            _x = chart_df[x_label] if x_label in chart_df.columns else chart_df.iloc[:, 0]
            _y = chart_df[y_label] if y_label in chart_df.columns else chart_df.iloc[:, 1]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(_x, _y)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_title(title)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
 
        elif ct == "line":
            _x = chart_df[x_label] if x_label in chart_df.columns else chart_df.iloc[:, 0]
            _y = chart_df[y_label] if y_label in chart_df.columns else chart_df.iloc[:, 1]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(_x, _y, marker="o")
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_title(title)
            plt.tight_layout()
 
        elif ct == "scatter":
            _x = chart_df[x_label] if x_label in chart_df.columns else chart_df.iloc[:, 0]
            _y = chart_df[y_label] if y_label in chart_df.columns else chart_df.iloc[:, 1]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(_x, _y, alpha=0.6)
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_title(title)
            plt.tight_layout()
 
        elif ct == "histogram":
            _x = chart_df[x_label] if x_label in chart_df.columns else chart_df.iloc[:, 0]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(_x, bins=20, edgecolor="black")
            ax.set_xlabel(x_label)
            ax.set_ylabel("Frequency")
            ax.set_title(title)
            plt.tight_layout()
 
        elif ct == "heatmap" and SEABORN_AVAILABLE:
            corr = df.select_dtypes(include=[np.number]).corr()
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(corr, annot=True, cmap="vlag", ax=ax)
            ax.set_title(title)
            plt.tight_layout()
 
        elif ct == "box":
            _x = chart_df[x_label] if x_label in chart_df.columns else None
            _y = chart_df[y_label] if y_label in chart_df.columns else chart_df.iloc[:, 0]
            fig, ax = plt.subplots(figsize=(10, 6))
            if _x is not None:
                chart_df.boxplot(column=y_label, by=x_label, ax=ax)
            else:
                ax.boxplot(_y)
            ax.set_title(title)
            plt.suptitle("")
            plt.tight_layout()
 
        elif ct == "pie":
            _labels = chart_df[x_label] if x_label in chart_df.columns else chart_df.iloc[:, 0]
            _values = chart_df[y_label] if y_label in chart_df.columns else chart_df.iloc[:, 1]
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(_values, labels=_labels, autopct="%1.1f%%")
            ax.set_title(title)
            plt.tight_layout()
 
        elif ct == "violin" and SEABORN_AVAILABLE:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.violinplot(
                data=chart_df,
                x=x_label if x_label in chart_df.columns else None,
                y=y_label if y_label in chart_df.columns else chart_df.columns[0],
                ax=ax,
            )
            ax.set_title(title)
            plt.tight_layout()
 
        elif ct == "kde" and SEABORN_AVAILABLE:
            fig, ax = plt.subplots(figsize=(10, 6))
            _col = x_label if x_label in chart_df.columns else chart_df.columns[0]
            sns.kdeplot(data=chart_df, x=_col, fill=True, ax=ax)
            ax.set_title(title)
            plt.tight_layout()
 
        else:
            # Default fallback — bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            numeric_cols = chart_df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                chart_df[numeric_cols[0]].plot(kind="bar", ax=ax)
                ax.set_title(title)
            plt.tight_layout()
 
        # ── Save to disk ──────────────────────────────────────────────────────
        plt.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close("all")
 
        return {
            "success":    True,
            "chart_path": chart_path,
            "chart_type": ct,
            "title":      title,
            "caption":    caption,
            "error":      None,
        }
 
    except Exception:
        plt.close("all")
        return {
            "success": False,
            "chart_path": None,
            "error": traceback.format_exc(),
        }
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Tool: format_chart_result
# ─────────────────────────────────────────────────────────────────────────────
 
@tool("format_chart_result", description=(
    "Produce a clean text description of the chart that was just created. "
    "Call this after create_chart succeeds. Include what the chart shows, "
    "the key insight, and any business rule interpretations."
))
def format_chart_result(
    step_title: str,
    chart_path: str,
    chart_type: str,
    title: str,
    caption: str = "",
    business_rule_notes: str = "",
) -> dict:
    """
    Produce a clean description of the chart for the reporter.
 
    Args:
        step_title:          The analysis step title.
        chart_path:          Path to the saved chart file.
        chart_type:          Type of chart (bar, line, etc.)
        title:               Chart title.
        caption:             Caption describing what the chart shows.
        business_rule_notes: Business rules relevant to interpretation.
 
    Returns:
        {"success": bool, "description": formatted text description}
    """
    try:
        description = (
            f"**{step_title}**\n\n"
            f"Chart type: {chart_type}\n"
            f"Title: {title}\n"
            f"Saved to: {chart_path}\n"
        )
        if caption:
            description += f"\n{caption}"
        if business_rule_notes:
            description += f"\n\n*Interpretation: {business_rule_notes}*"
 
        return {"success": True, "description": description}
 
    except Exception as e:
        return {"success": False, "error": str(e)}
