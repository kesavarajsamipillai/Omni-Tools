"""Tool catalog and request models for the OmniTools UI."""
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
    options: tuple[str, ...] = ()
    placeholder: str = ""


@dataclass(frozen=True)
class CategorySpec:
    key: str
    label: str
    icon: str
    description: str


@dataclass(frozen=True)
class ToolSpec:
    id: str
    category: str
    name: str
    description: str
    input_label: str = "Add files to get started"
    input_mode: Literal["files", "folder", "files_or_folder"] = "files_or_folder"
    fields: tuple[FieldSpec, ...] = ()


@dataclass(frozen=True)
class ToolRequest:
    """Immutable snapshot passed to a registered processing handler."""
    tool_id: str
    files: tuple[Path, ...]
    options: Mapping[str, Any]
    output_dir: Path | None = None


CATEGORIES: tuple[CategorySpec, ...] = (
    CategorySpec("pdf", "PDF Tools", "PDF", "Merge, split, protect, and export PDFs."),
    CategorySpec("documents", "Documents", "DOC", "Convert between common document formats."),
    CategorySpec("images", "Image Studio", "IMG", "Convert and optimize image files."),
    CategorySpec("media", "Audio & Media", "AUD", "Convert audio, extract tracks, and trim clips."),
    CategorySpec("sorter", "Folder Sorter", "SORT", "Organize local folders with a safe preview."),
    CategorySpec("utilities", "Utilities & Security", "UTIL", "Hash, compare, rename, and create QR codes."),
)


def _f(key: str, label: str, kind: FieldKind = "entry", default: Any = "", options: tuple[str, ...] = (), placeholder: str = "") -> FieldSpec:
    return FieldSpec(key, label, kind, default, options, placeholder)


TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec("pdf.unlock", "pdf", "Unlock PDF", "Remove a password from a PDF you are authorized to access.", fields=(_f("password", "Current password", "password"), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("pdf.protect", "pdf", "Protect PDF", "Encrypt a PDF with a password.", fields=(_f("password", "New password", "password"), _f("permissions", "Allow printing", "toggle", True), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("pdf.merge", "pdf", "Merge PDFs", "Combine selected PDFs in the order shown.", fields=(_f("output_name", "Output filename", default="merged.pdf"),)),
    ToolSpec("pdf.split", "pdf", "Split PDF", "Export selected pages or split into individual pages.", fields=(_f("pages", "Pages", placeholder="Example: 1-3, 5, 8-10"),)),
    ToolSpec("pdf.to_images", "pdf", "PDF to images", "Render PDF pages as PNG, JPG, or JPEG.", fields=(_f("format", "Image format", "choice", "PNG", ("PNG", "JPG", "JPEG")), _f("dpi", "Resolution (DPI)", default="150"), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("pdf.images_to_pdf", "pdf", "Images to PDF", "Combine images into a paginated PDF.", fields=(_f("page_size", "Page size", "choice", "A4", ("A4", "Letter", "Fit to image")), _f("orientation", "Orientation", "choice", "Portrait", ("Portrait", "Landscape")), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("documents.convert", "documents", "Convert document", "Auto-detects document format (PDF, DOCX, PPT, TXT) and converts to target type.", fields=(_f("format", "Output format", "choice", "PDF", ("PDF", "DOCX", "PPTX", "TXT")), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("documents.pdf_to_docx", "documents", "PDF to DOCX", "Convert PDF text and layout into an editable document.", fields=(_f("keep_originals", "Keep original files", "toggle", True),)),
    ToolSpec("documents.docx_to_pdf", "documents", "DOCX to PDF", "Export Word documents to PDF.", fields=(_f("keep_originals", "Keep original files", "toggle", True),)),
    ToolSpec("documents.pptx_to_pdf", "documents", "PPT to PDF", "Export PowerPoint presentations (.pptx, .ppt) to PDF.", fields=(_f("keep_originals", "Keep original files", "toggle", True),)),
    ToolSpec("documents.pdf_to_pptx", "documents", "PDF to PPT", "Convert PDF document pages into PowerPoint presentation slides (.pptx).", fields=(_f("keep_originals", "Keep original files", "toggle", True),)),
    ToolSpec("documents.txt_to_pdf", "documents", "TXT to PDF", "Format plain text as a PDF document.", fields=(_f("font_size", "Font size", default="11"), _f("page_size", "Page size", "choice", "A4", ("A4", "Letter")), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("images.convert", "images", "Convert images", "Convert images between PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF, and ICO.", fields=(_f("format", "Output format", "choice", "WEBP", ("PNG", "JPG", "JPEG", "WEBP", "BMP", "GIF", "TIFF", "ICO")), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("images.batch_convert", "images", "Batch folder conversion", "Convert every supported image in a folder.", input_label="Choose one or more folders or files", input_mode="folder", fields=(_f("format", "Output format", "choice", "WEBP", ("PNG", "JPG", "JPEG", "WEBP", "BMP", "GIF", "TIFF", "ICO")), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("images.resize", "images", "Resize images", "Resize one or more images while preserving proportions when selected.", fields=(_f("width", "Width (px)", default="1200"), _f("height", "Height (px)", default="800"), _f("keep_aspect", "Keep aspect ratio", "toggle", True), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("images.compress", "images", "Compress images", "Reduce image file size with a quality setting.", fields=(_f("quality", "Quality (1–100)", default="82"), _f("format", "Output format", "choice", "Keep original", ("Keep original", "JPG", "JPEG", "WEBP")), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("images.transparency", "images", "Transparency tools", "Preserve or flatten image transparency for the selected format.", fields=(_f("background", "Flatten background color", default="#FFFFFF"), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("media.convert", "media", "Convert audio", "Auto-detects any audio/video and converts into desired audio format.", fields=(_f("format", "Output format", "choice", "MP3", ("MP3", "OPUS", "M4A", "FLAC", "WAV", "AAC", "OGG")), _f("bitrate", "Bitrate", "choice", "192 kbps", ("96 kbps", "128 kbps", "192 kbps", "320 kbps")), _f("keep_tags", "Preserve song details & cover art", "toggle", True), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("media.extract_audio", "media", "Extract audio", "Extract an audio track from an MP4, MKV, or AVI video.", fields=(_f("keep_originals", "Keep original files", "toggle", True),)),
    ToolSpec("media.trim", "media", "Trim audio", "Export a segment from an audio file.", fields=(_f("start", "Start time", default="00:00:00"), _f("end", "End time", default="00:00:30"), _f("keep_originals", "Keep original files", "toggle", True))),
    ToolSpec("sorter.organize", "sorter", "Sort a folder", "Preview and organize files into type and extension subfolders.", input_label="Choose a folder to analyze", input_mode="folder", fields=(_f("dry_run", "Preview only (no files moved)", "toggle", True), _f("handle_duplicates", "Add a suffix to name collisions", "toggle", True))),
    ToolSpec("utilities.hash", "utilities", "File hash", "Calculate a cryptographic hash for selected files.", fields=(_f("algorithm", "Algorithm", "choice", "SHA-256", ("SHA-256", "MD5")),)),
    ToolSpec("utilities.duplicates", "utilities", "Find duplicates", "Compare file contents and list duplicate files.", fields=(_f("algorithm", "Comparison", "choice", "SHA-256", ("SHA-256", "MD5")),)),
    ToolSpec("utilities.rename", "utilities", "Batch rename", "Rename files with prefix, suffix, or find-and-replace rules.", fields=(_f("prefix", "Prefix"), _f("suffix", "Suffix"), _f("find", "Find text"), _f("replace", "Replace with"))),
    ToolSpec("utilities.qr", "utilities", "QR code", "Generate a QR code image offline.", fields=(_f("content", "Text or URL", placeholder="Enter text to encode"), _f("size", "Image size (px)", default="512"))),
)

TOOL_BY_ID = {tool.id: tool for tool in TOOLS}
CATEGORY_BY_ID = {category.key: category for category in CATEGORIES}
