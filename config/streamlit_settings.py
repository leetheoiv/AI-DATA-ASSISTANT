"""
Settings and configurations for Streamlit app. This includes API keys, model choices, 
and other parameters that can be easily adjusted without modifying the core codebase.
"""

API_BASE = "http://localhost:8000/analysis"

SEABORN_PALETTES = [
    "viridis", "magma", "plasma", "inferno", "cividis",
    "Blues", "Greens", "Reds", "Oranges", "Purples",
    "coolwarm", "RdBu", "Spectral", "Set2", "tab10",
    "muted", "pastel", "deep", "bright", "dark",
]