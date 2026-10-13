"""
PDF Tools Module (Completely Offline)
Features:
- Remove PDF Password (Decryption)
- Set PDF Password (Encryption)
- Merge Multiple PDFs
- Split PDF / Extract Pages
- Convert PDF Pages to Images
- Convert Images to PDF
"""

import os
from typing import List, Optional
from pypdf import PdfReader, PdfWriter
import pymupdf  # Modern PyMuPDF


def remove_pdf_password(input_path: str, output_path: str, password: str = "") -> dict:
    """Removes the known password from an encrypted PDF and saves an unprotected copy."""
    if not os.path.exists(input_path):
        return {"success": False, "error": f"File not found: {input_path}"}

    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            decrypt_res = reader.decrypt(password)
            if decrypt_res == 0:
                return {"success": False, "error": "Incorrect password. Failed to decrypt PDF."}

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)

        return {"success": True, "output": output_path, "pages": len(writer.pages)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_pdf_password(input_path: str, output_path: str, user_pwd: str, owner_pwd: Optional[str] = None) -> dict:
    """Protects a PDF file with a password."""
    if not os.path.exists(input_path):
        return {"success": False, "error": f"File not found: {input_path}"}
    if not user_pwd:
        return {"success": False, "error": "Password cannot be empty."}

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(user_password=user_pwd, owner_password=owner_pwd or user_pwd)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)

        return {"success": True, "output": output_path, "pages": len(writer.pages)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def merge_pdfs(pdf_paths: List[str], output_path: str) -> dict:
    """Merges multiple PDF files in order into a single output PDF."""
    if not pdf_paths:
        return {"success": False, "error": "No PDF files provided to merge."}

    writer = PdfWriter()
    total_pages = 0

    try:
        for p in pdf_paths:
            if not os.path.exists(p):
                return {"success": False, "error": f"File not found: {p}"}
            reader = PdfReader(p)
            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)

        return {"success": True, "output": output_path, "total_pages": total_pages, "files_merged": len(pdf_paths)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def split_pdf(input_path: str, output_folder: str, page_ranges: Optional[str] = None) -> dict:
    """
    Splits a PDF.
    If page_ranges is None or empty, splits into individual page PDFs.
    page_ranges format can be: '1-3, 5, 8-10' (1-indexed).
    """
    if not os.path.exists(input_path):
        return {"success": False, "error": f"File not found: {input_path}"}

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        os.makedirs(output_folder, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        created_files = []

        if not page_ranges:
            # Extract each single page
            for idx, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                out_file = os.path.join(output_folder, f"{base_name}_page_{idx:03d}.pdf")
                with open(out_file, "wb") as f:
                    writer.write(f)
                created_files.append(out_file)
        else:
            # Parse page ranges (e.g. "1-3, 5")
            parts = [p.strip() for p in page_ranges.split(",") if p.strip()]
            for part in parts:
                writer = PdfWriter()
                if "-" in part:
                    s_str, e_str = part.split("-", 1)
                    start = max(1, int(s_str.strip()))
                    end = min(total_pages, int(e_str.strip()))
                    out_name = f"{base_name}_pages_{start}-{end}.pdf"
                    for p_num in range(start, end + 1):
                        writer.add_page(reader.pages[p_num - 1])
                else:
                    p_num = int(part)
                    if 1 <= p_num <= total_pages:
                        writer.add_page(reader.pages[p_num - 1])
                        out_name = f"{base_name}_page_{p_num:03d}.pdf"
                    else:
                        continue

                out_file = os.path.join(output_folder, out_name)
                with open(out_file, "wb") as f:
                    writer.write(f)
                created_files.append(out_file)

        return {"success": True, "created_files": created_files, "count": len(created_files)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def pdf_to_images(input_path: str, output_folder: str, fmt: str = "png", dpi: int = 200) -> dict:
    """Converts each page of a PDF into high-resolution images."""
    if not os.path.exists(input_path):
        return {"success": False, "error": f"File not found: {input_path}"}

    fmt = fmt.lower().lstrip(".")
    try:
        doc = pymupdf.open(input_path)
        os.makedirs(output_folder, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        created_files = []

        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat)
            out_file = os.path.join(output_folder, f"{base_name}_page_{page_num + 1:03d}.{fmt}")
            pix.save(out_file)
            created_files.append(out_file)

        doc.close()
        return {"success": True, "created_files": created_files, "count": len(created_files)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def images_to_pdf(image_paths: List[str], output_path: str) -> dict:
    """Converts a list of images into a single combined PDF."""
    if not image_paths:
        return {"success": False, "error": "No images provided."}

    from PIL import Image
    try:
        opened_images = []
        for p in image_paths:
            if not os.path.exists(p):
                return {"success": False, "error": f"Image file not found: {p}"}
            img = Image.open(p)
            if img.mode != "RGB":
                img = img.convert("RGB")
            opened_images.append(img)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if opened_images:
            first = opened_images[0]
            rest = opened_images[1:]
            first.save(output_path, "PDF", resolution=100.0, save_all=True, append_images=rest)

        return {"success": True, "output": output_path, "images_count": len(image_paths)}
    except Exception as e:
        return {"success": False, "error": str(e)}
