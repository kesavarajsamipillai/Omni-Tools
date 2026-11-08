"""
OmniTools Handlers Bridge
Connects the modular tool specifications in omnitools_ui / omnitools_tui
directly to the 100% offline implementations in the `modules/` package.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol


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


def _expand_files(
    paths: Any,
    allowed_extensions: Optional[Iterable[str]] = None,
    recursive: bool = False
) -> List[Path]:
    """
    Expands a collection of file and folder paths into a list of file paths.
    If a path is a directory, it scans for matching files inside it.
    If allowed_extensions is specified, only files with matching extensions are included.
    """
    ext_set = {e.lower().lstrip(".") for e in allowed_extensions} if allowed_extensions else None
    expanded: List[Path] = []
    seen = set()

    for p in paths:
        path_obj = Path(p)
        if path_obj.is_dir():
            iterator = path_obj.rglob("*") if recursive else path_obj.iterdir()
            for child in sorted(iterator):
                if child.is_file() and not child.name.startswith("."):
                    if ext_set is None or child.suffix.lower().lstrip(".") in ext_set:
                        if child not in seen:
                            seen.add(child)
                            expanded.append(child)
        elif path_obj.is_file():
            if ext_set is None or path_obj.suffix.lower().lstrip(".") in ext_set:
                if path_obj not in seen:
                    seen.add(path_obj)
                    expanded.append(path_obj)
    return expanded


def _normalize_fmt(ext_or_fmt: str) -> str:
    """Normalizes format or file extension for comparison (e.g. jpeg==jpg, ppt==pptx, doc==docx)."""
    s = str(ext_or_fmt).lower().lstrip(".")
    if s in ("jpeg", "jpg"):
        return "jpg"
    if s in ("pptx", "ppt"):
        return "pptx"
    if s in ("docx", "doc"):
        return "docx"
    return s


# =========================================================================
# PDF HANDLERS
# =========================================================================

def handle_pdf_unlock(req, reporter: ProgressReporter) -> str:
    import modules.pdf_tools as pdf_tools
    files = _expand_files(req.files, ["pdf"])
    if not files:
        raise RuntimeError("No PDF files found in the selected path(s).")
    pwd = str(req.options.get("password", "") or "")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total = len(files)
    successes = 0

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Unlocking {path.name}...")
        out_path = out_dir / f"{path.stem}_unlocked{path.suffix}"
        res = pdf_tools.remove_pdf_password(str(path), str(out_path), password=pwd)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink()
        successes += 1

    reporter.report(100, "PDFs unlocked successfully.")
    return f"Unlocked {successes} PDF(s) into {out_dir}"


def handle_pdf_protect(req, reporter: ProgressReporter) -> str:
    import modules.pdf_tools as pdf_tools
    pwd = str(req.options.get("password", "") or "")
    if not pwd:
        raise ValueError("Password cannot be empty.")
    files = _expand_files(req.files, ["pdf"])
    if not files:
        raise RuntimeError("No PDF files found in the selected path(s).")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total = len(files)
    successes = 0

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Protecting {path.name}...")
        out_path = out_dir / f"{path.stem}_protected{path.suffix}"
        res = pdf_tools.set_pdf_password(str(path), str(out_path), user_pwd=pwd)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink()
        successes += 1

    reporter.report(100, "PDFs encrypted successfully.")
    return f"Protected {successes} PDF(s) with password."


def handle_pdf_merge(req, reporter: ProgressReporter) -> str:
    import modules.pdf_tools as pdf_tools
    files = _expand_files(req.files, ["pdf"])
    if len(files) < 2:
        raise ValueError(f"Please select at least 2 PDF files to merge (found {len(files)}).")
    out_name = str(req.options.get("output_name") or "merged.pdf").strip()
    if not out_name.lower().endswith(".pdf"):
        out_name += ".pdf"

    out_dir = _get_out_dir(req)
    out_path = out_dir / out_name

    reporter.report(30, f"Merging {len(files)} PDF files...")
    input_strs = [str(f) for f in files]
    res = pdf_tools.merge_pdfs(input_strs, str(out_path))
    if not res["success"]:
        raise RuntimeError(res.get("error", "PDF merge failed"))

    reporter.report(100, "PDFs merged successfully.")
    return f"Merged {len(files)} PDFs into {out_path.name} ({res.get('pages', 0)} pages)."


def handle_pdf_split(req, reporter: ProgressReporter) -> str:
    import modules.pdf_tools as pdf_tools
    files = _expand_files(req.files, ["pdf"])
    if not files:
        raise RuntimeError("No PDF files found in the selected path(s).")
    pages_spec = str(req.options.get("pages") or "").strip()
    out_dir = _get_out_dir(req)
    total = len(files)
    created_total = 0

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Splitting {path.name}...")
        res = pdf_tools.split_pdf(str(path), str(out_dir), page_range_str=pages_spec or None)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        created_total += res.get("count", 0)

    reporter.report(100, "Split complete.")
    return f"Extracted {created_total} page(s) into {out_dir}"


def handle_pdf_to_images(req, reporter: ProgressReporter) -> str:
    import modules.pdf_tools as pdf_tools
    files = _expand_files(req.files, ["pdf"])
    if not files:
        raise RuntimeError("No PDF files found in the selected path(s).")
    fmt = str(req.options.get("format") or "PNG").lower()
    dpi = int(req.options.get("dpi") or 150)
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total_imgs = 0

    for i, path in enumerate(files, 1):
        sub_folder = out_dir / f"{path.stem}_images"
        reporter.report((i - 1) / len(files) * 100, f"Rendering {path.name}...")
        res = pdf_tools.pdf_to_images(str(path), str(sub_folder), fmt=fmt, dpi=dpi)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        total_imgs += res.get("count", 0)
        if not keep_originals and sub_folder.exists():
            path.unlink()

    reporter.report(100, "Rendered all pages to images.")
    return f"Rendered {total_imgs} page image(s) into {out_dir}"


def handle_pdf_images_to_pdf(req, reporter: ProgressReporter) -> str:
    import modules.pdf_tools as pdf_tools
    files = _expand_files(req.files, ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "gif"])
    if not files:
        raise ValueError("Please select one or more image files or a folder containing images.")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    out_path = out_dir / "combined_images.pdf"

    reporter.report(40, f"Combining {len(files)} image(s) to PDF...")
    input_strs = [str(f) for f in files]
    res = pdf_tools.images_to_pdf(input_strs, str(out_path))
    if not res["success"]:
        raise RuntimeError(res.get("error", "Images to PDF conversion failed"))

    if not keep_originals and out_path.exists():
        for f in files:
            if f.resolve() != out_path.resolve():
                f.unlink(missing_ok=True)

    reporter.report(100, "PDF created successfully.")
    return f"Combined {len(files)} image(s) into {out_path.name}"


# =========================================================================
# DOCUMENT HANDLERS
# =========================================================================

def handle_doc_convert(req, reporter: ProgressReporter) -> str:
    import modules.doc_tools as doc_tools
    files = _expand_files(req.files, doc_tools.SUPPORTED_DOCUMENT_FORMATS)
    if not files:
        raise RuntimeError("No supported document files (PDF, DOCX, PPTX, TXT) found in selected path(s).")
    target_fmt = str(req.options.get("format") or "PDF").upper()
    if target_fmt == "PPT":
        target_fmt = "PPTX"
    ext_out = "pptx" if target_fmt == "PPTX" else target_fmt.lower()
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total = len(files)
    count = 0
    skipped = 0

    for i, path in enumerate(files, 1):
        src_fmt = doc_tools.detect_document_type(str(path))
        if _normalize_fmt(src_fmt) == _normalize_fmt(target_fmt):
            reporter.report((i - 1) / total * 100, f"[SKIP] {path.name} is already {target_fmt}. Skipping...")
            skipped += 1
            continue

        reporter.report((i - 1) / total * 100, f"[{i}/{total}] [Auto-detect: {src_fmt} -> {target_fmt}] Converting {path.name}...")
        out_path = out_dir / f"{path.stem}.{ext_out}"
        res = doc_tools.convert_document(str(path), str(out_path), target_format=target_fmt)
        if not res.get("success"):
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if res.get("skipped"):
            skipped += 1
            continue
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Document conversion complete.")
    msg = f"Converted {count} document(s) to {target_fmt}."
    if skipped:
        msg += f" (Skipped {skipped} already in {target_fmt} format)"
    return msg


def handle_doc_pdf_to_docx(req, reporter: ProgressReporter) -> str:
    import modules.doc_tools as doc_tools
    files = _expand_files(req.files, ["pdf", "docx"])
    if not files:
        raise RuntimeError("No PDF files found in the selected path(s).")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total = len(files)
    count = 0

    for i, path in enumerate(files, 1):
        if _normalize_fmt(path.suffix) == "docx":
            reporter.report((i - 1) / total * 100, f"[SKIP] {path.name} is already DOCX. Skipping...")
            continue
        reporter.report((i - 1) / total * 100, f"Converting {path.name} to DOCX...")
        out_path = out_dir / f"{path.stem}.docx"
        res = doc_tools.pdf_to_docx(str(path), str(out_path))
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Converted to DOCX.")
    return f"Converted {count} PDF(s) to editable Word DOCX."


def handle_doc_docx_to_pdf(req, reporter: ProgressReporter) -> str:
    import modules.doc_tools as doc_tools
    files = _expand_files(req.files, ["docx", "doc", "pdf"])
    if not files:
        raise RuntimeError("No Word document (.docx/.doc) files found in the selected path(s).")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total = len(files)
    count = 0

    for i, path in enumerate(files, 1):
        if _normalize_fmt(path.suffix) == "pdf":
            reporter.report((i - 1) / total * 100, f"[SKIP] {path.name} is already PDF. Skipping...")
            continue
        reporter.report((i - 1) / total * 100, f"Converting {path.name} to PDF...")
        out_path = out_dir / f"{path.stem}.pdf"
        res = doc_tools.docx_to_pdf(str(path), str(out_path))
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Converted to PDF.")
    return f"Converted {count} Word DOCX document(s) to PDF."


def handle_doc_pptx_to_pdf(req, reporter: ProgressReporter) -> str:
    import modules.doc_tools as doc_tools
    files = _expand_files(req.files, ["pptx", "ppt", "pdf"])
    if not files:
        raise RuntimeError("No PowerPoint presentation (.pptx/.ppt) files found in the selected path(s).")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total = len(files)
    count = 0

    for i, path in enumerate(files, 1):
        if _normalize_fmt(path.suffix) == "pdf":
            reporter.report((i - 1) / total * 100, f"[SKIP] {path.name} is already PDF. Skipping...")
            continue
        reporter.report((i - 1) / total * 100, f"Converting {path.name} to PDF...")
        out_path = out_dir / f"{path.stem}.pdf"
        res = doc_tools.pptx_to_pdf(str(path), str(out_path))
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Presentation converted to PDF.")
    return f"Converted {count} PowerPoint presentation(s) to PDF."


def handle_doc_pdf_to_pptx(req, reporter: ProgressReporter) -> str:
    import modules.doc_tools as doc_tools
    files = _expand_files(req.files, ["pdf", "pptx", "ppt"])
    if not files:
        raise RuntimeError("No PDF files found in the selected path(s).")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total = len(files)
    count = 0

    for i, path in enumerate(files, 1):
        if _normalize_fmt(path.suffix) == "pptx":
            reporter.report((i - 1) / total * 100, f"[SKIP] {path.name} is already PowerPoint. Skipping...")
            continue
        reporter.report((i - 1) / total * 100, f"Converting {path.name} to PowerPoint PPTX...")
        out_path = out_dir / f"{path.stem}.pptx"
        res = doc_tools.pdf_to_pptx(str(path), str(out_path))
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Converted PDF to PowerPoint PPTX.")
    return f"Converted {count} PDF document(s) to PowerPoint presentation slides."


def handle_doc_txt_to_pdf(req, reporter: ProgressReporter) -> str:
    import modules.doc_tools as doc_tools
    files = _expand_files(req.files, ["txt", "pdf"])
    if not files:
        raise RuntimeError("No TXT files found in the selected path(s).")
    font_size = int(req.options.get("font_size") or 11)
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    count = 0

    for i, path in enumerate(files, 1):
        if _normalize_fmt(path.suffix) == "pdf":
            reporter.report((i - 1) / len(files) * 100, f"[SKIP] {path.name} is already PDF. Skipping...")
            continue
        reporter.report((i - 1) / len(files) * 100, f"Formatting {path.name} as PDF...")
        out_path = out_dir / f"{path.stem}.pdf"
        res = doc_tools.text_to_pdf(str(path), str(out_path), font_size=font_size)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Text formatted as PDF.")
    return f"Converted {count} text file(s) to PDF."


# =========================================================================
# IMAGE HANDLERS
# =========================================================================

def handle_image_convert(req, reporter: ProgressReporter) -> str:
    import modules.image_tools as image_tools
    files = _expand_files(req.files, ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"])
    if not files:
        raise RuntimeError("No supported image files found in the selected path(s).")
    target_fmt = str(req.options.get("format") or "WEBP").lower()
    ext_out = "jpeg" if target_fmt == "jpeg" else ("jpg" if target_fmt == "jpg" else target_fmt)
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    count = 0
    total = len(files)

    for i, path in enumerate(files, 1):
        if _normalize_fmt(path.suffix) == _normalize_fmt(target_fmt):
            reporter.report((i - 1) / total * 100, f"[SKIP] {path.name} is already {target_fmt.upper()}. Skipping...")
            continue
        reporter.report((i - 1) / total * 100, f"Converting {path.name} -> {target_fmt.upper()}...")
        out_path = out_dir / f"{path.stem}.{ext_out}"
        res = image_tools.convert_image(str(path), str(out_path), target_format=target_fmt)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Image conversion complete.")
    return f"Converted {count} image(s) to {target_fmt.upper()} in {out_dir}"


def handle_image_batch_convert(req, reporter: ProgressReporter) -> str:
    import modules.image_tools as image_tools
    files = _expand_files(req.files, ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"])
    if not files:
        raise RuntimeError("No supported image files found in the selected path(s).")
    target_fmt = str(req.options.get("format") or "WEBP").lower()
    ext_out = "jpeg" if target_fmt == "jpeg" else ("jpg" if target_fmt == "jpg" else target_fmt)
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    total_converted = 0
    total = len(files)

    for i, path in enumerate(files, 1):
        if _normalize_fmt(path.suffix) == _normalize_fmt(target_fmt):
            reporter.report((i - 1) / total * 100, f"[SKIP] {path.name} is already {target_fmt.upper()}. Skipping...")
            continue
        reporter.report((i - 1) / total * 100, f"Batch converting {path.name} -> {target_fmt.upper()}...")
        out_file = out_dir / f"{path.stem}.{ext_out}"
        res = image_tools.convert_image(str(path), str(out_file), target_format=target_fmt)
        if res["success"]:
            total_converted += 1
            if not keep_originals and out_file.exists() and out_file.resolve() != path.resolve():
                path.unlink(missing_ok=True)

    reporter.report(100, "Batch conversion complete.")
    return f"Batch converted {total_converted} images to {target_fmt.upper()}."


def handle_image_resize(req, reporter: ProgressReporter) -> str:
    import modules.image_tools as image_tools
    files = _expand_files(req.files, ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"])
    if not files:
        raise RuntimeError("No supported image files found in the selected path(s).")
    w = int(req.options.get("width") or 1200)
    h = int(req.options.get("height") or 800)
    keep_aspect = bool(req.options.get("keep_aspect", True))
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    count = 0
    total = len(files)

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Resizing {path.name}...")
        out_path = out_dir / f"{path.stem}_resized{path.suffix}"
        res = image_tools.resize_image(str(path), str(out_path), width=w, height=h, keep_aspect=keep_aspect)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Resize complete.")
    return f"Resized {count} image(s) to target dimensions."


def handle_image_compress(req, reporter: ProgressReporter) -> str:
    import modules.image_tools as image_tools
    files = _expand_files(req.files, ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"])
    if not files:
        raise RuntimeError("No supported image files found in the selected path(s).")
    quality = int(req.options.get("quality") or 82)
    fmt_choice = str(req.options.get("format") or "Keep original")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    count = 0
    total = len(files)

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Compressing {path.name}...")
        ext = path.suffix
        if fmt_choice == "JPG":
            ext = ".jpg"
        elif fmt_choice == "WEBP":
            ext = ".webp"
        out_path = out_dir / f"{path.stem}_compressed{ext}"
        res = image_tools.compress_image(str(path), str(out_path), quality=quality)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Compression complete.")
    return f"Compressed {count} image(s) at quality={quality}."


def handle_image_transparency(req, reporter: ProgressReporter) -> str:
    import modules.image_tools as image_tools
    files = _expand_files(req.files, ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"])
    if not files:
        raise RuntimeError("No supported image files found in the selected path(s).")
    hex_color = str(req.options.get("background") or "#FFFFFF").lstrip("#")
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        r, g, b = (255, 255, 255)

    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    count = 0
    total = len(files)

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Flattening {path.name} background...")
        out_path = out_dir / f"{path.stem}_flat.jpg"
        res = image_tools.convert_image(str(path), str(out_path), target_format="jpeg", bg_color=(r, g, b))
        if not res["success"]:
            raise RuntimeError(res.get("error"))
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Transparency flattened.")
    return f"Flattened {count} transparent image(s) to clean JPEG with color #{hex_color}."


# =========================================================================
# MEDIA / AUDIO HANDLERS
# =========================================================================

def handle_media_convert(req, reporter: ProgressReporter) -> str:
    import modules.audio_tools as audio_tools
    target_fmt = str(req.options.get("format") or "MP3").lower()
    bitrate_raw = str(req.options.get("bitrate") or "192 kbps")
    bitrate = bitrate_raw.split()[0] + "k"
    keep_tags = bool(req.options.get("keep_tags", True))
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)

    # Expand any folders or file selections into individual media files
    media_exts = audio_tools.SUPPORTED_AUDIO_FORMATS + [v.lstrip(".") for v in audio_tools.SUPPORTED_VIDEO_FORMATS]
    files = _expand_files(req.files, media_exts)
    if not files:
        raise RuntimeError("No supported audio or video files found in the selected path(s).")

    count = 0
    total = len(files)

    for i, path in enumerate(files, 1):
        detection = audio_tools.detect_media_type(str(path))
        detected_fmt = (detection.get("format") or path.suffix.lstrip(".")).upper()
        if _normalize_fmt(detected_fmt) == _normalize_fmt(target_fmt):
            reporter.report((i - 1) / total * 100, f"[SKIP] {path.name} is already {target_fmt.upper()}. Skipping...")
            continue
        tag_info = f" (\"{detection['title']}\")" if detection.get("title") else ""
        cover_info = " + cover art" if detection.get("has_cover") else ""
        reporter.report((i - 1) / total * 100, f"[{i}/{total}] [Auto-detect: {detected_fmt} -> {target_fmt.upper()}] Converting {path.name}{tag_info}{cover_info}...")
        out_path = out_dir / f"{path.stem}.{target_fmt}"
        res = audio_tools.convert_audio(str(path), str(out_path), target_format=target_fmt, bitrate=bitrate, keep_tags=keep_tags)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Audio conversion complete.")
    tags_status = "with song details & cover art preserved" if keep_tags else "transcoded"
    return f"Successfully converted {count} audio track(s) to {target_fmt.upper()} ({bitrate}) {tags_status}."


def handle_media_extract_audio(req, reporter: ProgressReporter) -> str:
    import modules.audio_tools as audio_tools
    files = _expand_files(req.files, [v.lstrip(".") for v in audio_tools.SUPPORTED_VIDEO_FORMATS])
    if not files:
        raise RuntimeError("No video files found in the selected path(s).")
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    count = 0
    total = len(files)

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Extracting audio from {path.name}...")
        out_path = out_dir / f"{path.stem}.mp3"
        res = audio_tools.extract_audio_from_video(str(path), str(out_path), target_format="mp3")
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Audio extraction complete.")
    return f"Extracted MP3 soundtrack from {count} video file(s)."


def handle_media_trim(req, reporter: ProgressReporter) -> str:
    import modules.audio_tools as audio_tools
    files = _expand_files(req.files, audio_tools.SUPPORTED_AUDIO_FORMATS)
    if not files:
        raise RuntimeError("No audio files found in the selected path(s).")
    start_t = str(req.options.get("start") or "00:00:00").strip()
    end_t = str(req.options.get("end") or "00:00:30").strip()
    keep_originals = bool(req.options.get("keep_originals", True))
    out_dir = _get_out_dir(req)
    count = 0
    total = len(files)

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Trimming {path.name}...")
        out_path = out_dir / f"{path.stem}_trimmed{path.suffix}"
        res = audio_tools.trim_audio(str(path), str(out_path), start_time=start_t, duration_or_end=end_t, is_duration=False)
        if not res["success"]:
            raise RuntimeError(f"Failed on {path.name}: {res.get('error')}")
        if not keep_originals and out_path.exists() and out_path.resolve() != path.resolve():
            path.unlink(missing_ok=True)
        count += 1

    reporter.report(100, "Audio trimmed.")
    return f"Trimmed {count} audio file(s) from {start_t} to {end_t}."


# =========================================================================
# FOLDER SORTER HANDLER
# =========================================================================

def handle_sorter_organize(req, reporter: ProgressReporter) -> str:
    import modules.folder_sorter as folder_sorter
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
    import modules.extra_tools as extra_tools
    files = _expand_files(req.files, None)
    if not files:
        raise RuntimeError("No files found in the selected path(s).")
    algo = str(req.options.get("algorithm") or "SHA-256").lower().replace("-", "")
    lines = []
    total = len(files)

    for i, path in enumerate(files, 1):
        reporter.report((i - 1) / total * 100, f"Calculating {algo.upper()} for {path.name}...")
        res = extra_tools.calculate_file_hash(str(path), algorithm=algo)
        if not res["success"]:
            raise RuntimeError(f"{path.name}: {res.get('error')}")
        lines.append(f"{path.name} [{algo.upper()}]: {res['hash']}")

    reporter.report(100, "Hash calculated.")
    return "\n".join(lines)


def handle_utilities_duplicates(req, reporter: ProgressReporter) -> str:
    import modules.extra_tools as extra_tools
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
    import modules.extra_tools as extra_tools
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
    import modules.extra_tools as extra_tools
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
    "documents.convert": handle_doc_convert,
    "documents.pdf_to_docx": handle_doc_pdf_to_docx,
    "documents.docx_to_pdf": handle_doc_docx_to_pdf,
    "documents.pptx_to_pdf": handle_doc_pptx_to_pdf,
    "documents.pdf_to_pptx": handle_doc_pdf_to_pptx,
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
