"""Composable CustomTkinter shell for OmniTools.

Processing stays in caller-provided handlers. Handlers run in worker threads and
receive a ToolRequest plus a ProgressReporter; they should not touch Tk widgets.
"""
from __future__ import annotations

import queue
import shutil
import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable, Mapping

import customtkinter as ctk

from .catalog import CATEGORIES, CATEGORY_BY_ID, TOOLS, FieldSpec, ToolRequest, ToolSpec
from .theme import COLORS, FONT

Handler = Callable[[ToolRequest, "ProgressReporter"], Any]


class ProgressReporter:
    """Thread-safe progress callback supplied to a backend handler."""
    def __init__(self, callback: Callable[[float, str], None]):
        self._callback = callback

    def report(self, percent: float, message: str = "") -> None:
        self._callback(max(0.0, min(100.0, float(percent))), str(message))

    update = report


@dataclass
class _FieldControl:
    spec: FieldSpec
    variable: Any


class OmniToolsApp(ctk.CTkFrame):
    """Embed the OmniTools UI in a CTk or TkinterDnD root window."""
    def __init__(self, master: Any, handlers: Mapping[str, Handler] | None = None, worker_count: int = 2):
        super().__init__(master, fg_color=COLORS["background"], corner_radius=0)
        self.master = master
        self.handlers = dict(handlers or {})
        self.executor = ThreadPoolExecutor(max_workers=max(1, worker_count), thread_name_prefix="omnitools")
        self.events: queue.Queue[tuple[Any, ...]] = queue.Queue()
        self._closing = False
        self._future: Future[Any] | None = None
        self._active_category = CATEGORIES[0].key
        self._active_tool: ToolSpec | None = None
        self._files: list[Path] = []
        self._field_controls: dict[str, _FieldControl] = {}
        self._output_dir: Path | None = None
        self.search_var = tk.StringVar(master=self, value="")
        self.search_var.trace_add("write", self._on_search_changed)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._build_sidebar()
        self._build_content()
        self._build_logs()
        self._build_footer()
        self._render_category()
        self._render_navigation()
        self._log("OmniTools UI ready. Connect local handlers to enable processing.")
        self.after(100, self._poll_events)
        self.master.protocol("WM_DELETE_WINDOW", self.close)

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=248, fg_color=COLORS["sidebar"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 22))
        mark = ctk.CTkLabel(brand, text="O", width=34, height=34, corner_radius=10, fg_color=COLORS["accent_soft"], text_color=COLORS["accent"], font=(FONT, 17, "bold"))
        mark.pack(side="left")
        titlebox = ctk.CTkFrame(brand, fg_color="transparent")
        titlebox.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(titlebox, text="OmniTools", text_color=COLORS["text"], font=(FONT, 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(titlebox, text="LOCAL FILE WORKSPACE", text_color=COLORS["subtle"], font=(FONT, 9, "bold")).pack(anchor="w", pady=(2, 0))
        self.search_entry = ctk.CTkEntry(self.sidebar, textvariable=self.search_var, placeholder_text="⌕   Search tools", height=38, corner_radius=9, fg_color=COLORS["surface"], border_color=COLORS["border"], text_color=COLORS["text"], placeholder_text_color=COLORS["subtle"], font=(FONT, 12))
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 20))
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.grid(row=2, column=0, sticky="new", padx=10)
        self.nav_frame.grid_columnconfigure(0, weight=1)
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.sidebar.grid_rowconfigure(2, weight=1)
        self.ffmpeg_label = ctk.CTkLabel(self.sidebar, text="", justify="left", text_color=COLORS["muted"], font=(FONT, 10), wraplength=210)
        self.ffmpeg_label.grid(row=3, column=0, sticky="ew", padx=18, pady=(8, 18))
        self._refresh_ffmpeg_status()

    def _build_content(self) -> None:
        self.content = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=(0, 24), pady=(20, 10))
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _build_logs(self) -> None:
        self.log_drawer = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        self.log_drawer.grid(row=1, column=1, sticky="ew", padx=(18, 24), pady=(0, 10))
        self.log_drawer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.log_drawer, text="Activity log", text_color=COLORS["text"], font=(FONT, 11, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(9, 4))
        self.log_text = ctk.CTkTextbox(self.log_drawer, height=112, fg_color=COLORS["background"], text_color=COLORS["muted"], border_width=0, font=("Consolas", 10), wrap="word")
        self.log_text.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")
        self.log_drawer.grid_remove()

    def _build_footer(self) -> None:
        self.footer = ctk.CTkFrame(self, height=54, fg_color=COLORS["sidebar"], corner_radius=0)
        self.footer.grid(row=2, column=1, sticky="ew", padx=(0, 0))
        self.footer.grid_propagate(False)
        self.footer.grid_columnconfigure(2, weight=1)
        self.status_dot = ctk.CTkLabel(self.footer, text="●", text_color=COLORS["muted"], font=(FONT, 12))
        self.status_dot.grid(row=0, column=0, padx=(18, 7), pady=13)
        self.status_text = ctk.CTkLabel(self.footer, text="IDLE", text_color=COLORS["muted"], font=(FONT, 10, "bold"))
        self.status_text.grid(row=0, column=1, sticky="w")
        self.progress = ctk.CTkProgressBar(self.footer, height=6, corner_radius=4, fg_color=COLORS["border"], progress_color=COLORS["accent"])
        self.progress.set(0)
        self.progress.grid(row=0, column=2, sticky="ew", padx=(20, 12), pady=20)
        self.progress_label = ctk.CTkLabel(self.footer, text="", width=130, anchor="w", text_color=COLORS["subtle"], font=(FONT, 10))
        self.progress_label.grid(row=0, column=3, sticky="w", padx=(0, 10))
        self.log_toggle = ctk.CTkButton(self.footer, text="Show log  ˄", width=96, height=28, corner_radius=7, fg_color="transparent", hover_color=COLORS["surface_hover"], text_color=COLORS["muted"], font=(FONT, 10), command=self._toggle_logs)
        self.log_toggle.grid(row=0, column=4, padx=(0, 16))

    def _refresh_ffmpeg_status(self) -> None:
        present = shutil.which("ffmpeg") is not None
        if present:
            text, color = "●  FFmpeg available", COLORS["success"]
        else:
            text, color = "○  FFmpeg not detected\nAudio/video handlers may require it.", COLORS["warning"]
        self.ffmpeg_label.configure(text=text, text_color=color)

    def _on_search_changed(self, *_: Any) -> None:
        self._render_navigation()
        self._render_category()

    def _matching_tools(self, category: str | None = None) -> list[ToolSpec]:
        query = self.search_var.get().strip().casefold()
        return [tool for tool in TOOLS if (category is None or tool.category == category) and (not query or query in tool.name.casefold() or query in tool.description.casefold() or query in tool.category.casefold())]

    def _render_navigation(self) -> None:
        for child in self.nav_frame.winfo_children():
            child.destroy()
        query = self.search_var.get().strip()
        for category in CATEGORIES:
            if query and not self._matching_tools(category.key):
                continue
            active = self._active_category == category.key and self._active_tool is None
            button = ctk.CTkButton(self.nav_frame, text=f"{category.icon:>4}   {category.label}", anchor="w", height=40, corner_radius=8, fg_color=COLORS["surface_active"] if active else "transparent", hover_color=COLORS["surface_hover"], text_color=COLORS["text"] if active else COLORS["muted"], font=(FONT, 12, "bold" if active else "normal"), command=lambda key=category.key: self.select_category(key))
            button.pack(fill="x", pady=2)
            self.nav_buttons[category.key] = button

    def select_category(self, key: str) -> None:
        self._active_category = key
        self._active_tool = None
        self._files.clear()
        self._render_navigation()
        self._render_category()

    def _clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def _render_category(self) -> None:
        self._active_tool = None
        self._clear_content()
        category = CATEGORY_BY_ID[self._active_category]
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(page, text=category.label, text_color=COLORS["text"], font=(FONT, 26, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(page, text=category.description, text_color=COLORS["muted"], font=(FONT, 12)).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 20))
        tools = self._matching_tools(self._active_category)
        if not tools:
            ctk.CTkLabel(page, text="No matching tools. Try a different search.", text_color=COLORS["muted"], font=(FONT, 13)).grid(row=2, column=0, sticky="nw", padx=10, pady=20)
            return
        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["muted"])
        scroll.grid(row=2, column=0, sticky="nsew", padx=2, pady=(0, 8))
        page.grid_rowconfigure(2, weight=1)
        columns = 3
        for col in range(columns):
            scroll.grid_columnconfigure(col, weight=1, uniform="toolcards")
        for index, tool in enumerate(tools):
            card = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12, border_width=1, border_color=COLORS["border"])
            card.grid(row=index // columns, column=index % columns, sticky="nsew", padx=7, pady=7)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=category.icon, width=36, height=34, corner_radius=9, fg_color=COLORS["accent_soft"], text_color=COLORS["accent"], font=(FONT, 10, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 10))
            ctk.CTkLabel(card, text=tool.name, text_color=COLORS["text"], font=(FONT, 14, "bold")).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 5))
            ctk.CTkLabel(card, text=tool.description, text_color=COLORS["muted"], font=(FONT, 11), wraplength=220, justify="left", height=42).grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
            ctk.CTkButton(card, text="Open tool  →", anchor="w", height=32, corner_radius=7, fg_color="transparent", hover_color=COLORS["surface_hover"], text_color=COLORS["accent"], font=(FONT, 11, "bold"), command=lambda selected=tool: self.open_tool(selected)).grid(row=3, column=0, sticky="ew", padx=9, pady=(0, 9))

    def open_tool(self, tool: ToolSpec) -> None:
        self._active_tool = tool
        self._files.clear()
        self._output_dir = None
        self._render_navigation()
        self._render_tool()

    def _render_tool(self) -> None:
        tool = self._active_tool
        if tool is None:
            self._render_category()
            return
        self._clear_content()
        self._field_controls = {}
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(3, weight=1)
        ctk.CTkButton(page, text="←  All tools", width=100, height=28, fg_color="transparent", hover_color=COLORS["surface_hover"], text_color=COLORS["muted"], font=(FONT, 11), anchor="w", command=self._render_category).grid(row=0, column=0, sticky="w", padx=8, pady=(0, 10))
        ctk.CTkLabel(page, text=tool.name, text_color=COLORS["text"], font=(FONT, 25, "bold")).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 4))
        ctk.CTkLabel(page, text=tool.description, text_color=COLORS["muted"], font=(FONT, 12)).grid(row=2, column=0, sticky="w", padx=10, pady=(0, 16))
        body = ctk.CTkScrollableFrame(page, fg_color="transparent", scrollbar_button_color=COLORS["border"])
        body.grid(row=3, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self._build_file_picker(body, tool)
        self._build_options(body, tool)
        self._build_output_picker(body)
        run_row = ctk.CTkFrame(body, fg_color="transparent")
        run_row.grid(row=3, column=0, sticky="ew", padx=6, pady=(14, 24))
        run_row.grid_columnconfigure(0, weight=1)
        self.run_button = ctk.CTkButton(run_row, text="Run tool  →", width=150, height=42, corner_radius=9, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["background"], font=(FONT, 12, "bold"), command=self._run_tool)
        self.run_button.grid(row=0, column=1, sticky="e")
        self._render_file_list()

    def _build_file_picker(self, parent: Any, tool: ToolSpec) -> None:
        panel = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        panel.grid(row=0, column=0, sticky="ew", padx=6, pady=(0, 12))
        panel.grid_columnconfigure(0, weight=1)
        zone = ctk.CTkFrame(panel, fg_color=COLORS["background"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        zone.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        zone.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(zone, text="↥", text_color=COLORS["accent"], font=(FONT, 24, "bold")).grid(row=0, column=0, pady=(12, 2))
        ctk.CTkLabel(zone, text=tool.input_label, text_color=COLORS["text"], font=(FONT, 13, "bold")).grid(row=1, column=0, pady=(0, 3))
        dnd_available = self._enable_drop(zone)
        hint = "Drop files here or browse from this device" if dnd_available else "Select files from this device — drag-and-drop is optional"
        ctk.CTkLabel(zone, text=hint, text_color=COLORS["subtle"], font=(FONT, 10)).grid(row=2, column=0, pady=(0, 9))
        if tool.input_mode == "folder":
            ctk.CTkButton(zone, text="Choose folder", width=118, height=30, corner_radius=7, fg_color=COLORS["accent_soft"], hover_color=COLORS["surface_active"], text_color=COLORS["accent"], font=(FONT, 10, "bold"), command=self._choose_folder).grid(row=3, column=0, pady=(0, 12))
        else:
            ctk.CTkButton(zone, text="Browse files", width=118, height=30, corner_radius=7, fg_color=COLORS["accent_soft"], hover_color=COLORS["surface_active"], text_color=COLORS["accent"], font=(FONT, 10, "bold"), command=self._choose_files).grid(row=3, column=0, pady=(0, 12))
        self.file_list_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.file_list_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.file_list_frame.grid_columnconfigure(0, weight=1)

    def _enable_drop(self, widget: Any) -> bool:
        if not (hasattr(widget, "drop_target_register") and hasattr(widget, "dnd_bind")):
            return False
        try:
            from tkinterdnd2 import DND_FILES
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._on_drop)
            return True
        except Exception:
            return False

    def _on_drop(self, event: Any) -> str:
        try:
            self._add_paths(self.tk.splitlist(event.data))
        except Exception as exc:
            self._log(f"Could not read dropped paths: {exc}")
        return "copy"

    def _choose_files(self) -> None:
        paths = filedialog.askopenfilenames(parent=self.winfo_toplevel(), title="Choose files")
        self._add_paths(paths)

    def _choose_folder(self) -> None:
        path = filedialog.askdirectory(parent=self.winfo_toplevel(), title="Choose a folder")
        if path:
            self._add_paths((path,))

    def _add_paths(self, values: Any) -> None:
        known = {str(path) for path in self._files}
        for value in values:
            path = Path(value).expanduser()
            if path.exists() and str(path) not in known:
                self._files.append(path)
                known.add(str(path))
        self._render_file_list()

    def _render_file_list(self) -> None:
        if not hasattr(self, "file_list_frame") or not self.file_list_frame.winfo_exists():
            return
        for child in self.file_list_frame.winfo_children():
            child.destroy()
        if not self._files:
            return
        header = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=f"{len(self._files)} item{'s' if len(self._files) != 1 else ''} selected", text_color=COLORS["muted"], font=(FONT, 10, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Clear", width=48, height=23, fg_color="transparent", hover_color=COLORS["surface_hover"], text_color=COLORS["subtle"], font=(FONT, 9), command=self._clear_files).grid(row=0, column=1, sticky="e")
        for index, path in enumerate(self._files):
            row = ctk.CTkFrame(self.file_list_frame, fg_color=COLORS["background"], corner_radius=7)
            row.grid(row=index + 1, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(0, weight=1)
            try:
                meta = "Folder" if path.is_dir() else f"{path.suffix[1:].upper() or 'FILE'} · {self._format_size(path.stat().st_size)}"
            except OSError:
                meta = "Unavailable"
            ctk.CTkLabel(row, text=path.name, text_color=COLORS["text"], font=(FONT, 10, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=(9, 5), pady=(6, 0))
            ctk.CTkLabel(row, text=meta, text_color=COLORS["subtle"], font=(FONT, 9), anchor="w").grid(row=1, column=0, sticky="ew", padx=9, pady=(0, 6))
            ctk.CTkButton(row, text="×", width=28, height=26, fg_color="transparent", hover_color=COLORS["surface_hover"], text_color=COLORS["muted"], font=(FONT, 14), command=lambda selected=path: self._remove_file(selected)).grid(row=0, column=1, rowspan=2, padx=5)

    @staticmethod
    def _format_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"

    def _remove_file(self, path: Path) -> None:
        self._files = [item for item in self._files if item != path]
        self._render_file_list()

    def _clear_files(self) -> None:
        self._files.clear()
        self._render_file_list()

    def _build_options(self, parent: Any, tool: ToolSpec) -> None:
        panel = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        panel.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 12))
        panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text="Options", text_color=COLORS["text"], font=(FONT, 12, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
        if not tool.fields:
            ctk.CTkLabel(panel, text="No additional settings for this tool.", text_color=COLORS["subtle"], font=(FONT, 10)).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))
            return
        for index, field in enumerate(tool.fields, start=1):
            row = ctk.CTkFrame(panel, fg_color="transparent")
            row.grid(row=index, column=0, sticky="ew", padx=14, pady=5)
            row.grid_columnconfigure(0, weight=1)
            if field.kind == "toggle":
                variable = tk.BooleanVar(master=self, value=bool(field.default))
                control = ctk.CTkSwitch(row, text=field.label, variable=variable, onvalue=True, offvalue=False, progress_color=COLORS["accent"], button_color=COLORS["text"], button_hover_color=COLORS["white"], text_color=COLORS["muted"], font=(FONT, 10))
                control.grid(row=0, column=0, sticky="w", pady=5)
            else:
                ctk.CTkLabel(row, text=field.label, text_color=COLORS["muted"], font=(FONT, 10)).grid(row=0, column=0, sticky="w", pady=(0, 5))
                variable = tk.StringVar(master=self, value=str(field.default))
                if field.kind == "choice":
                    control = ctk.CTkOptionMenu(row, values=list(field.options), variable=variable, height=32, corner_radius=7, fg_color=COLORS["background"], button_color=COLORS["surface_active"], button_hover_color=COLORS["border"], text_color=COLORS["text"], dropdown_fg_color=COLORS["surface"], dropdown_text_color=COLORS["text"], font=(FONT, 10), dropdown_font=(FONT, 10))
                    control.grid(row=1, column=0, sticky="ew")
                else:
                    kwargs = {"show": "•"} if field.kind == "password" else {}
                    control = ctk.CTkEntry(row, textvariable=variable, placeholder_text=field.placeholder, height=32, corner_radius=7, fg_color=COLORS["background"], border_color=COLORS["border"], text_color=COLORS["text"], placeholder_text_color=COLORS["subtle"], font=(FONT, 10), **kwargs)
                    control.grid(row=1, column=0, sticky="ew")
            self._field_controls[field.key] = _FieldControl(field, variable)
        ctk.CTkFrame(panel, height=7, fg_color="transparent").grid(row=len(tool.fields) + 1, column=0)

    def _build_output_picker(self, parent: Any) -> None:
        panel = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        panel.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 2))
        panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text="Save results to", text_color=COLORS["text"], font=(FONT, 11, "bold")).grid(row=0, column=0, sticky="w", padx=13, pady=(10, 5))
        line = ctk.CTkFrame(panel, fg_color="transparent")
        line.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        line.grid_columnconfigure(0, weight=1)
        self.output_label = ctk.CTkLabel(line, text="Same folder as source files (handler default)", text_color=COLORS["subtle"], font=(FONT, 10), anchor="w")
        self.output_label.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(line, text="Choose…", width=78, height=28, corner_radius=7, fg_color=COLORS["surface_active"], hover_color=COLORS["border"], text_color=COLORS["text"], font=(FONT, 9), command=self._choose_output_dir).grid(row=0, column=1)

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(parent=self.winfo_toplevel(), title="Choose output folder")
        if path:
            self._output_dir = Path(path)
            self.output_label.configure(text=str(self._output_dir), text_color=COLORS["text"])

    def _request_options(self) -> dict[str, Any]:
        return {key: control.variable.get() for key, control in self._field_controls.items()}

    def _run_tool(self) -> None:
        tool = self._active_tool
        if tool is None:
            return
        if not self._files:
            messagebox.showinfo("Choose input", "Add at least one file or folder first.", parent=self.winfo_toplevel())
            return
        handler = self.handlers.get(tool.id) or self.handlers.get(tool.category)
        if handler is None:
            message = f"No processing handler registered for {tool.id}. The UI is ready; connect your existing local function."
            self._set_status("IDLE", 0, "Backend not connected")
            self._log(message)
            messagebox.showinfo("Connect a handler", message, parent=self.winfo_toplevel())
            return
        request = ToolRequest(tool.id, tuple(self._files), self._request_options(), self._output_dir)
        self.run_button.configure(state="disabled", text="Working…")
        self._set_status("RUNNING", 0, tool.name)
        self._log(f"Started {tool.name} ({len(request.files)} input item(s)).")
        reporter = ProgressReporter(lambda percent, message: self.events.put(("progress", percent, message)))
        self._future = self.executor.submit(handler, request, reporter)
        self._future.add_done_callback(self._on_future_done)

    def _on_future_done(self, future: Future[Any]) -> None:
        try:
            result = future.result()
            detail = str(result) if result is not None else "Complete"
            self.events.put(("finished", True, detail))
        except Exception as exc:
            self.events.put(("finished", False, f"{type(exc).__name__}: {exc}"))

    def _poll_events(self) -> None:
        if self._closing:
            return
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "progress":
                    _, percent, message = event
                    self._set_status("RUNNING", percent, message)
                elif event[0] == "finished":
                    _, success, detail = event
                    if hasattr(self, "run_button") and self.run_button.winfo_exists():
                        self.run_button.configure(state="normal", text="Run tool  →")
                    if success:
                        self._set_status("SUCCESS", 100, "Completed")
                        self._log(f"Finished: {detail}")
                    else:
                        self._set_status("FAILED", 0, "See activity log")
                        self._log(f"Processing failed: {detail}")
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _set_status(self, state: str, percent: float, detail: str) -> None:
        color = {"IDLE": COLORS["muted"], "RUNNING": COLORS["accent"], "SUCCESS": COLORS["success"], "FAILED": COLORS["danger"]}.get(state, COLORS["muted"])
        self.status_dot.configure(text_color=color)
        self.status_text.configure(text=state, text_color=color)
        self.progress.set(max(0.0, min(100.0, percent)) / 100.0)
        self.progress_label.configure(text=detail[:24])

    def _toggle_logs(self) -> None:
        if self.log_drawer.winfo_ismapped():
            self.log_drawer.grid_remove()
            self.log_toggle.configure(text="Show log  ˄")
        else:
            self.log_drawer.grid()
            self.log_toggle.configure(text="Hide log  ˅")

    def _log(self, message: str) -> None:
        if not hasattr(self, "log_text"):
            return
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{stamp}]  {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.master.destroy()


def launch(handlers: Mapping[str, Handler] | None = None, worker_count: int = 2) -> None:
    """Create the window and start Tk's event loop.

    tkinterdnd2 is detected automatically for drag-and-drop. Without it, the
    file and folder browse buttons remain fully available.
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
        root.configure(background=COLORS["background"])
    except ImportError:
        root = ctk.CTk(fg_color=COLORS["background"])
    root.title("OmniTools — Local File Workspace")
    root.geometry("1260x820")
    root.minsize(960, 640)
    app = OmniToolsApp(root, handlers=handlers, worker_count=worker_count)
    app.pack(fill="both", expand=True)
    root.mainloop()
