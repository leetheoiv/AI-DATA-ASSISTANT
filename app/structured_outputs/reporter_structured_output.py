from pydantic import BaseModel, Field
from typing import List, Optional

class QuestionAnalysis(BaseModel):
    revised_analysis_question: str = Field(description="The Supervisor's refined, technically precise question.")
    visualizer_chart_path: Optional[str] = Field(description="Local path to the generated chart image.")
    reconciled_finding: str = Field(description="Narrative merging math and visual into one story.")
    coder_stats_summary: str = Field(description="Key statistical findings or tables.")

class ExecutiveSynthesis(BaseModel):
    so_what: str = Field(description="The bottom-line conclusion for leadership. (TOP OF PDF)")
    why_it_matters: str = Field(description="The business risk or opportunity identified. (TOP OF PDF)")
    strategic_recommendations: Optional[List[str]] = Field(description="Actionable steps based on the analysis goal.")
    evidence_summary: str = Field(description="High-level recap of the data points supporting the findings.")
    methodology: str = Field(description="Brief overview of tools and tests used.")

class FinalReportSchema(BaseModel):
    # The Reporter will generate this based on the Overall Goal
    dynamic_report_title: str = Field(description="A professional, insight-driven title (e.g., 'Optimization Strategy for Customer ARPU').")
    
    # BLUF Section (Top of PDF)
    synthesis: ExecutiveSynthesis = Field(description="The primary executive summary (So What/Why/Recommendations).")
    
    # Detailed Data Sections
    sections: List[QuestionAnalysis] = Field(description="Deep-dive results grouped by the Supervisor's revised questions.")