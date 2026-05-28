import os
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from app.utils.logger import get_logger
from app.utils.storage import save_json

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

logger = get_logger(__name__)

def aggregate_violations(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Groups violations by page and by type."""
    by_page = {}
    by_type = {}
    
    for v in violations:
        page = v.get("page", 0)
        v_type = v.get("type", "Unknown")
        
        if page not in by_page:
            by_page[page] = []
        by_page[page].append(v)
        
        if v_type not in by_type:
            by_type[v_type] = []
        by_type[v_type].append(v)
        
    return {
        "by_page": by_page,
        "by_type": by_type,
        "total_violations": len(violations)
    }

def calculate_severity_score(violations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Computes counts of Critical, High, Medium, and Low severity issues."""
    severity = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for v in violations:
        sev = v.get("severity", "Medium")
        if sev in severity:
            severity[sev] += 1
        else:
            severity["Medium"] += 1
    return severity

def generate_json_report(file_path: str, violations: List[Dict[str, Any]], pages: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """Creates the structured JSON report with metadata."""
    report_data = {
        "metadata": {
            "file_name": os.path.basename(file_path),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_pages": len(pages),
        },
        "summary": {
            "severity_counts": calculate_severity_score(violations),
            "total_violations": len(violations)
        },
        "violations": aggregate_violations(violations)
    }
    
    save_json(report_data, output_path)
    logger.info(f"JSON report generated at {output_path}")
    return report_data

def generate_pdf_report(report_data: Dict[str, Any], output_path: str):
    """Uses reportlab to convert the JSON structured report into a beautiful PDF file."""
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'MainTitle', 
        parent=styles['Heading1'], 
        fontSize=24, 
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=20,
        alignment=1 # Center
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom', 
        parent=styles['Heading2'], 
        fontSize=18, 
        textColor=colors.HexColor("#34495E"),
        spaceBefore=20, spaceAfter=10
    )
    h3_style = ParagraphStyle(
        'Heading3_Custom', 
        parent=styles['Heading3'], 
        fontSize=14, 
        textColor=colors.HexColor("#2980B9"),
        spaceBefore=15, spaceAfter=8
    )
    normal_style = styles['Normal']
    
    # Table cell paragraph style (for wrapping text)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=10, leading=12)
    cell_style_bold = ParagraphStyle('CellStyleBold', parent=styles['Normal'], fontSize=10, leading=12, fontName="Helvetica-Bold")
    
    story = []
    
    # Title
    story.append(Paragraph("Compliance Scanning Report", title_style))
    story.append(Spacer(1, 20))
    
    # Metadata
    metadata = report_data.get("metadata", {})
    story.append(Paragraph("Document Information", h2_style))
    
    meta_data = [
        [Paragraph("<b>File Name:</b>", cell_style), Paragraph(str(metadata.get('file_name', 'Unknown')), cell_style)],
        [Paragraph("<b>Generated At:</b>", cell_style), Paragraph(str(metadata.get('generated_at', 'Unknown')), cell_style)],
        [Paragraph("<b>Total Pages:</b>", cell_style), Paragraph(str(metadata.get('total_pages', 0)), cell_style)]
    ]
    meta_table = Table(meta_data, colWidths=[120, 400])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # Summary
    summary = report_data.get("summary", {})
    story.append(Paragraph("Executive Summary", h2_style))
    
    sev_counts = summary.get("severity_counts", {})
    total_viol = summary.get('total_violations', 0)
    
    summary_data = [
        [Paragraph("<b>Total Violations:</b>", cell_style), Paragraph(str(total_viol), cell_style)],
        [Paragraph("<b>Critical Severity:</b>", cell_style_bold), Paragraph(f"<font color='red'>{sev_counts.get('Critical', 0)}</font>", cell_style_bold)],
        [Paragraph("<b>High Severity:</b>", cell_style), Paragraph(str(sev_counts.get('High', 0)), cell_style)],
        [Paragraph("<b>Medium Severity:</b>", cell_style), Paragraph(str(sev_counts.get('Medium', 0)), cell_style)],
        [Paragraph("<b>Low Severity:</b>", cell_style), Paragraph(str(sev_counts.get('Low', 0)), cell_style)]
    ]
    summary_table = Table(summary_data, colWidths=[120, 400])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Page Break before violations
    story.append(PageBreak())
    
    # Violations Details
    story.append(Paragraph("Violations Details", h2_style))
    story.append(Spacer(1, 10))
    
    violations_agg = report_data.get("violations", {})
    by_type = violations_agg.get("by_type", {})
    
    if not by_type:
        story.append(Paragraph("No compliance violations were detected in this document.", normal_style))
    
    for v_type, v_list in by_type.items():
        story.append(Paragraph(f"{v_type} Violations", h3_style))
        
        # Create a table for this violation type
        # Use Paragraphs for headers to ensure consistency and wrapping if needed
        table_data = [[
            Paragraph("<b>Page</b>", cell_style_bold),
            Paragraph("<b>Subtype</b>", cell_style_bold),
            Paragraph("<b>Severity</b>", cell_style_bold),
            Paragraph("<b>Value / Context</b>", cell_style_bold)
        ]]
        
        for v in v_list:
            # Wrap values in Paragraph to enforce text wrapping!
            # Truncate values to a reasonable length in case they are massive
            raw_val = str(v.get("value", "-"))
            if len(raw_val) > 1000:
                raw_val = raw_val[:1000] + "..."
                
            table_data.append([
                Paragraph(str(v.get("page", "-")), cell_style),
                Paragraph(str(v.get("subtype", "-")), cell_style),
                Paragraph(str(v.get("severity", "-")), cell_style),
                Paragraph(raw_val, cell_style)
            ])
            
        # Define column widths to total ~ 530 for letter size (8.5x11 inches = 612x792 points, minus 80 margins)
        t = Table(table_data, colWidths=[40, 110, 60, 320])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#34495E")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('TOPPADDING', (0,0), (-1,0), 10),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#2C3E50")),
        ]))
        
        # Add alternating row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                t.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F9F9F9"))]))
            else:
                t.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.white)]))
                
        story.append(t)
        story.append(Spacer(1, 20))
        
    doc.build(story)
    logger.info(f"Beautiful PDF report generated at {output_path}")

def generate_report(state: Dict[str, Any]) -> Dict[str, str]:
    """
    Main entry point that coordinates the report generation.
    Returns the paths to the generated reports.
    """
    file_path = state.get("file_path", "unknown_file")
    violations = state.get("violations", [])
    extracted_pages = state.get("extracted_pages", [])
    
    base_name = os.path.basename(file_path).split('.')[0]
    json_path = os.path.join("data/reports", f"{base_name}_report.json")
    pdf_path = os.path.join("data/reports", f"{base_name}_report.pdf")
    
    # Ensure reports directory exists
    os.makedirs("data/reports", exist_ok=True)
    
    report_data = generate_json_report(file_path, violations, extracted_pages, json_path)
    
    try:
        generate_pdf_report(report_data, pdf_path)
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")
        # fallback to empty string if failed
        return {"json": json_path, "pdf": ""}
        
    return {"json": json_path, "pdf": pdf_path}
