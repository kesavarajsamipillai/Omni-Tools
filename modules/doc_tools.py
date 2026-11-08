"""
Document Converter Module (Completely Offline)
Features:
- PDF to DOCX (via pdf2docx)
- DOCX to PDF (via Microsoft Word automation with pure-python ReportLab fallback)
- PPTX / PPT to PDF (via Microsoft PowerPoint automation with pure-python ReportLab fallback)
- PDF to PPTX (via PyMuPDF high-res slide rendering and python-pptx)
- Text to PDF (via ReportLab)
"""

import os
from typing import Optional


def pdf_to_docx(input_pdf: str, output_docx: str, start_page: int = 0, end_page: Optional[int] = None) -> dict:
    """Converts a PDF file to editable Microsoft Word DOCX format offline."""
    if not os.path.exists(input_pdf):
        return {"success": False, "error": f"File not found: {input_pdf}"}

    try:
        from pdf2docx import Converter

        os.makedirs(os.path.dirname(os.path.abspath(output_docx)), exist_ok=True)
        cv = Converter(input_pdf)
        cv.convert(output_docx, start=start_page, end=end_page)
        cv.close()

        return {"success": True, "output": output_docx}
    except Exception as e:
        return {"success": False, "error": str(e)}


def docx_to_pdf(input_docx: str, output_pdf: str) -> dict:
    """
    Converts DOCX to PDF.
    First attempts native MS Word automation (docx2pdf) for perfect layout rendering.
    If MS Word is not installed, seamlessly falls back to pure-Python DOCX parsing with ReportLab!
    """
    if not os.path.exists(input_docx):
        return {"success": False, "error": f"File not found: {input_docx}"}

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf)), exist_ok=True)

    # Method 1: Try docx2pdf (Requires Word installed on Windows)
    try:
        from docx2pdf import convert
        convert(input_docx, output_pdf)
        if os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
            return {"success": True, "output": output_pdf, "engine": "MS Word Native"}
    except Exception:
        pass  # Fall back to pure Python

    # Method 2: Pure Python fallback using python-docx + ReportLab
    try:
        import docx
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors

        doc = docx.Document(input_docx)
        pdf_doc = SimpleDocTemplate(
            output_pdf,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        normal_style = styles["Normal"]
        heading_style = styles["Heading1"]
        h2_style = styles["Heading2"]
        story = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                story.append(Spacer(1, 6))
                continue
            
            # Escape XML entities for ReportLab Paragraph
            safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            if p.style.name.startswith("Heading 1"):
                story.append(Paragraph(safe_text, heading_style))
                story.append(Spacer(1, 10))
            elif p.style.name.startswith("Heading 2"):
                story.append(Paragraph(safe_text, h2_style))
                story.append(Spacer(1, 8))
            else:
                story.append(Paragraph(safe_text, normal_style))
                story.append(Spacer(1, 6))

        for tbl in doc.tables:
            table_data = []
            for row in tbl.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            if table_data:
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
                ]))
                story.append(t)
                story.append(Spacer(1, 12))

        if not story:
            story.append(Paragraph("(Empty Document)", normal_style))

        pdf_doc.build(story)
        return {"success": True, "output": output_pdf, "engine": "Pure Python ReportLab"}
    except Exception as e:
        return {"success": False, "error": f"DOCX to PDF conversion failed: {str(e)}"}


def pptx_to_pdf(input_pptx: str, output_pdf: str) -> dict:
    """
    Converts a PowerPoint presentation (.pptx or .ppt) to PDF.
    First attempts native MS PowerPoint automation (win32com) for 100% layout and font fidelity.
    If MS PowerPoint is not available, uses pure-Python fallback using python-pptx and ReportLab.
    """
    if not os.path.exists(input_pptx):
        return {"success": False, "error": f"File not found: {input_pptx}"}

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf)), exist_ok=True)

    # Method 1: Try native MS PowerPoint automation on Windows
    try:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        ppt_app = None
        try:
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            abs_in = os.path.abspath(input_pptx)
            abs_out = os.path.abspath(output_pdf)
            presentation = ppt_app.Presentations.Open(abs_in, WithWindow=False)
            presentation.SaveAs(abs_out, 32)  # 32 = ppSaveAsPDF
            presentation.Close()
            if os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
                return {"success": True, "output": output_pdf, "engine": "MS PowerPoint Native"}
        finally:
            if ppt_app:
                try:
                    ppt_app.Quit()
                except Exception:
                    pass
            pythoncom.CoUninitialize()
    except Exception:
        pass  # Fall back to pure Python

    # Method 2: Pure Python fallback using python-pptx + ReportLab
    try:
        import io
        import pptx
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader

        prs = pptx.Presentation(input_pptx)
        # Dimensions in points (1 pt = 12700 EMUs)
        slide_w_pt = prs.slide_width / 12700
        slide_h_pt = prs.slide_height / 12700

        c = canvas.Canvas(output_pdf, pagesize=(slide_w_pt, slide_h_pt))

        for slide in prs.slides:
            for shape in slide.shapes:
                # 1. Images
                try:
                    if shape.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE:
                        img_bytes = shape.image.blob
                        img_reader = ImageReader(io.BytesIO(img_bytes))
                        x_pt = shape.left / 12700
                        y_pt = slide_h_pt - (shape.top + shape.height) / 12700
                        w_pt = shape.width / 12700
                        h_pt = shape.height / 12700
                        c.drawImage(img_reader, x_pt, y_pt, width=w_pt, height=h_pt, preserveAspectRatio=True)
                except Exception:
                    pass

                # 2. Text
                if shape.has_text_frame:
                    text_x = shape.left / 12700
                    current_y = slide_h_pt - (shape.top / 12700)
                    for paragraph in shape.text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if not p_text:
                            current_y -= 12
                            continue
                        font_size = 14
                        if paragraph.font and paragraph.font.size:
                            font_size = max(8, paragraph.font.size.pt)
                        font_name = "Helvetica-Bold" if (paragraph.font and paragraph.font.bold) else "Helvetica"
                        c.setFont(font_name, font_size)
                        c.drawString(text_x, current_y - font_size, p_text)
                        current_y -= (font_size + 4)

            c.showPage()

        c.save()
        return {"success": True, "output": output_pdf, "engine": "Pure Python ReportLab", "slides": len(prs.slides)}
    except Exception as e:
        return {"success": False, "error": f"PPT to PDF conversion failed: {str(e)}"}


def pdf_to_pptx(input_pdf: str, output_pptx: str, dpi: int = 150) -> dict:
    """
    Converts a PDF file into a Microsoft PowerPoint presentation (.pptx).
    Renders each page into high-resolution slide graphics with matching aspect ratio.
    """
    if not os.path.exists(input_pdf):
        return {"success": False, "error": f"File not found: {input_pdf}"}

    try:
        import io
        import pymupdf
        import pptx
        from pptx.util import Pt

        os.makedirs(os.path.dirname(os.path.abspath(output_pptx)), exist_ok=True)
        doc = pymupdf.open(input_pdf)
        if len(doc) == 0:
            return {"success": False, "error": "PDF has no pages."}

        prs = pptx.Presentation()
        first_page = doc[0]
        prs.slide_width = Pt(first_page.rect.width)
        prs.slide_height = Pt(first_page.rect.height)
        blank_layout = prs.slide_layouts[6]

        for page in doc:
            slide = prs.slides.add_slide(blank_layout)
            pix = page.get_pixmap(dpi=dpi)
            img_buf = io.BytesIO(pix.tobytes("png"))
            slide.shapes.add_picture(img_buf, 0, 0, width=prs.slide_width, height=prs.slide_height)

        prs.save(output_pptx)
        page_count = len(doc)
        doc.close()
        return {"success": True, "output": output_pptx, "pages": page_count}
    except Exception as e:
        return {"success": False, "error": f"PDF to PPT conversion failed: {str(e)}"}


def text_to_pdf(input_txt: str, output_pdf: str, font_size: int = 10) -> dict:
    """Converts a plain text file into a clean formatted PDF."""
    if not os.path.exists(input_txt):
        return {"success": False, "error": f"File not found: {input_txt}"}

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

        with open(input_txt, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        os.makedirs(os.path.dirname(os.path.abspath(output_pdf)), exist_ok=True)
        pdf = SimpleDocTemplate(
            output_pdf,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        mono_style = ParagraphStyle(
            name="MonoText",
            fontName="Courier",
            fontSize=font_size,
            leading=font_size + 3
        )

        story = []
        for line in lines:
            safe_line = line.rstrip("\r\n").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
            if not safe_line:
                story.append(Spacer(1, font_size))
            else:
                story.append(Paragraph(safe_line, mono_style))

        pdf.build(story)
        return {"success": True, "output": output_pdf, "lines_processed": len(lines)}
    except Exception as e:
        return {"success": False, "error": str(e)}
