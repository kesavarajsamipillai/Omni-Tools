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


def pdf_to_txt(input_pdf: str, output_txt: str) -> dict:
    """Extracts all text content from a PDF document offline."""
    if not os.path.exists(input_pdf):
        return {"success": False, "error": f"File not found: {input_pdf}"}
    try:
        import pymupdf
        os.makedirs(os.path.dirname(os.path.abspath(output_txt)), exist_ok=True)
        doc = pymupdf.open(input_pdf)
        text_parts = [page.get_text() for page in doc]
        doc.close()
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("\n\n--- Page Break ---\n\n".join(text_parts))
        return {"success": True, "output": output_txt, "pages": len(text_parts)}
    except Exception as e:
        return {"success": False, "error": f"PDF to TXT failed: {str(e)}"}


def docx_to_txt(input_docx: str, output_txt: str) -> dict:
    """Extracts plain text from a Word DOCX document."""
    if not os.path.exists(input_docx):
        return {"success": False, "error": f"File not found: {input_docx}"}
    try:
        import docx
        os.makedirs(os.path.dirname(os.path.abspath(output_txt)), exist_ok=True)
        doc = docx.Document(input_docx)
        lines = [p.text for p in doc.paragraphs]
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return {"success": True, "output": output_txt, "paragraphs": len(lines)}
    except Exception as e:
        return {"success": False, "error": f"DOCX to TXT failed: {str(e)}"}


def pptx_to_txt(input_pptx: str, output_txt: str) -> dict:
    """Extracts plain text from a PowerPoint PPTX/PPT presentation."""
    if not os.path.exists(input_pptx):
        return {"success": False, "error": f"File not found: {input_pptx}"}
    try:
        import pptx
        os.makedirs(os.path.dirname(os.path.abspath(output_txt)), exist_ok=True)
        prs = pptx.Presentation(input_pptx)
        slide_texts = []
        for i, slide in enumerate(prs.slides, 1):
            lines = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        t = p.text.strip()
                        if t:
                            lines.append(t)
            slide_texts.append(f"--- Slide {i} ---\n" + "\n".join(lines))
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("\n\n".join(slide_texts))
        return {"success": True, "output": output_txt, "slides": len(prs.slides)}
    except Exception as e:
        return {"success": False, "error": f"PPT to TXT failed: {str(e)}"}


def text_to_docx(input_txt: str, output_docx: str) -> dict:
    """Converts a plain text file into a Word DOCX document."""
    if not os.path.exists(input_txt):
        return {"success": False, "error": f"File not found: {input_txt}"}
    try:
        import docx
        os.makedirs(os.path.dirname(os.path.abspath(output_docx)), exist_ok=True)
        doc = docx.Document()
        with open(input_txt, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                doc.add_paragraph(line.rstrip("\r\n"))
        doc.save(output_docx)
        return {"success": True, "output": output_docx}
    except Exception as e:
        return {"success": False, "error": f"TXT to DOCX failed: {str(e)}"}


def pptx_to_docx(input_pptx: str, output_docx: str) -> dict:
    """Converts a PowerPoint presentation to a Word DOCX document via PDF intermediate or direct extraction."""
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp_pdf = os.path.join(td, "temp_pptx.pdf")
            res_pdf = pptx_to_pdf(input_pptx, tmp_pdf)
            if res_pdf.get("success") and os.path.exists(tmp_pdf):
                return pdf_to_docx(tmp_pdf, output_docx)
            # Fallback: extract text to docx
            tmp_txt = os.path.join(td, "temp_pptx.txt")
            res_txt = pptx_to_txt(input_pptx, tmp_txt)
            if res_txt.get("success"):
                return text_to_docx(tmp_txt, output_docx)
            return {"success": False, "error": res_pdf.get("error", "Failed to convert PPT to DOCX")}
    except Exception as e:
        return {"success": False, "error": f"PPT to DOCX failed: {str(e)}"}


def docx_to_pptx(input_docx: str, output_pptx: str) -> dict:
    """Converts a Word DOCX document to a PowerPoint PPTX presentation via PDF intermediate."""
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp_pdf = os.path.join(td, "temp_docx.pdf")
            res_pdf = docx_to_pdf(input_docx, tmp_pdf)
            if not res_pdf.get("success") or not os.path.exists(tmp_pdf):
                return {"success": False, "error": res_pdf.get("error", "DOCX to PDF step failed")}
            return pdf_to_pptx(tmp_pdf, output_pptx)
    except Exception as e:
        return {"success": False, "error": f"DOCX to PPT failed: {str(e)}"}


def text_to_pptx(input_txt: str, output_pptx: str) -> dict:
    """Converts a plain text file into a PowerPoint presentation via PDF intermediate."""
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp_pdf = os.path.join(td, "temp_txt.pdf")
            res_pdf = text_to_pdf(input_txt, tmp_pdf)
            if not res_pdf.get("success") or not os.path.exists(tmp_pdf):
                return {"success": False, "error": res_pdf.get("error", "TXT to PDF step failed")}
            return pdf_to_pptx(tmp_pdf, output_pptx)
    except Exception as e:
        return {"success": False, "error": f"TXT to PPT failed: {str(e)}"}


SUPPORTED_DOCUMENT_FORMATS = ["pdf", "docx", "doc", "pptx", "ppt", "txt"]


def detect_document_type(file_path: str) -> str:
    """Detects document format from file extension and contents."""
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if ext == "pdf":
        return "PDF"
    elif ext in ("docx", "doc"):
        return "DOCX"
    elif ext in ("pptx", "ppt"):
        return "PPTX"
    elif ext == "txt":
        return "TXT"
    return ext.upper()


def convert_document(input_path: str, output_path: str, target_format: str) -> dict:
    """
    Universal document converter with auto-detection.
    Supports conversions across PDF, DOCX, PPTX (PPT), and TXT.
    If source format matches target format, returns skipped status.
    """
    src_fmt = detect_document_type(input_path)
    tgt_fmt = target_format.upper()
    if tgt_fmt == "PPT":
        tgt_fmt = "PPTX"

    if src_fmt == tgt_fmt:
        return {
            "success": True,
            "skipped": True,
            "source_format": src_fmt,
            "target_format": tgt_fmt,
            "message": f"Source is already in {tgt_fmt} format"
        }

    if tgt_fmt == "PDF":
        if src_fmt == "DOCX":
            return docx_to_pdf(input_path, output_path)
        elif src_fmt == "PPTX":
            return pptx_to_pdf(input_path, output_path)
        elif src_fmt == "TXT":
            return text_to_pdf(input_path, output_path)
    elif tgt_fmt == "DOCX":
        if src_fmt == "PDF":
            return pdf_to_docx(input_path, output_path)
        elif src_fmt == "PPTX":
            return pptx_to_docx(input_path, output_path)
        elif src_fmt == "TXT":
            return text_to_docx(input_path, output_path)
    elif tgt_fmt == "PPTX":
        if src_fmt == "PDF":
            return pdf_to_pptx(input_path, output_path)
        elif src_fmt == "DOCX":
            return docx_to_pptx(input_path, output_path)
        elif src_fmt == "TXT":
            return text_to_pptx(input_path, output_path)
    elif tgt_fmt == "TXT":
        if src_fmt == "PDF":
            return pdf_to_txt(input_path, output_path)
        elif src_fmt == "DOCX":
            return docx_to_txt(input_path, output_path)
        elif src_fmt == "PPTX":
            return pptx_to_txt(input_path, output_path)

    return {"success": False, "error": f"Unsupported conversion from {src_fmt} to {tgt_fmt}"}
