from fpdf import FPDF
from app.structured_outputs.reporter_structured_output import FinalReportSchema

def create_executive_pdf(report: FinalReportSchema, output_path: str = "Analysis_Report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # 1. THE BRANDED TITLE
    pdf.set_font("Helvetica", 'B', 20)
    pdf.cell(0, 15, report.dynamic_report_title, ln=True, align='C')
    pdf.ln(5)

    # 2. EXECUTIVE SUMMARY BOX (The "So What?")
    pdf.set_fill_color(240, 240, 240)  # Light grey background
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "EXECUTIVE SUMMARY", ln=True, fill=True)
    
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 7, "SO WHAT?", ln=True)
    pdf.set_font("Helvetica", '', 10)
    pdf.multi_cell(0, 5, report.synthesis.so_what)
    pdf.ln(2)

    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 7, "WHY IT MATTERS?", ln=True)
    pdf.set_font("Helvetica", '', 10)
    pdf.multi_cell(0, 5, report.synthesis.why_it_matters)
    pdf.ln(5)

    # 3. STRATEGIC RECOMMENDATIONS
    if report.synthesis.strategic_recommendations:
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 7, "STRATEGIC RECOMMENDATIONS", ln=True)
        pdf.set_font("Helvetica", '', 10)
        for rec in report.synthesis.strategic_recommendations:
            pdf.multi_cell(0, 5, f"- {rec}")
        pdf.ln(10)

    # 4. DETAILED ANALYSIS SECTIONS (The Deep Dives)
    for section in report.sections:
        pdf.add_page() # Start each major question on a new page for clarity
        pdf.set_font("Helvetica", 'B', 14)
        pdf.multi_cell(0, 10, section.revised_analysis_question)
        pdf.ln(5)

        # Insert Chart if it exists
        if section.visualizer_chart_path:
            # We assume the visualizer saved a .png
            pdf.image(section.visualizer_chart_path, x=10, w=180)
            pdf.ln(5)

        pdf.set_font("Helvetica", 'I', 11)
        pdf.multi_cell(0, 7, "Finding Summary:")
        pdf.set_font("Helvetica", '', 10)
        pdf.multi_cell(0, 5, section.reconciled_finding)
        pdf.ln(5)

        # Technical Data Block
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(0, 7, "Technical Evidence:", ln=True)
        pdf.set_font("Courier", '', 8) # Monospace for data tables
        pdf.multi_cell(0, 4, section.coder_stats_summary)

    pdf.output(output_path)
    return output_path