import json
import io
from datetime import datetime
from typing import Dict, Any
from app.utils.logger import get_logger
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = get_logger(__name__)

def generate_reports(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates beautifully formatted JSON and PDF reports in memory.
    """
    logger.info("Generating beautiful in-memory reports...")
    violations = state.get("violations", [])
    file_name = state.get("file_name", "Unknown Document.pdf")
    
    # 1. Generate JSON String
    report_json_str = json.dumps(violations, indent=4)
    
    # 2. Generate PDF Bytes
    pdf_buffer = io.BytesIO()
    # Adjust margins
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, spaceAfter=10, textColor=colors.HexColor("#111827"))
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor("#4b5563"), spaceAfter=5)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=10, leading=12)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=11, textColor=colors.white, fontName='Helvetica-Bold')
    
    story = []
    
    # Header
    story.append(Paragraph("AI Compliance & Security Report", title_style))
    story.append(Spacer(1, 10))
    
    # Metadata
    now = datetime.now()
    story.append(Paragraph(f"<b>File Name:</b> {file_name}", meta_style))
    story.append(Paragraph(f"<b>Scan Date:</b> {now.strftime('%B %d, %Y')}", meta_style))
    story.append(Paragraph(f"<b>Scan Time:</b> {now.strftime('%I:%M %p')}", meta_style))
    story.append(Spacer(1, 15))
    
    # Group by Severity
    sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    sev_data = {"Critical": [], "High": [], "Medium": [], "Low": []}
    
    for v in violations:
        sev = v.get("severity", "High").capitalize()
        if sev not in sev_counts:
            sev = "High"
        sev_counts[sev] += 1
        sev_data[sev].append(v)
        
    # Summary Table
    story.append(Paragraph("<b>Violation Summary</b>", styles['Heading2']))
    story.append(Spacer(1, 5))
    
    summary_data = [
        [Paragraph("Severity", header_style), Paragraph("Violation Count", header_style)]
    ]
    for s in ["Critical", "High", "Medium", "Low"]:
        summary_data.append([Paragraph(s, cell_style), Paragraph(str(sev_counts[s]), cell_style)])
        
    summary_table = Table(summary_data, colWidths=[150, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4b5563")), # Grey header
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#d1d5db")),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f9fafb"))
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    if not violations:
        story.append(Paragraph("✅ No compliance violations detected. The document is clear.", styles['Normal']))
    else:
        story.append(Paragraph("<b>Detailed Findings</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        colors_map = {
            "Critical": colors.HexColor("#8b5cf6"), # Violet
            "High": colors.HexColor("#ef4444"), # Red
            "Medium": colors.HexColor("#eab308"), # Yellow
            "Low": colors.HexColor("#22c55e")  # Green
        }
        
        for sev in ["Critical", "High", "Medium", "Low"]:
            if sev_counts[sev] > 0:
                # Add Severity Header Section
                story.append(Paragraph(f"<font color='{colors_map[sev]}'>■</font> <b>{sev} Violations ({sev_counts[sev]})</b>", styles['Heading3']))
                story.append(Spacer(1, 5))
                
                # Table Data
                table_data = [
                    [Paragraph("Type", header_style), Paragraph("Details", header_style), Paragraph("Page", header_style)]
                ]
                
                for v in sev_data[sev]:
                    v_type = f"{v.get('type')} ({v.get('subtype', '')})"
                    val = str(v.get('value', ''))
                    # Text wrapping handled by Paragraph
                    table_data.append([
                        Paragraph(v_type, cell_style),
                        Paragraph(val, cell_style),
                        Paragraph(str(v.get('page', 'N/A')), cell_style)
                    ])
                    
                t = Table(table_data, colWidths=[150, 320, 50])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors_map[sev]),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb")),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white)
                ]))
                story.append(t)
                story.append(Spacer(1, 15))
                
    doc.build(story)
    report_pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    
    logger.info("Successfully generated beautiful in-memory JSON and PDF reports.")
    return {
        "report_json_str": report_json_str,
        "report_pdf_bytes": report_pdf_bytes
    }
