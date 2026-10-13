"""
Extra Offline Utilities Module
Features:
- File Hash Generator (MD5, SHA-1, SHA-256)
- Offline Duplicate File Finder (finds identical files by hash)
- Batch File Renamer (prefix, suffix, replace, sequential index)
- Offline QR Code Generator
"""

import os
import hashlib
from typing import Dict, List, Optional
import qrcode
from PIL import Image


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> dict:
    """Calculates cryptographic hash of a file offline."""
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    algo = algorithm.lower()
    hasher = getattr(hashlib, algo, None)
    if not hasher:
        return {"success": False, "error": f"Unsupported hash algorithm: {algorithm}"}

    h = hasher()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return {
            "success": True,
            "file": file_path,
            "algorithm": algo,
            "hash": h.hexdigest(),
            "size_bytes": os.path.getsize(file_path)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def find_duplicate_files(folder_path: str, min_size_bytes: int = 1) -> dict:
    """
    Finds duplicate files in a folder based on exact binary SHA-256 hashes.
    Fast two-step check: sizes first, then hashes only for candidates with identical size.
    """
    if not os.path.isdir(folder_path):
        return {"success": False, "error": f"Folder not found: {folder_path}"}

    size_map: Dict[int, List[str]] = {}
    for root, _, files in os.walk(folder_path):
        for f in files:
            full_p = os.path.join(root, f)
            try:
                sz = os.path.getsize(full_p)
                if sz >= min_size_bytes:
                    size_map.setdefault(sz, []).append(full_p)
            except Exception:
                continue

    # Only inspect sizes that have >= 2 files
    candidates = [paths for paths in size_map.values() if len(paths) > 1]
    hash_map: Dict[str, List[str]] = {}

    for path_group in candidates:
        for p in path_group:
            h_res = calculate_file_hash(p, "sha256")
            if h_res["success"]:
                hash_map.setdefault(h_res["hash"], []).append(p)

    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}

    total_wasted_bytes = 0
    dup_groups = []
    for h, paths in duplicates.items():
        sz = os.path.getsize(paths[0])
        wasted = sz * (len(paths) - 1)
        total_wasted_bytes += wasted
        dup_groups.append({
            "hash": h,
            "size_per_file": sz,
            "count": len(paths),
            "files": paths
        })

    return {
        "success": True,
        "folder": folder_path,
        "duplicate_groups_count": len(dup_groups),
        "total_wasted_bytes": total_wasted_bytes,
        "groups": dup_groups
    }


def batch_rename_files(
    folder_path: str,
    prefix: str = "",
    suffix: str = "",
    find_str: str = "",
    replace_str: str = "",
    add_numbering: bool = False,
    start_num: int = 1,
    dry_run: bool = False
) -> dict:
    """Batch renames files in a directory with pattern matching and sequential numbering."""
    if not os.path.isdir(folder_path):
        return {"success": False, "error": f"Folder not found: {folder_path}"}

    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    files.sort()

    plan = []
    num = start_num

    for f in files:
        base, ext = os.path.splitext(f)
        new_base = base

        if find_str:
            new_base = new_base.replace(find_str, replace_str)

        if prefix:
            new_base = f"{prefix}{new_base}"

        if suffix:
            new_base = f"{new_base}{suffix}"

        if add_numbering:
            new_base = f"{new_base}_{num:03d}"
            num += 1

        new_filename = f"{new_base}{ext}"
        old_path = os.path.join(folder_path, f)
        new_path = os.path.join(folder_path, new_filename)

        if old_path != new_path:
            plan.append({"old": old_path, "new": new_path, "old_name": f, "new_name": new_filename})

    if dry_run:
        return {"success": True, "dry_run": True, "plan": plan, "total_to_rename": len(plan)}

    renamed = []
    failed = []

    for item in plan:
        try:
            if not os.path.exists(item["new"]):
                os.rename(item["old"], item["new"])
                renamed.append(item)
            else:
                failed.append({"item": item, "error": "Destination file already exists."})
        except Exception as e:
            failed.append({"item": item, "error": str(e)})

    return {
        "success": True,
        "dry_run": False,
        "renamed_count": len(renamed),
        "failed_count": len(failed),
        "renamed": renamed,
        "failed": failed
    }


def generate_qr(text_or_url: str, output_path: str, scale: int = 10, border: int = 4) -> dict:
    """Generates a high-resolution QR code image offline."""
    if not text_or_url:
        return {"success": False, "error": "Content cannot be empty."}

    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=scale,
            border=border,
        )
        qr.add_data(text_or_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img.save(output_path)

        return {"success": True, "output": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}
