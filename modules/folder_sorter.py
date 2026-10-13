"""
Smart Folder Sorter & Organizer Module (Completely Offline)
Features:
- Sort files in any target directory by file types:
  - Images (JPG, PNG, JPEG, WEBP, GIF, BMP, TIFF, SVG, ICO) -> Images/JPG, Images/PNG...
  - Documents (PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS, TXT, CSV) -> Documents/PDF, Documents/DOCX...
  - Audio (MP3, WAV, AAC, FLAC, OGG, M4A, OPUS) -> Audio/MP3...
  - Videos (MP4, MKV, AVI, MOV, WMV, FLV, WEBM) -> Videos/MP4...
  - Archives (ZIP, RAR, 7Z, TAR, GZ) -> Archives/ZIP...
  - Code/Data (PY, JSON, XML, HTML, CSS, JS, SQL, CPP, C, JAVA)
  - Executables/Installers (EXE, MSI, BAT, CMD, PS1)
- Supports Dry-Run Preview (shows exact plan before touching files)
- Zero-overwrite collision safety (appends _1, _2 if same file name exists)
- Supports Move or Copy
"""

import os
import shutil
from typing import Dict, List, Optional, Tuple

CATEGORY_MAP = {
    # Images
    "jpg": ("Images", "JPG"),
    "jpeg": ("Images", "JPEG"),
    "png": ("Images", "PNG"),
    "webp": ("Images", "WEBP"),
    "gif": ("Images", "GIF"),
    "bmp": ("Images", "BMP"),
    "tiff": ("Images", "TIFF"),
    "ico": ("Images", "ICO"),
    "svg": ("Images", "SVG"),
    "heic": ("Images", "HEIC"),

    # Documents
    "pdf": ("Documents", "PDF"),
    "docx": ("Documents", "DOCX"),
    "doc": ("Documents", "DOC"),
    "pptx": ("Documents", "PPTX"),
    "ppt": ("Documents", "PPT"),
    "xlsx": ("Documents", "XLSX"),
    "xls": ("Documents", "XLS"),
    "txt": ("Documents", "TXT"),
    "csv": ("Documents", "CSV"),
    "rtf": ("Documents", "RTF"),
    "odt": ("Documents", "ODT"),
    "epub": ("Documents", "EPUB"),

    # Audio
    "mp3": ("Audio", "MP3"),
    "wav": ("Audio", "WAV"),
    "aac": ("Audio", "AAC"),
    "ogg": ("Audio", "OGG"),
    "flac": ("Audio", "FLAC"),
    "m4a": ("Audio", "M4A"),
    "wma": ("Audio", "WMA"),
    "opus": ("Audio", "OPUS"),

    # Video
    "mp4": ("Videos", "MP4"),
    "mkv": ("Videos", "MKV"),
    "avi": ("Videos", "AVI"),
    "mov": ("Videos", "MOV"),
    "wmv": ("Videos", "WMV"),
    "flv": ("Videos", "FLV"),
    "webm": ("Videos", "WEBM"),

    # Archives
    "zip": ("Archives", "ZIP"),
    "rar": ("Archives", "RAR"),
    "7z": ("Archives", "7Z"),
    "tar": ("Archives", "TAR"),
    "gz": ("Archives", "GZ"),

    # Code & Data
    "py": ("Code & Data", "Python"),
    "json": ("Code & Data", "JSON"),
    "xml": ("Code & Data", "XML"),
    "html": ("Code & Data", "HTML"),
    "css": ("Code & Data", "CSS"),
    "js": ("Code & Data", "JavaScript"),
    "sql": ("Code & Data", "SQL"),
    "cpp": ("Code & Data", "CPP"),
    "c": ("Code & Data", "C"),
    "java": ("Code & Data", "Java"),

    # Installers
    "exe": ("Programs & Scripts", "EXE"),
    "msi": ("Programs & Scripts", "MSI"),
    "bat": ("Programs & Scripts", "BAT"),
    "ps1": ("Programs & Scripts", "PS1"),
}

TOP_LEVEL_CATEGORIES = {
    "Images", "Documents", "Audio", "Videos", "Archives", "Code & Data", "Programs & Scripts", "Others"
}


def get_unique_destination_path(dest_path: str) -> str:
    """Ensures no file is overwritten if a file with the same name already exists."""
    if not os.path.exists(dest_path):
        return dest_path

    folder, filename = os.path.split(dest_path)
    base, ext = os.path.splitext(filename)
    counter = 1
    while True:
        candidate = os.path.join(folder, f"{base}_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def analyze_folder(folder_path: str, organize_style: str = "category_and_extension") -> dict:
    """
    Scans folder without modifying anything and returns file counts, sizes,
    and planned destination folders.
    organize_style:
      - 'category_and_extension': e.g. Images/JPG/, Documents/PDF/
      - 'extension_only': e.g. JPG/, PNG/, PDF/
      - 'category_only': e.g. Images/, Documents/
    """
    if not os.path.isdir(folder_path):
        return {"success": False, "error": f"Folder not found: {folder_path}"}

    items = os.listdir(folder_path)
    plan = []
    stats = {}

    for item in items:
        full_p = os.path.join(folder_path, item)
        if not os.path.isfile(full_p):
            continue  # Skip existing folders

        ext = os.path.splitext(item)[1].lower().lstrip(".")
        if not ext:
            cat, subcat = "Others", "No_Extension"
        elif ext in CATEGORY_MAP:
            cat, subcat = CATEGORY_MAP[ext]
        else:
            cat, subcat = "Others", ext.upper()

        if organize_style == "category_and_extension":
            dest_subfolder = os.path.join(cat, subcat)
        elif organize_style == "extension_only":
            dest_subfolder = subcat
        else:  # category_only
            dest_subfolder = cat

        dest_file = os.path.join(folder_path, dest_subfolder, item)
        file_size = os.path.getsize(full_p)

        plan.append({
            "source": full_p,
            "filename": item,
            "category": cat,
            "subcategory": subcat,
            "target_relative": os.path.join(dest_subfolder, item),
            "target_full": dest_file,
            "size": file_size
        })

        key = f"{cat} / {subcat}"
        stats[key] = stats.get(key, 0) + 1

    return {
        "success": True,
        "folder": folder_path,
        "total_files": len(plan),
        "breakdown": stats,
        "plan": plan
    }


def sort_folder(
    folder_path: str,
    action: str = "move",  # 'move' or 'copy'
    organize_style: str = "category_and_extension",
    dry_run: bool = False
) -> dict:
    """
    Sorts files in the given folder into organized subdirectories.
    action: 'move' or 'copy'
    dry_run: if True, returns the plan without moving files
    """
    analysis = analyze_folder(folder_path, organize_style=organize_style)
    if not analysis["success"]:
        return analysis

    if dry_run:
        return analysis

    plan = analysis["plan"]
    processed = []
    failed = []

    for item in plan:
        src = item["source"]
        target = item["target_full"]
        target_dir = os.path.dirname(target)

        try:
            os.makedirs(target_dir, exist_ok=True)
            safe_target = get_unique_destination_path(target)

            if action == "copy":
                shutil.copy2(src, safe_target)
            else:
                shutil.move(src, safe_target)

            processed.append({"source": src, "destination": safe_target})
        except Exception as e:
            failed.append({"source": src, "error": str(e)})

    return {
        "success": True,
        "action": action,
        "organize_style": organize_style,
        "total_processed": len(processed),
        "failed_count": len(failed),
        "processed": processed,
        "failed": failed,
        "breakdown": analysis["breakdown"]
    }
