"""Declarative categories and tool form schemas."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

FieldKind = Literal["entry", "password", "choice", "toggle"]


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    kind: FieldKind = "entry"
    default: Any = ""
    choices: tuple[str, ...] = ()
    placeholder: str = ""


@dataclass(frozen=True)
class CategorySpec:
    key: str
    label: str
    short_label: str
    description: str


@dataclass(frozen=True)
class ToolSpec:
    id: str
    category: str
    name: str
    description: str
    fields: tuple[FieldSpec, ...] = ()
    input_mode: Literal["files", "folder", "files_or_folder", "none"] = "files"
    needs_input: bool = True


@dataclass(frozen=True)
class ToolRequest:
    tool_id: str
    paths: tuple[Path, ...]
    options: Mapping[str, Any]
    output_dir: Path | None = None


def _field(key: str, label: str, kind: FieldKind = "entry", default: Any = "", choices: tuple[str, ...] = (), placeholder: str = "") -> FieldSpec:
    return FieldSpec(key, label, kind, default, choices, placeholder)


CATEGORIES: tuple[CategorySpec, ...] = (
    CategorySpec("pdf", "PDF Tools", "PDF", "Merge, split, protect, and export PDF files."),
    CategorySpec("documents", "Document Converter", "DOCS", "Convert PDF, DOCX, and TXT documents."),
    CategorySpec("images", "Image Studio", "IMAGES", "Convert, resize, and compress image files."),
    CategorySpec("media", "Audio & Media", "MEDIA", "Convert audio, extract tracks, and trim clips."),
    CategorySpec("sorter", "Smart Folder Sorter", "SORTER", "Preview and organize local directories safely."),
    CategorySpec("utilities", "Utilities", "UTILS", "Hash, find duplicates, rename, and create QR codes."),
)

TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec("pdf.unlock", "pdf", "Unlock PDF", "Remove a password from a PDF you are authorized to access.", (_field("password", "Current password", "password"),)),
    ToolSpec("pdf.protect", "pdf", "Protect PDF", "Encrypt a PDF with a password.", (_field("password", "New password", "password"), _field("allow_print", "Allow printing", "toggle", True))),
    ToolSpec("pdf.merge", "pdf", "Merge PDFs", "Combine selected PDFs in the listed order.", (_field("output_name", "Output filename", default="merged.pdf"),)),
    ToolSpec("pdf.split", "pdf", "Split PDF", "Export selected pages or split into individual pages.", (_field("pages", "Pages to extract", placeholder="Example: 1-3, 5, 8-10"),)),
    ToolSpec("pdf.to_images", "pdf", "PDF to images", "Render PDF pages as PNG or JPG.", (_field("format", "Image format", "choice", "PNG", ("PNG", "JPG")), _field("dpi", "Resolution (DPI)", default="150"))),
    ToolSpec("pdf.images_to_pdf", "pdf", "Images to PDF", "Combine selected images into a PDF.", (_field("page_size", "Page size", "choice", "A4", ("A4", "Letter", "Fit to image")), _field("orientation", "Orientation", "choice", "Portrait", ("Portrait", "Landscape"))), input_mode="files"),
    ToolSpec("documents.pdf_to_docx", "documents", "PDF to DOCX", "Convert a PDF into an editable document."),
    ToolSpec("documents.docx_to_pdf", "documents", "DOCX to PDF", "Export a Word document as PDF."),
    ToolSpec("documents.txt_to_pdf", "documents", "TXT to PDF", "Format plain text as a PDF document.", (_field("font_size", "Font size", default="11"), _field("page_size", "Page size", "choice", "A4", ("A4", "Letter")))),
    ToolSpec("images.convert", "images", "Convert images", "Convert PNG, JPG, WEBP, BMP, GIF, TIFF, and ICO.", (_field("format", "Output format", "choice", "WEBP", ("PNG", "JPG", "WEBP", "BMP", "GIF", "TIFF", "ICO")), _field("keep_originals", "Keep original files", "toggle", True)), input_mode="files_or_folder"),
    ToolSpec("images.batch_convert", "images", "Batch folder conversion", "Convert supported images from a folder.", (_field("format", "Output format", "choice", "WEBP", ("PNG", "JPG", "WEBP", "BMP", "GIF", "TIFF", "ICO")),), input_mode="folder"),
    ToolSpec("images.resize", "images", "Resize images", "Resize images with optional aspect-ratio preservation.", (_field("width", "Width (px)", default="1200"), _field("height", "Height (px)", default="800"), _field("keep_aspect", "Keep aspect ratio", "toggle", True))),
    ToolSpec("images.compress", "images", "Compress images", "Reduce file size with an image quality setting.", (_field("quality", "Quality (1-100)", default="82"), _field("format", "Output format", "choice", "Keep original", ("Keep original", "JPG", "WEBP")))),
    ToolSpec("media.convert", "media", "Convert audio", "Convert between common audio formats.", (_field("format", "Output format", "choice", "MP3", ("MP3", "WAV", "AAC", "FLAC", "OGG", "M4A", "OPUS")), _field("bitrate", "Bitrate", "choice", "192 kbps", ("96 kbps", "128 kbps", "192 kbps", "320 kbps")))),
    ToolSpec("media.extract_audio", "media", "Extract audio track", "Extract audio from MP4, MKV, or AVI video."),
    ToolSpec("media.trim", "media", "Trim audio", "Export a segment from an audio file.", (_field("start", "Start time", default="00:00:00"), _field("end", "End time", default="00:00:30"))),
    ToolSpec("sorter.organize", "sorter", "Sort a folder", "Preview and sort files into type and extension folders.", (_field("dry_run", "Preview only (no files moved)", "toggle", True), _field("handle_collisions", "Prevent name collisions", "toggle", True)), input_mode="folder"),
    ToolSpec("utilities.hash", "utilities", "File hash", "Calculate a cryptographic hash for each selected file.", (_field("algorithm", "Algorithm", "choice", "SHA-256", ("SHA-256", "MD5")),)),
    ToolSpec("utilities.duplicates", "utilities", "Find duplicates", "Compare selected files and report duplicates.", (_field("algorithm", "Comparison", "choice", "SHA-256", ("SHA-256", "MD5")),), input_mode="files_or_folder"),
    ToolSpec("utilities.rename", "utilities", "Batch rename", "Rename files with prefix, suffix, or find-and-replace.", (_field("prefix", "Prefix"), _field("suffix", "Suffix"), _field("find", "Find text"), _field("replace", "Replace with"))),
    ToolSpec("utilities.qr", "utilities", "QR code generator", "Generate a QR code image entirely offline.", (_field("content", "Text or URL", placeholder="Enter text to encode"), _field("size", "Image size (px)", default="512")), input_mode="none", needs_input=False),
)

CATEGORY_BY_ID = {category.key: category for category in CATEGORIES}
TOOL_BY_ID = {tool.id: tool for tool in TOOLS}
TOOLS_BY_CATEGORY = {category.key: tuple(tool for tool in TOOLS if tool.category == category.key) for category in CATEGORIES}
