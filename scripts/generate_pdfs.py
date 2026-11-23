"""
PDF Document Generator for PS-068 Project
Converts Markdown documents to beautifully styled PDFs using ReportLab.
Generates:
1. docs/design_document.pdf
2. docs/decision_log.pdf
3. docs/test_suite_report.pdf
And creates copies in the root directory for immediate access.
"""

import os
import re
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Preformatted
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages after page 1)
        if self._pageNumber > 1:
            header_text = getattr(self, "doc_header_title", "PS-068 Student Attendance & Condonation Engine")
            self.drawString(54, letter[1] - 36, header_text)
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)
        
        # Footer (all pages)
        footer_left = "PS-068 Institutional Project Documentation"
        footer_right = f"Page {self._pageNumber} of {page_count}"
        self.drawString(54, 32, footer_left)
        self.drawRightString(letter[0] - 54, 32, footer_right)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 42, letter[0] - 54, 42)
        
        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=base['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#3B82F6'),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'DocH1',
        parent=base['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=base['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1D4ED8'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    h3_style = ParagraphStyle(
        'DocH3',
        parent=base['Heading4'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#374151'),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=5
    )
    
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1F2937'),
        leftIndent=14,
        spaceAfter=3
    )

    quote_style = ParagraphStyle(
        'DocQuote',
        parent=base['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1E40AF'),
        leftIndent=15,
        rightIndent=15,
        spaceBefore=4,
        spaceAfter=6
    )
    
    table_cell_style = ParagraphStyle(
        'DocTableCell',
        parent=base['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1F2937')
    )
    
    table_header_style = ParagraphStyle(
        'DocTableHeader',
        parent=base['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    code_style = ParagraphStyle(
        'DocCode',
        parent=base['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#111827')
    )

    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'h1': h1_style,
        'h2': h2_style,
        'h3': h3_style,
        'body': body_style,
        'bullet': bullet_style,
        'quote': quote_style,
        'table_cell': table_cell_style,
        'table_header': table_header_style,
        'code': code_style
    }


def clean_markdown_inline(text):
    """Convert common inline markdown tags to ReportLab tags."""
    # Convert bold+italic
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Convert bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert italic
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Convert inline code: `code`
    def code_repl(m):
        code_text = m.group(1).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<font face="Courier" color="#1E3A8A"><b>{code_text}</b></font>'
    text = re.sub(r'`(.*?)`', code_repl, text)
    # Convert mathematical symbols like \lfloor, \rfloor, \implies, \times, \ge, \le
    text = text.replace(r'\lfloor', '[').replace(r'\rfloor', ']').replace(r'\times', '×')
    text = text.replace(r'\implies', '⇒').replace(r'\ge', '≥').replace(r'\le', '≤')
    text = text.replace(r'\approx', '≈').replace(r'\to', '→').replace(r'\cdot', '·')
    text = text.replace(r'\text{', '').replace('}', '')
    # Strip bare math dollars $...$
    text = re.sub(r'\$([^$]+)\$', r'<i>\1</i>', text)
    return text


def parse_markdown_to_flowables(md_content, styles, doc_title=""):
    flowables = []
    lines = md_content.splitlines()
    i = 0
    total_lines = len(lines)
    
    in_code_block = False
    code_lines = []
    
    while i < total_lines:
        line = lines[i]
        stripped = line.strip()
        
        # Check code fence
        if stripped.startswith("```"):
            if in_code_block:
                # End code block
                code_text = "\n".join(code_lines)
                # Split code into table or preformatted box
                code_p = Preformatted(code_text, styles['code'])
                t = Table([[code_p]], colWidths=[letter[0] - 108])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
                    ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                    ('RIGHTPADDING', (0,0), (-1,-1), 8),
                ]))
                flowables.append(Spacer(1, 4))
                flowables.append(t)
                flowables.append(Spacer(1, 4))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue
            
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
            
        # Empty line
        if not stripped:
            i += 1
            continue
            
        # Table detection
        if stripped.startswith("|") and stripped.endswith("|"):
            # Gather all contiguous table lines
            table_raw = []
            while i < total_lines and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                row_line = lines[i].strip()
                # Check if it's separator row | :--- | :--- |
                if not re.match(r'^\|[\s\-:]+(\|[\s\-:]+)+\|$', row_line):
                    # Data or header row
                    cells = [c.strip() for c in row_line.strip('|').split('|')]
                    table_raw.append(cells)
                i += 1
                
            if table_raw:
                # Normalize column count
                num_cols = max(len(r) for r in table_raw)
                avail_width = letter[0] - 108  # 504 points
                col_width = avail_width / num_cols
                
                # Check if first column should be smaller
                if num_cols >= 4:
                    col_widths = [avail_width * 0.15, avail_width * 0.35, avail_width * 0.20, avail_width * 0.30]
                    if len(col_widths) < num_cols:
                        col_widths = [col_width] * num_cols
                else:
                    col_widths = [col_width] * num_cols

                table_data = []
                for row_idx, r in enumerate(table_raw):
                    padded_row = r + [''] * (num_cols - len(r))
                    row_cells = []
                    for c in padded_row:
                        c_clean = clean_markdown_inline(c)
                        if row_idx == 0:
                            p = Paragraph(c_clean, styles['table_header'])
                        else:
                            p = Paragraph(c_clean, styles['table_cell'])
                        row_cells.append(p)
                    table_data.append(row_cells)
                    
                table_style_cmds = [
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 5),
                    ('RIGHTPADDING', (0,0), (-1,-1), 5),
                ]
                # Alternating row colors
                for r_idx in range(1, len(table_data)):
                    bg = colors.HexColor('#F8FAFC') if r_idx % 2 == 1 else colors.white
                    table_style_cmds.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))
                    
                t = Table(table_data, colWidths=col_widths, repeatRows=1)
                t.setStyle(TableStyle(table_style_cmds))
                flowables.append(Spacer(1, 4))
                flowables.append(t)
                flowables.append(Spacer(1, 6))
            continue
            
        # Horizontal rule
        if stripped in ('---', '***', '___'):
            # Divider line
            d_table = Table([['']], colWidths=[letter[0] - 108], rowHeights=[1])
            d_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            flowables.append(Spacer(1, 6))
            flowables.append(d_table)
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # Headings
        if stripped.startswith("# "):
            title_text = clean_markdown_inline(stripped[2:])
            flowables.append(Paragraph(title_text, styles['title']))
            i += 1
            continue
            
        if stripped.startswith("## "):
            h1_text = clean_markdown_inline(stripped[3:])
            flowables.append(Paragraph(h1_text, styles['h1']))
            i += 1
            continue
            
        if stripped.startswith("### "):
            h2_text = clean_markdown_inline(stripped[4:])
            flowables.append(Paragraph(h2_text, styles['h2']))
            i += 1
            continue
            
        if stripped.startswith("#### "):
            h3_text = clean_markdown_inline(stripped[5:])
            flowables.append(Paragraph(h3_text, styles['h3']))
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            quote_text = clean_markdown_inline(stripped.lstrip('>').strip())
            qp = Paragraph(quote_text, styles['quote'])
            q_table = Table([[qp]], colWidths=[letter[0] - 108])
            q_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
                ('LINELEFT', (0,0), (0,-1), 2.5, colors.HexColor('#2563EB')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            flowables.append(Spacer(1, 2))
            flowables.append(q_table)
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # Bullet point or numbered item
        bullet_match = re.match(r'^(\*|-|\d+\.)\s+(.*)$', stripped)
        if bullet_match:
            bullet_prefix = bullet_match.group(1)
            bullet_content = clean_markdown_inline(bullet_match.group(2))
            if bullet_prefix in ('*', '-'):
                bullet_symbol = "• "
            else:
                bullet_symbol = f"{bullet_prefix} "
            bp = Paragraph(f"<b>{bullet_symbol}</b>{bullet_content}", styles['bullet'])
            flowables.append(bp)
            i += 1
            continue

        # Regular paragraph
        body_text = clean_markdown_inline(stripped)
        flowables.append(Paragraph(body_text, styles['body']))
        i += 1

    return flowables


def build_pdf(md_path, pdf_path, header_title):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    styles = get_styles()
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    flowables = parse_markdown_to_flowables(md_content, styles, header_title)
    
    # Custom canvas with document header
    class CustomCanvas(NumberedCanvas):
        doc_header_title = header_title
        
    doc.build(flowables, canvasmaker=CustomCanvas)
    print(f"Successfully generated: {pdf_path}")


def main():
    print("Starting PDF generation for PS-068 Documentation...")
    
    targets = [
        {
            "src": "docs/design_document.md",
            "pdf_doc": "docs/design_document.pdf",
            "pdf_root": "design_document.pdf",
            "header": "PS-068 Technical Architecture & Design Document"
        },
        {
            "src": "docs/decision_log.md",
            "pdf_doc": "docs/decision_log.pdf",
            "pdf_root": "decision_log.pdf",
            "header": "PS-068 Architecture Decision Log (ADRs)"
        },
        {
            "src": "tests/test_suite_report.md",
            "pdf_doc": "docs/test_suite_report.pdf",
            "pdf_root": "test_suite_report.pdf",
            "header": "PS-068 Complete Test Suite Verification Report"
        }
    ]
    
    for t in targets:
        if os.path.exists(t["src"]):
            build_pdf(t["src"], t["pdf_doc"], t["header"])
            # Copy to root as well for immediate visibility
            shutil.copy2(t["pdf_doc"], t["pdf_root"])
            print(f"Copied {t['pdf_doc']} -> {t['pdf_root']}")
        else:
            print(f"Error: {t['src']} not found!")

    print("All documentation PDFs generated successfully!")

if __name__ == "__main__":
    main()
