"""
OmniTools Handlers Bridge
Connects the modular tool specifications in omnitools_ui / omnitools_tui
directly to the 100% offline implementations in the `modules/` package.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, Protocol

import modules.pdf_tools as pdf_tools
import modules.doc_tools as doc_tools
import modules.image_tools as image_tools
import modules.audio_tools as audio_tools
import modules.folder_sorter as folder_sorter
import modules.extra_tools as extra_tools


class ProgressReporter(Protocol):
    def report(self, percent: float, message: str = "") -> None: ...


def _get_out_dir(req, default_dir: Path | None = None) -> Path:
    if getattr(req, "output_dir", None):
        return Path(req.output_dir)
    if default_dir:
        return default_dir
    if req.files:
        f = req.files[0]
        return f if f.is_dir() else f.parent
    return Path.cwd()


# =========================================================================
# PDF HANDLERS
# =========================================================================

def handle_pdf_unlock(req, reporter: ProgressReporter) -> str:
    pwd = str(req.options.get("password", "") or "")
    out_dir = _get_out_dir(req)
    total = len(req.files)
    successes = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / total * 100, f"Unlocking {path.name}...")
        out_path = out_dir / f"{path.stem}_unlocked{path.suffix}"
        res = pdf_tools.remove_pdf_password(str(path), str(out_path), password=pwd)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        successes += 1

    reporter.report(100, "PDFs unlocked successfully.")
    return f"Unlocked {successes} PDF(s) into {out_dir}"


def handle_pdf_protect(req, reporter: ProgressReporter) -> str:
    pwd = str(req.options.get("password", "") or "")
    if not pwd:
        raise ValueError("Password cannot be empty.")
    out_dir = _get_out_dir(req)
    total = len(req.files)
    successes = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / total * 100, f"Protecting {path.name}...")
        out_path = out_dir / f"{path.stem}_protected{path.suffix}"
        res = pdf_tools.set_pdf_password(str(path), str(out_path), user_pwd=pwd)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        successes += 1

    reporter.report(100, "PDFs encrypted successfully.")
    return f"Protected {successes} PDF(s) with password."


def handle_pdf_merge(req, reporter: ProgressReporter) -> str:
    if len(req.files) < 2:
        raise ValueError("Please select at least 2 PDF files to merge.")
    out_name = str(req.options.get("output_name") or "merged.pdf").strip()
    if not out_name.lower().endswith(".pdf"):
        out_name += ".pdf"

    out_dir = _get_out_dir(req)
    out_path = out_dir / out_name

    reporter.report(30, f"Merging {len(req.files)} PDF files...")
    input_strs = [str(f) for f in req.files]
    res = pdf_tools.merge_pdfs(input_strs, str(out_path))
    if not res["success"]:
        raise RuntimeError(res.get("error", "PDF merge failed"))

    reporter.report(100, "PDFs merged successfully.")
    return f"Merged {len(req.files)} PDFs into {out_path.name} ({res.get('pages', 0)} pages)."


def handle_pdf_split(req, reporter: ProgressReporter) -> str:
    pages_spec = str(req.options.get("pages") or "").strip()
    out_dir = _get_out_dir(req)
    total = len(req.files)
    created_total = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / total * 100, f"Splitting {path.name}...")
        res = pdf_tools.split_pdf(str(path), str(out_dir), page_range_str=pages_spec or None)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        created_total += res.get("count", 0)

    reporter.report(100, "Split complete.")
    return f"Extracted {created_total} page(s) into {out_dir}"


def handle_pdf_to_images(req, reporter: ProgressReporter) -> str:
    fmt = str(req.options.get("format") or "PNG").lower()
    dpi = int(req.options.get("dpi") or 150)
    out_dir = _get_out_dir(req)
    total_imgs = 0

    for i, path in enumerate(req.files, 1):
        sub_folder = out_dir / f"{path.stem}_images"
        reporter.report((i - 1) / len(req.files) * 100, f"Rendering {path.name}...")
        res = pdf_tools.pdf_to_images(str(path), str(sub_folder), fmt=fmt, dpi=dpi)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        total_imgs += res.get("count", 0)

    reporter.report(100, "Rendered all pages to images.")
    return f"Rendered {total_imgs} page image(s) into {out_dir}"


def handle_pdf_images_to_pdf(req, reporter: ProgressReporter) -> str:
    if not req.files:
        raise ValueError("Please select one or more image files.")
    out_dir = _get_out_dir(req)
    out_path = out_dir / "combined_images.pdf"

    reporter.report(40, f"Combining {len(req.files)} image(s) to PDF...")
    input_strs = [str(f) for f in req.files]
    res = pdf_tools.images_to_pdf(input_strs, str(out_path))
    if not res["success"]:
        raise RuntimeError(res.get("error", "Images to PDF conversion failed"))

    reporter.report(100, "PDF created successfully.")
    return f"Combined {len(req.files)} image(s) into {out_path.name}"


# =========================================================================
# DOCUMENT HANDLERS
# =========================================================================

def handle_doc_pdf_to_docx(req, reporter: ProgressReporter) -> str:
    out_dir = _get_out_dir(req)
    total = len(req.files)
    count = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / total * 100, f"Converting {path.name} to DOCX...")
        out_path = out_dir / f"{path.stem}.docx"
        res = doc_tools.pdf_to_docx(str(path), str(out_path))
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        count += 1

    reporter.report(100, "Converted to DOCX.")
    return f"Converted {count} PDF(s) to editable Word DOCX."


def handle_doc_docx_to_pdf(req, reporter: ProgressReporter) -> str:
    out_dir = _get_out_dir(req)
    total = len(req.files)
    count = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / total * 100, f"Converting {path.name} to PDF...")
        out_path = out_dir / f"{path.stem}.pdf"
        res = doc_tools.docx_to_pdf(str(path), str(out_path))
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        count += 1

    reporter.report(100, "Converted to PDF.")
    return f"Converted {count} Word DOCX document(s) to PDF."


def handle_doc_txt_to_pdf(req, reporter: ProgressReporter) -> str:
    font_size = int(req.options.get("font_size") or 11)
    out_dir = _get_out_dir(req)
    count = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / len(req.files) * 100, f"Formatting {path.name} as PDF...")
        out_path = out_dir / f"{path.stem}.pdf"
        res = doc_tools.text_to_pdf(str(path), str(out_path), font_size=font_size)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        count += 1

    reporter.report(100, "Text formatted as PDF.")
    return f"Converted {count} text file(s) to PDF."


# =========================================================================
# IMAGE HANDLERS
# =========================================================================

def handle_image_convert(req, reporter: ProgressReporter) -> str:
    target_fmt = str(req.options.get("format") or "WEBP").lower()
    ext_out = "jpg" if target_fmt in ("jpg", "jpeg") else target_fmt
    out_dir = _get_out_dir(req)
    count = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / len(req.files) * 100, f"Converting {path.name} -> {target_fmt.upper()}...")
        out_path = out_dir / f"{path.stem}.{ext_out}"
        res = image_tools.convert_image(str(path), str(out_path), target_format=target_fmt)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        count += 1

    reporter.report(100, "Image conversion complete.")
    return f"Converted {count} image(s) to {target_fmt.upper()} in {out_dir}"


def handle_image_batch_convert(req, reporter: ProgressReporter) -> str:
    target_fmt = str(req.options.get("format") or "WEBP").lower()
    out_dir = _get_out_dir(req)
    total_converted = 0

    for path in req.files:
        if path.is_dir():
            target_sub = out_dir / f"{path.name}_{target_fmt}"
            reporter.report(40, f"Batch converting directory {path.name}...")
            res = image_tools.batch_convert_images(str(path), str(target_sub), target_format=target_fmt)
            if not res["success"]:
                raise RuntimeError(res.get("error"))
            total_converted += len(res.get("converted", []))
        else:
            ext_out = "jpg" if target_fmt in ("jpg", "jpeg") else target_fmt
            res = image_tools.convert_image(str(path), str(out_dir / f"{path.stem}.{ext_out}"), target_format=target_fmt)
            if res["success"]:
                total_converted += 1

    reporter.report(100, "Batch conversion complete.")
    return f"Batch converted {total_converted} images to {target_fmt.upper()}."


def handle_image_resize(req, reporter: ProgressReporter) -> str:
    w = int(req.options.get("width") or 1200)
    h = int(req.options.get("height") or 800)
    keep_aspect = bool(req.options.get("keep_aspect", True))
    out_dir = _get_out_dir(req)
    count = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / len(req.files) * 100, f"Resizing {path.name}...")
        out_path = out_dir / f"{path.stem}_resized{path.suffix}"
        res = image_tools.resize_image(str(path), str(out_path), width=w, height=h, keep_aspect=keep_aspect)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        count += 1

    reporter.report(100, "Resize complete.")
    return f"Resized {count} image(s) to target dimensions."


def handle_image_compress(req, reporter: ProgressReporter) -> str:
    quality = int(req.options.get("quality") or 82)
    fmt_choice = str(req.options.get("format") or "Keep original")
    out_dir = _get_out_dir(req)
    count = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / len(req.files) * 100, f"Compressing {path.name}...")
        ext = path.suffix
        if fmt_choice == "JPG":
            ext = ".jpg"
        elif fmt_choice == "WEBP":
            ext = ".webp"
        out_path = out_dir / f"{path.stem}_compressed{ext}"
        res = image_tools.compress_image(str(path), str(out_path), quality=quality)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        count += 1

    reporter.report(100, "Compression complete.")
    return f"Compressed {count} image(s) at quality={quality}."


def handle_image_transparency(req, reporter: ProgressReporter) -> str:
    hex_color = str(req.options.get("background") or "#FFFFFF").lstrip("#")
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        r, g, b = (255, 255, 255)

    out_dir = _get_out_dir(req)
    count = 0
    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / len(req.files) * 100, f"Flattening {path.name} background...")
        out_path = out_dir / f"{path.stem}_flat.jpg"
        res = image_tools.convert_image(str(path), str(out_path), target_format="jpeg", bg_color=(r, g, b))
        if not res["success"]:
            raise RuntimeError(res.get("error"))
        count += 1

    reporter.report(100, "Transparency flattened.")
    return f"Flattened {count} transparent image(s) to clean JPEG with color #{hex_color}."


# =========================================================================
# MEDIA / AUDIO HANDLERS
# =========================================================================

def handle_media_convert(req, reporter: ProgressReporter) -> str:
    target_fmt = str(req.options.get("format") or "MP3").lower()
    bitrate_raw = str(req.options.get("bitrate") or "192 kbps")
    bitrate = bitrate_raw.split()[0] + "k"
    out_dir = _get_out_dir(req)
    count = 0

    for i, path in enumerate(req.files, 1):
        if path.is_dir():
            res = audio_tools.batch_convert_audio(str(path), str(out_dir), target_format=target_fmt, bitrate=bitrate)
            if not res["success"]:
                raise RuntimeError(res.get("error"))
            count += len(res.get("converted", []))
        else:
            reporter.report((i - 1) / len(req.files) * 100, f"Converting {path.name} -> {target_fmt.upper()}...")
            out_path = out_dir / f"{path.stem}.{target_fmt}"
            res = audio_tools.convert_audio(str(path), str(out_path), target_format=target_fmt, bitrate=bitrate)
            if not res["success"]:
                raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
            count += 1

    reporter.report(100, "Audio conversion complete.")
    return f"Converted {count} audio track(s) to {target_fmt.upper()} ({bitrate})."


def handle_media_extract_audio(req, reporter: ProgressReporter) -> str:
    out_dir = _get_out_dir(req)
    count = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / len(req.files) * 100, f"Extracting audio from {path.name}...")
        out_path = out_dir / f"{path.stem}.mp3"
        res = audio_tools.extract_audio_from_video(str(path), str(out_path), target_format="mp3")
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        count += 1

    reporter.report(100, "Audio extraction complete.")
    return f"Extracted MP3 soundtrack from {count} video file(s)."


def handle_media_trim(req, reporter: ProgressReporter) -> str:
    start_t = str(req.options.get("start") or "00:00:00").strip()
    end_t = str(req.options.get("end") or "00:00:30").strip()
    out_dir = _get_out_dir(req)
    count = 0

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / len(req.files) * 100, f"Trimming {path.name}...")
        out_path = out_dir / f"{path.stem}_trimmed{path.suffix}"
        res = audio_tools.trim_audio(str(path), str(out_path), start_time=start_t, duration_or_end=end_t, is_duration=False)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        count += 1

    reporter.report(100, "Audio trimmed.")
    return f"Trimmed {count} audio file(s) from {start_t} to {end_t}."


# =========================================================================
# FOLDER SORTER HANDLER
# =========================================================================

def handle_sorter_organize(req, reporter: ProgressReporter) -> str:
    dry_run = bool(req.options.get("dry_run", True))
    out_dir = _get_out_dir(req)
    target_folder = req.files[0] if (req.files and req.files[0].is_dir()) else out_dir

    reporter.report(25, f"Analyzing folder contents: {target_folder.name}...")
    res = folder_sorter.sort_folder(str(target_folder), action="move", dry_run=dry_run)
    if not res["success"]:
        raise RuntimeError(res.get("error"))

    reporter.report(100, "Sorting finished.")
    total = res.get("total_files", 0)
    if dry_run:
        bd = res.get("breakdown", {})
        summary = ", ".join(f"{k}: {v}" for k, v in bd.items()) or "None"
        return f"[Dry-Run] Planned {total} files to organize into categories. Breakdown: {summary}"
    else:
        moved = len(res.get("processed", []))
        return f"Successfully organized {moved} file(s) into category subfolders in {target_folder.name}."


# =========================================================================
# UTILITIES HANDLERS
# =========================================================================

def handle_utilities_hash(req, reporter: ProgressReporter) -> str:
    algo = str(req.options.get("algorithm") or "SHA-256").lower().replace("-", "")
    lines = []

    for i, path in enumerate(req.files, 1):
        reporter.report((i - 1) / len(req.files) * 100, f"Calculating {algo.upper()} for {path.name}...")
        res = extra_tools.calculate_file_hash(str(path), algorithm=algo)
        if not res["success"]:
            raise RuntimeError(f"{path.name}: {res.get('error')}")
        lines.append(f"{path.name} [{algo.upper()}]: {res['hash']}")

    reporter.report(100, "Hash calculated.")
    return "\n".join(lines)


def handle_utilities_duplicates(req, reporter: ProgressReporter) -> str:
    target_folder = req.files[0] if (req.files and req.files[0].is_dir()) else _get_out_dir(req)
    reporter.report(30, f"Scanning for duplicates in {target_folder.name}...")
    res = extra_tools.find_duplicate_files(str(target_folder))
    if not res["success"]:
        raise RuntimeError(res.get("error"))

    reporter.report(100, "Scan complete.")
    dups = res.get("duplicates", [])
    if not dups:
        return f"Scanned {res.get('scanned_files', 0)} files in {target_folder.name}: No duplicate files found!"

    summary = f"Found {len(dups)} duplicate group(s) across {res.get('scanned_files', 0)} files:\n"
    for d in dups:
        orig = Path(d["original"]).name
        dup_names = ", ".join(Path(p).name for p in d["duplicates"])
        summary += f"• Original: {orig} == Duplicates: {dup_names}\n"
    return summary


def handle_utilities_rename(req, reporter: ProgressReporter) -> str:
    prefix = str(req.options.get("prefix") or "")
    suffix = str(req.options.get("suffix") or "")
    find_str = str(req.options.get("find") or "")
    replace_str = str(req.options.get("replace") or "")

    target_folder = req.files[0] if (req.files and req.files[0].is_dir()) else _get_out_dir(req)
    reporter.report(40, "Batch renaming files...")
    res = extra_tools.batch_rename_files(
        str(target_folder),
        prefix=prefix,
        suffix=suffix,
        find_str=find_str,
        replace_str=replace_str,
        dry_run=False
    )
    if not res["success"]:
        raise RuntimeError(res.get("error"))

    reporter.report(100, "Rename complete.")
    return f"Renamed {res.get('renamed_count', 0)} file(s) in {target_folder.name}."


def handle_utilities_qr(req, reporter: ProgressReporter) -> str:
    text = str(req.options.get("content") or "").strip()
    if not text:
        # Fall back to using the first file name/path if user provided a file instead of text
        if req.files:
            text = str(req.files[0])
        else:
            raise ValueError("Please enter text or a URL in the Content field to generate a QR code.")

    out_dir = _get_out_dir(req)
    out_path = out_dir / "omnitools_qr.png"

    reporter.report(50, "Generating QR code...")
    res = extra_tools.generate_qr(text, str(out_path))
    if not res["success"]:
        raise RuntimeError(res.get("error"))

    reporter.report(100, "QR code generated.")
    return f"QR code successfully created at: {out_path}"


# =========================================================================
# HANDLERS REGISTRY
# =========================================================================

HANDLERS: Dict[str, Callable] = {
    # PDF
    "pdf.unlock": handle_pdf_unlock,
    "pdf.protect": handle_pdf_protect,
    "pdf.merge": handle_pdf_merge,
    "pdf.split": handle_pdf_split,
    "pdf.to_images": handle_pdf_to_images,
    "pdf.images_to_pdf": handle_pdf_images_to_pdf,

    # Documents
    "documents.pdf_to_docx": handle_doc_pdf_to_docx,
    "documents.docx_to_pdf": handle_doc_docx_to_pdf,
    "documents.txt_to_pdf": handle_doc_txt_to_pdf,

    # Images
    "images.convert": handle_image_convert,
    "images.batch_convert": handle_image_batch_convert,
    "images.resize": handle_image_resize,
    "images.compress": handle_image_compress,
    "images.transparency": handle_image_transparency,

    # Media / Audio
    "media.convert": handle_media_convert,
    "media.extract_audio": handle_media_extract_audio,
    "media.trim": handle_media_trim,

    # Folder Sorter
    "sorter.organize": handle_sorter_organize,

    # Utilities
    "utilities.hash": handle_utilities_hash,
    "utilities.duplicates": handle_utilities_duplicates,
    "utilities.rename": handle_utilities_rename,
    "utilities.qr": handle_utilities_qr,
}
