import json
import io
from typing import Dict, Any
from app.utils.logger import get_logger
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

logger = get_logger(__name__)

def generate_reports(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates JSON and PDF reports in memory and returns their raw bytes/strings.
    Replaces disk-based generation.
    """
    logger.info("Generating in-memory reports...")
    violations = state.get("violations", [])
    
    # 1. Generate JSON String
    report_json_str = json.dumps(violations, indent=4)
    
    # 2. Generate PDF Bytes
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("AI Compliance Scanner Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    if not violations:
        story.append(Paragraph("✅ No compliance violations detected. The document is clear.", styles['Normal']))
    else:
        story.append(Paragraph(f"⚠️ Found {len(violations)} violations.", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Build Table
        table_data = [["Severity", "Type", "Details", "Page"]]
        for v in violations:
            sev = v.get('severity', 'High')
            v_type = f"{v.get('type')} ({v.get('subtype', '')})"
            details = str(v.get('value', ''))[:100] + "..." if len(str(v.get('value', ''))) > 100 else str(v.get('value', ''))
            page = str(v.get('page', 'N/A'))
            table_data.append([sev, v_type, details, page])
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f3f4f6")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)
        
    doc.build(story)
    report_pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    
    logger.info("Successfully generated in-memory JSON and PDF reports.")
    return {
        "report_json_str": report_json_str,
        "report_pdf_bytes": report_pdf_bytes
    }
