"""Native Windows File & Folder Explorer Bridge.

Provides seamless, non-blocking native Windows popup dialogs for selecting
files and folders directly from the terminal.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional


def open_system_picker(
    mode: str = "files",
    title: str = "",
    initial_dir: Optional[Path] = None,
) -> List[str]:
    """Open default native Windows File Explorer dialog for files or folders."""
    import tkinter as tk
    from tkinter import filedialog

    init_str = str(initial_dir) if initial_dir and initial_dir.exists() else str(Path.cwd())
    try:
        root = tk.Tk()
        root.withdraw()
        # Bring to front of Windows Terminal / PowerShell
        root.attributes("-topmost", True)
        root.update()
        if mode == "folder":
            dialog_title = title or "OmniTools - Select Folder"
            folder = filedialog.askdirectory(title=dialog_title, initialdir=init_str, parent=root)
            root.destroy()
            return [folder] if folder else []
        else:
            dialog_title = title or "OmniTools - Select Files"
            files = filedialog.askopenfilenames(title=dialog_title, initialdir=init_str, parent=root)
            root.destroy()
            return list(files) if files else []
    except Exception:
        return []
