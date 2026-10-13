"""
OmniTools Studio Pro — High-Spec Modern Offline Desktop Application
Built with CustomTkinter & Multi-threaded Async Engine
"""

import os
import sys
import threading
import subprocess
import shutil
from typing import List, Optional
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from modules.pdf_tools import (
    remove_pdf_password, set_pdf_password, merge_pdfs, split_pdf,
    pdf_to_images, images_to_pdf
)
from modules.doc_tools import pdf_to_docx, docx_to_pdf, text_to_pdf
from modules.image_tools import (
    convert_image, batch_convert_images, resize_image, compress_image,
    SUPPORTED_IMAGE_FORMATS
)
from modules.audio_tools import (
    convert_audio, batch_convert_audio, extract_audio_from_video, trim_audio,
    SUPPORTED_AUDIO_FORMATS, get_ffmpeg_path
)
from modules.folder_sorter import analyze_folder, sort_folder
from modules.extra_tools import (
    calculate_file_hash, find_duplicate_files, batch_rename_files, generate_qr
)

# App Appearance Defaults
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def format_bytes(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


class OmniToolsApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ OmniTools Studio Pro — Offline Python Toolkit")
        self.geometry("1180x760")
        self.minsize(1040, 680)

        # Set window icon if available or configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.active_tab = "pdf"
        self.create_sidebar()
        self.create_main_content()

        # Select initial tab
        self.select_tab("pdf")

    # ==========================================================================
    # SIDEBAR DESIGN (HIGH SPEC)
    # ==========================================================================
    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=("#1e2530", "#0f141c"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        # Brand Logo Banner
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.logo_label = ctk.CTkLabel(
            logo_frame,
            text="⚡ OmniTools",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#38bdf8"
        )
        self.logo_label.pack(anchor="w")

        self.badge_label = ctk.CTkLabel(
            logo_frame,
            text="STUDIO PRO • 100% OFFLINE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#4ade80",
            fg_color=("#162820", "#12281e"),
            corner_radius=6,
            padx=8,
            pady=2
        )
        self.badge_label.pack(anchor="w", pady=(4, 0))

        # Search / Quick Filter Bar
        self.search_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text="🔍 Search tools...",
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("#2b3544", "#161f2e"),
            border_color="#334155"
        )
        self.search_entry.grid(row=1, column=0, padx=16, pady=(10, 15), sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search_filter)

        # Navigation Buttons
        self.nav_buttons = {}
        tabs = [
            ("pdf", "📄  PDF Hub", "Unlock, Protect, Merge, Split"),
            ("docs", "📝  Document Station", "PDF ⇄ Word, Text to PDF"),
            ("images", "🖼️  Image Studio", "Universal format converter, Resize"),
            ("audio", "🎵  Audio & Video Deck", "Convert MP3/WAV/FLAC, Extract"),
            ("sorter", "🗂️  Folder Organizer", "Sort files into categorized folders"),
            ("extra", "🧰  Extra Utilities", "Hashes, Duplicates, QR Generator"),
        ]

        for idx, (tab_id, tab_name, subtitle) in enumerate(tabs, start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=f"{tab_name}\n   {subtitle}",
                height=52,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="normal"),
                fg_color="transparent",
                text_color=("gray20", "gray85"),
                hover_color=("#2e3b4e", "#1b2537"),
                corner_radius=8,
                command=lambda tid=tab_id: self.select_tab(tid)
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[tab_id] = btn

        # System Specs Card (Bottom Sidebar)
        specs_card = ctk.CTkFrame(self.sidebar_frame, fg_color=("#222c3d", "#131924"), corner_radius=8)
        specs_card.grid(row=10, column=0, padx=14, pady=(10, 15), sticky="ew")

        ffmpeg_status = "Available" if get_ffmpeg_path() else "Missing"
        ffmpeg_color = "#4ade80" if ffmpeg_status == "Available" else "#f87171"

        ctk.CTkLabel(specs_card, text="SYSTEM STATUS", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray50").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(specs_card, text="• Network: Offline Only", font=ctk.CTkFont(size=11), text_color="#38bdf8").pack(anchor="w", padx=12)
        ctk.CTkLabel(specs_card, text=f"• Local FFmpeg: {ffmpeg_status}", font=ctk.CTkFont(size=11), text_color=ffmpeg_color).pack(anchor="w", padx=12)
        ctk.CTkLabel(specs_card, text="• PyMuPDF Engine: Ready", font=ctk.CTkFont(size=11), text_color="#4ade80").pack(anchor="w", padx=12, pady=(0, 8))

        # Appearance Selector
        theme_bar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        theme_bar.grid(row=11, column=0, padx=14, pady=(0, 15), sticky="ew")
        ctk.CTkLabel(theme_bar, text="Theme:", font=ctk.CTkFont(size=11), text_color="gray60").pack(side="left")
        theme_menu = ctk.CTkOptionMenu(
            theme_bar,
            values=["Dark", "Light", "System"],
            width=90,
            height=26,
            command=lambda m: ctk.set_appearance_mode(m)
        )
        theme_menu.pack(side="right")

    def _on_search_filter(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            for btn in self.nav_buttons.values():
                btn.grid()
            return

        for tid, btn in self.nav_buttons.items():
            txt = btn.cget("text").lower()
            if query in txt or query in tid:
                btn.grid()
            else:
                btn.grid_remove()

    # ==========================================================================
    # MAIN CONTENT CONTAINER
    # ==========================================================================
    def create_main_content(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Global Top Header Bar
        self.top_bar = ctk.CTkFrame(self.main_container, height=48, fg_color=("#f1f5f9", "#111722"), corner_radius=8)
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self.current_title_label = ctk.CTkLabel(
            self.top_bar,
            text="📄 PDF Hub",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        self.current_title_label.pack(side="left", padx=16, pady=8)

        # Global Progress Bar inside Top Bar
        self.global_progress = ctk.CTkProgressBar(self.top_bar, width=220, height=10, mode="indeterminate")
        self.global_progress.set(0)

        self.status_pill = ctk.CTkLabel(
            self.top_bar,
            text="IDLE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8",
            fg_color=("#e2e8f0", "#1e293b"),
            corner_radius=6,
            padx=10,
            pady=3
        )
        self.status_pill.pack(side="right", padx=16)

        # Views Container
        self.views_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.views_container.grid(row=1, column=0, sticky="nsew")
        self.views_container.grid_rowconfigure(0, weight=1)
        self.views_container.grid_columnconfigure(0, weight=1)

        self.views = {
            "pdf": self.build_pdf_view(),
            "docs": self.build_docs_view(),
            "images": self.build_images_view(),
            "audio": self.build_audio_view(),
            "sorter": self.build_sorter_view(),
            "extra": self.build_extra_view(),
        }

    def select_tab(self, tab_id: str):
        self.active_tab = tab_id
        titles = {
            "pdf": "📄 PDF Hub — Password Remover, Protection, Merge & Split",
            "docs": "📝 Document Station — PDF ⇄ Word DOCX, TXT Converter",
            "images": "🖼️ Image Studio — Universal Image Converter, Resize & Compress",
            "audio": "🎵 Audio Deck — Format Converter, Video Soundtrack Extractor",
            "sorter": "🗂️ Smart Folder Sorter — Automated Categorized Organization",
            "extra": "🧰 Extra Utilities — Hash Checksum, Duplicate Scanner, QR Maker"
        }
        self.current_title_label.configure(text=titles.get(tab_id, "OmniTools"))

        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(fg_color=("#2563eb", "#1d4ed8"), text_color="#ffffff", font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color=("gray20", "gray85"), font=ctk.CTkFont(size=13, weight="normal"))

        for tid, frame in self.views.items():
            if tid == tab_id:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

    # Async Task Runner with High-Spec Interactive Feedback
    def run_task_async(self, func, log_box: ctk.CTkTextbox, file_badge: Optional[ctk.CTkLabel], *args, **kwargs):
        def worker():
            self.status_pill.configure(text="RUNNING...", text_color="#38bdf8", fg_color="#0c4a6e")
            self.global_progress.pack(side="right", padx=10)
            self.global_progress.start()

            log_box.configure(state="normal")
            log_box.insert("end", "\n[STATUS] Starting operation in background...\n")
            log_box.see("end")
            log_box.configure(state="disabled")

            try:
                res = func(*args, **kwargs)
                log_box.configure(state="normal")
                if res.get("success"):
                    self.status_pill.configure(text="SUCCESS", text_color="#4ade80", fg_color="#14532d")
                    log_box.insert("end", "[SUCCESS] Operation finished successfully!\n")
                    for k, v in res.items():
                        if k not in ("success", "plan"):
                            log_box.insert("end", f"  • {k}: {v}\n")
                    if file_badge and res.get("output"):
                        file_badge.configure(text=f"Last output: {os.path.basename(res['output'])}")
                else:
                    self.status_pill.configure(text="FAILED", text_color="#f87171", fg_color="#7f1d1d")
                    log_box.insert("end", f"[ERROR] {res.get('error')}\n")
                log_box.see("end")
                log_box.configure(state="disabled")
            except Exception as e:
                self.status_pill.configure(text="ERROR", text_color="#f87171", fg_color="#7f1d1d")
                log_box.configure(state="normal")
                log_box.insert("end", f"[EXCEPTION] {str(e)}\n")
                log_box.see("end")
                log_box.configure(state="disabled")
            finally:
                self.global_progress.stop()
                self.global_progress.pack_forget()

        threading.Thread(target=worker, daemon=True).start()

    def open_in_explorer(self, file_or_folder: str):
        if not file_or_folder:
            return
        p = os.path.normpath(file_or_folder)
        if os.path.exists(p):
            folder = p if os.path.isdir(p) else os.path.dirname(p)
            os.startfile(folder)
        else:
            messagebox.showinfo("Path Notice", f"Path does not exist yet:\n{p}")

    def update_file_meta_badge(self, file_path: str, badge: ctk.CTkLabel):
        if os.path.isfile(file_path):
            sz = os.path.getsize(file_path)
            ext = os.path.splitext(file_path)[1].upper()
            badge.configure(text=f"Detected: {ext} | Size: {format_bytes(sz)}", text_color="#38bdf8")
        else:
            badge.configure(text="No file selected", text_color="gray50")

    # ==========================================================================
    # VIEW 1: PDF HUB
    # ==========================================================================
    def build_pdf_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        tabview = ctk.CTkTabview(frame, fg_color=("#ffffff", "#131a26"))
        tabview.pack(fill="both", expand=True)

        t_unlock = tabview.add("🔓 Unlock PDF")
        t_protect = tabview.add("🔒 Protect PDF")
        t_merge = tabview.add("📑 Merge PDFs")
        t_split = tabview.add("✂️ Split PDF")
        t_to_img = tabview.add("🖼️ PDF to Images")

        # Unlock PDF
        c1 = ctk.CTkFrame(t_unlock, fg_color="transparent")
        c1.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(c1, text="Remove Known Password from Encrypted PDF", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(c1, text="Instantly decrypts and creates a permanently unlocked copy of your PDF.", font=ctk.CTkFont(size=11), text_color="gray50").pack(anchor="w", pady=(0, 10))

        badge1 = ctk.CTkLabel(c1, text="No file selected", font=ctk.CTkFont(size=11), text_color="gray50")
        badge1.pack(anchor="w", pady=(0, 4))

        f_in = ctk.CTkFrame(c1, fg_color="transparent")
        f_in.pack(fill="x", pady=4)
        e_in = ctk.CTkEntry(f_in, placeholder_text="Select encrypted PDF...", height=36)
        e_in.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_in, text="Browse PDF...", height=36, command=lambda: self._browse_and_badge(e_in, badge1, [("PDF Files", "*.pdf")])).pack(side="right")

        f_pwd = ctk.CTkFrame(c1, fg_color="transparent")
        f_pwd.pack(fill="x", pady=4)
        e_pwd = ctk.CTkEntry(f_pwd, placeholder_text="Enter PDF Password (e.g. KESA1998)", show="*", height=36)
        e_pwd.pack(side="left", fill="x", expand=True)

        f_out = ctk.CTkFrame(c1, fg_color="transparent")
        f_out.pack(fill="x", pady=4)
        e_out = ctk.CTkEntry(f_out, placeholder_text="Output unlocked PDF path (optional)...", height=36)
        e_out.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_out, text="Save As...", height=36, command=lambda: self._save_file(e_out, [("PDF Files", "*.pdf")])).pack(side="right")

        log1 = ctk.CTkTextbox(c1, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log1.pack(fill="both", expand=True, pady=10)

        f_act = ctk.CTkFrame(c1, fg_color="transparent")
        f_act.pack(fill="x", pady=(0, 5))

        def on_unlock():
            inp = e_in.get().strip().strip('"')
            if not inp:
                messagebox.showerror("Error", "Please choose an encrypted PDF file.")
                return
            out = e_out.get().strip().strip('"') or (os.path.splitext(inp)[0] + "_unlocked.pdf")
            self.run_task_async(remove_pdf_password, log1, badge1, inp, out, e_pwd.get())

        ctk.CTkButton(f_act, text="🔓 Unlock PDF Now", fg_color="#16a34a", hover_color="#15803d", height=36, font=ctk.CTkFont(weight="bold"), command=on_unlock).pack(side="left", padx=(0, 10))
        ctk.CTkButton(f_act, text="Open Output Folder", height=36, fg_color="#334155", hover_color="#475569", command=lambda: self.open_in_explorer(e_out.get() or e_in.get())).pack(side="left")

        # Protect PDF
        c2 = ctk.CTkFrame(t_protect, fg_color="transparent")
        c2.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c2, text="Encrypt PDF with a Password", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        badge2 = ctk.CTkLabel(c2, text="No file selected", font=ctk.CTkFont(size=11), text_color="gray50")
        badge2.pack(anchor="w", pady=(0, 4))

        f_in2 = ctk.CTkFrame(c2, fg_color="transparent")
        f_in2.pack(fill="x", pady=4)
        e_in2 = ctk.CTkEntry(f_in2, placeholder_text="Select PDF...", height=36)
        e_in2.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_in2, text="Browse PDF...", height=36, command=lambda: self._browse_and_badge(e_in2, badge2, [("PDF Files", "*.pdf")])).pack(side="right")

        e_pwd2 = ctk.CTkEntry(c2, placeholder_text="Set New Password", show="*", height=36)
        e_pwd2.pack(fill="x", pady=4)

        f_out2 = ctk.CTkFrame(c2, fg_color="transparent")
        f_out2.pack(fill="x", pady=4)
        e_out2 = ctk.CTkEntry(f_out2, placeholder_text="Output protected PDF path...", height=36)
        e_out2.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_out2, text="Save As...", height=36, command=lambda: self._save_file(e_out2, [("PDF Files", "*.pdf")])).pack(side="right")

        log2 = ctk.CTkTextbox(c2, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log2.pack(fill="both", expand=True, pady=10)

        def on_protect():
            inp = e_in2.get().strip().strip('"')
            pwd = e_pwd2.get().strip()
            out = e_out2.get().strip().strip('"') or (os.path.splitext(inp)[0] + "_protected.pdf")
            self.run_task_async(set_pdf_password, log2, badge2, inp, out, pwd)

        ctk.CTkButton(c2, text="🔒 Protect PDF", fg_color="#2563eb", height=36, font=ctk.CTkFont(weight="bold"), command=on_protect).pack(anchor="w")

        # Merge PDFs
        c3 = ctk.CTkFrame(t_merge, fg_color="transparent")
        c3.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c3, text="Combine Multiple PDFs into One Document", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        merge_files = []
        lbl_mcount = ctk.CTkLabel(c3, text="0 PDF files selected", text_color="#38bdf8")
        lbl_mcount.pack(anchor="w")

        txt_mfiles = ctk.CTkTextbox(c3, height=80, fg_color=("#f8fafc", "#080c14"))
        txt_mfiles.pack(fill="x", pady=4)

        def add_mfiles():
            paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
            if paths:
                merge_files.extend(paths)
                lbl_mcount.configure(text=f"{len(merge_files)} PDF files selected")
                txt_mfiles.delete("0.0", "end")
                txt_mfiles.insert("end", "\n".join(merge_files))

        f_mbtns = ctk.CTkFrame(c3, fg_color="transparent")
        f_mbtns.pack(fill="x", pady=4)
        ctk.CTkButton(f_mbtns, text="+ Add PDFs...", command=add_mfiles).pack(side="left", padx=(0, 10))
        ctk.CTkButton(f_mbtns, text="Clear List", fg_color="#475569", command=lambda: [merge_files.clear(), txt_mfiles.delete("0.0", "end"), lbl_mcount.configure(text="0 files")]).pack(side="left")

        f_mout = ctk.CTkFrame(c3, fg_color="transparent")
        f_mout.pack(fill="x", pady=4)
        e_mout = ctk.CTkEntry(f_mout, placeholder_text="Output merged PDF path...", height=36)
        e_mout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_mout, text="Save As...", height=36, command=lambda: self._save_file(e_mout, [("PDF Files", "*.pdf")])).pack(side="right")

        log3 = ctk.CTkTextbox(c3, height=100, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log3.pack(fill="both", expand=True, pady=8)

        def on_merge():
            out = e_mout.get().strip().strip('"')
            self.run_task_async(merge_pdfs, log3, None, merge_files, out)

        ctk.CTkButton(c3, text="📑 Merge All PDFs", height=36, font=ctk.CTkFont(weight="bold"), command=on_merge).pack(anchor="w")

        # Split PDF
        c4 = ctk.CTkFrame(t_split, fg_color="transparent")
        c4.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c4, text="Split PDF or Extract Pages Range", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        f_sin = ctk.CTkFrame(c4, fg_color="transparent")
        f_sin.pack(fill="x", pady=4)
        e_sin = ctk.CTkEntry(f_sin, placeholder_text="Select PDF to split...", height=36)
        e_sin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_sin, text="Browse...", height=36, command=lambda: self._browse_file(e_sin, [("PDF Files", "*.pdf")])).pack(side="right")

        e_srange = ctk.CTkEntry(c4, placeholder_text="Page range (e.g. '1-3, 5' or leave empty to extract every page)", height=36)
        e_srange.pack(fill="x", pady=4)

        f_sout = ctk.CTkFrame(c4, fg_color="transparent")
        f_sout.pack(fill="x", pady=4)
        e_sout = ctk.CTkEntry(f_sout, placeholder_text="Output directory...", height=36)
        e_sout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_sout, text="Browse Folder...", height=36, command=lambda: self._browse_folder(e_sout)).pack(side="right")

        log4 = ctk.CTkTextbox(c4, height=120, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log4.pack(fill="both", expand=True, pady=8)

        def on_split():
            inp = e_sin.get().strip().strip('"')
            out = e_sout.get().strip().strip('"') or os.path.dirname(inp)
            r = e_srange.get().strip() or None
            self.run_task_async(split_pdf, log4, None, inp, out, r)

        ctk.CTkButton(c4, text="✂️ Split PDF", height=36, font=ctk.CTkFont(weight="bold"), command=on_split).pack(anchor="w")

        # PDF to Images
        c5 = ctk.CTkFrame(t_to_img, fg_color="transparent")
        c5.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c5, text="Render High-Resolution Images from PDF Pages", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))

        f_iin = ctk.CTkFrame(c5, fg_color="transparent")
        f_iin.pack(fill="x", pady=4)
        e_iin = ctk.CTkEntry(f_iin, placeholder_text="Select PDF...", height=36)
        e_iin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_iin, text="Browse...", height=36, command=lambda: self._browse_file(e_iin, [("PDF Files", "*.pdf")])).pack(side="right")

        f_iopts = ctk.CTkFrame(c5, fg_color="transparent")
        f_iopts.pack(fill="x", pady=4)
        ctk.CTkLabel(f_iopts, text="Format:").pack(side="left", padx=(0, 5))
        ifmt = ctk.CTkOptionMenu(f_iopts, values=["png", "jpg", "webp"], width=90)
        ifmt.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_iopts, text="DPI:").pack(side="left", padx=(0, 5))
        idpi = ctk.CTkOptionMenu(f_iopts, values=["150", "200", "300"], width=90)
        idpi.set("200")
        idpi.pack(side="left")

        f_iout = ctk.CTkFrame(c5, fg_color="transparent")
        f_iout.pack(fill="x", pady=4)
        e_iout = ctk.CTkEntry(f_iout, placeholder_text="Output folder for images...", height=36)
        e_iout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_iout, text="Browse Folder...", height=36, command=lambda: self._browse_folder(e_iout)).pack(side="right")

        log5 = ctk.CTkTextbox(c5, height=120, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log5.pack(fill="both", expand=True, pady=8)

        def on_p2i():
            inp = e_iin.get().strip().strip('"')
            out = e_iout.get().strip().strip('"') or os.path.dirname(inp)
            self.run_task_async(pdf_to_images, log5, None, inp, out, ifmt.get(), int(idpi.get()))

        ctk.CTkButton(c5, text="Render Images", height=36, font=ctk.CTkFont(weight="bold"), command=on_p2i).pack(anchor="w")

        return frame

    # ==========================================================================
    # VIEW 2: DOCUMENT STATION
    # ==========================================================================
    def build_docs_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        tabview = ctk.CTkTabview(frame, fg_color=("#ffffff", "#131a26"))
        tabview.pack(fill="both", expand=True)

        t_p2d = tabview.add("📄 PDF to Word DOCX")
        t_d2p = tabview.add("📝 Word DOCX to PDF")

        # PDF to DOCX
        c1 = ctk.CTkFrame(t_p2d, fg_color="transparent")
        c1.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c1, text="Convert PDF into Editable Microsoft Word (.docx)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        badge1 = ctk.CTkLabel(c1, text="No file selected", font=ctk.CTkFont(size=11), text_color="gray50")
        badge1.pack(anchor="w", pady=(0, 4))

        f_in1 = ctk.CTkFrame(c1, fg_color="transparent")
        f_in1.pack(fill="x", pady=4)
        e_in1 = ctk.CTkEntry(f_in1, placeholder_text="Select PDF...", height=36)
        e_in1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_in1, text="Browse PDF...", height=36, command=lambda: self._browse_and_badge(e_in1, badge1, [("PDF Files", "*.pdf")])).pack(side="right")

        f_out1 = ctk.CTkFrame(c1, fg_color="transparent")
        f_out1.pack(fill="x", pady=4)
        e_out1 = ctk.CTkEntry(f_out1, placeholder_text="Output Word DOCX path...", height=36)
        e_out1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_out1, text="Save As...", height=36, command=lambda: self._save_file(e_out1, [("Word Documents", "*.docx")])).pack(side="right")

        log1 = ctk.CTkTextbox(c1, height=180, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log1.pack(fill="both", expand=True, pady=10)

        def on_p2d():
            inp = e_in1.get().strip().strip('"')
            out = e_out1.get().strip().strip('"') or (os.path.splitext(inp)[0] + ".docx")
            self.run_task_async(pdf_to_docx, log1, badge1, inp, out)

        ctk.CTkButton(c1, text="Convert PDF to Word DOCX", fg_color="#16a34a", hover_color="#15803d", height=36, font=ctk.CTkFont(weight="bold"), command=on_p2d).pack(anchor="w")

        # DOCX to PDF
        c2 = ctk.CTkFrame(t_d2p, fg_color="transparent")
        c2.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c2, text="Convert Microsoft Word (.docx) to PDF", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        badge2 = ctk.CTkLabel(c2, text="No file selected", font=ctk.CTkFont(size=11), text_color="gray50")
        badge2.pack(anchor="w", pady=(0, 4))

        f_in2 = ctk.CTkFrame(c2, fg_color="transparent")
        f_in2.pack(fill="x", pady=4)
        e_in2 = ctk.CTkEntry(f_in2, placeholder_text="Select DOCX...", height=36)
        e_in2.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_in2, text="Browse DOCX...", height=36, command=lambda: self._browse_and_badge(e_in2, badge2, [("Word Documents", "*.docx")])).pack(side="right")

        f_out2 = ctk.CTkFrame(c2, fg_color="transparent")
        f_out2.pack(fill="x", pady=4)
        e_out2 = ctk.CTkEntry(f_out2, placeholder_text="Output PDF path...", height=36)
        e_out2.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_out2, text="Save As...", height=36, command=lambda: self._save_file(e_out2, [("PDF Files", "*.pdf")])).pack(side="right")

        log2 = ctk.CTkTextbox(c2, height=180, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log2.pack(fill="both", expand=True, pady=10)

        def on_d2p():
            inp = e_in2.get().strip().strip('"')
            out = e_out2.get().strip().strip('"') or (os.path.splitext(inp)[0] + ".pdf")
            self.run_task_async(docx_to_pdf, log2, badge2, inp, out)

        ctk.CTkButton(c2, text="Convert Word to PDF", fg_color="#2563eb", height=36, font=ctk.CTkFont(weight="bold"), command=on_d2p).pack(anchor="w")

        return frame

    # ==========================================================================
    # VIEW 3: IMAGE STUDIO
    # ==========================================================================
    def build_images_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        tabview = ctk.CTkTabview(frame, fg_color=("#ffffff", "#131a26"))
        tabview.pack(fill="both", expand=True)

        t_single = tabview.add("🔄 Single Image")
        t_batch = tabview.add("📁 Batch Folder")
        t_resize = tabview.add("📐 Resize & Scale")
        t_compress = tabview.add("🗜️ Compress")

        # Single Image
        c1 = ctk.CTkFrame(t_single, fg_color="transparent")
        c1.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c1, text="Convert Between Any Image Format (PNG, JPG, WEBP, BMP, GIF, TIFF, ICO)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        badge1 = ctk.CTkLabel(c1, text="No image selected", font=ctk.CTkFont(size=11), text_color="gray50")
        badge1.pack(anchor="w", pady=(0, 4))

        f_in1 = ctk.CTkFrame(c1, fg_color="transparent")
        f_in1.pack(fill="x", pady=4)
        e_in1 = ctk.CTkEntry(f_in1, placeholder_text="Select image...", height=36)
        e_in1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_in1, text="Browse Image...", height=36, command=lambda: self._browse_and_badge(e_in1, badge1, [("Images", "*.*")])).pack(side="right")

        f_opts1 = ctk.CTkFrame(c1, fg_color="transparent")
        f_opts1.pack(fill="x", pady=6)
        ctk.CTkLabel(f_opts1, text="Target Format:").pack(side="left", padx=(0, 6))
        fmt1 = ctk.CTkOptionMenu(f_opts1, values=["jpg", "png", "webp", "bmp", "gif", "tiff", "ico"], width=100)
        fmt1.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(f_opts1, text="Quality:").pack(side="left", padx=(0, 6))
        q_slide = ctk.CTkSlider(f_opts1, from_=10, to=100, number_of_steps=18, width=160)
        q_slide.set(95)
        q_slide.pack(side="left", padx=(0, 6))
        q_lbl = ctk.CTkLabel(f_opts1, text="95%", text_color="#38bdf8")
        q_lbl.pack(side="left")
        q_slide.configure(command=lambda val: q_lbl.configure(text=f"{int(val)}%"))

        f_out1 = ctk.CTkFrame(c1, fg_color="transparent")
        f_out1.pack(fill="x", pady=4)
        e_out1 = ctk.CTkEntry(f_out1, placeholder_text="Output image path (optional)...", height=36)
        e_out1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_out1, text="Save As...", height=36, command=lambda: self._save_file(e_out1)).pack(side="right")

        log1 = ctk.CTkTextbox(c1, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log1.pack(fill="both", expand=True, pady=10)

        def on_conv_img():
            inp = e_in1.get().strip().strip('"')
            f = fmt1.get().lower()
            out = e_out1.get().strip().strip('"') or f"{os.path.splitext(inp)[0]}.{f}"
            self.run_task_async(convert_image, log1, badge1, inp, out, f, quality=int(q_slide.get()))

        ctk.CTkButton(c1, text="Convert Image", fg_color="#16a34a", hover_color="#15803d", height=36, font=ctk.CTkFont(weight="bold"), command=on_conv_img).pack(anchor="w")

        # Batch Folder
        c2 = ctk.CTkFrame(t_batch, fg_color="transparent")
        c2.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c2, text="Batch Convert Entire Folder of Images", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        f_bin = ctk.CTkFrame(c2, fg_color="transparent")
        f_bin.pack(fill="x", pady=4)
        e_bin = ctk.CTkEntry(f_bin, placeholder_text="Select input folder...", height=36)
        e_bin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_bin, text="Browse Folder...", height=36, command=lambda: self._browse_folder(e_bin)).pack(side="right")

        f_bopts = ctk.CTkFrame(c2, fg_color="transparent")
        f_bopts.pack(fill="x", pady=6)
        ctk.CTkLabel(f_bopts, text="Target Format:").pack(side="left", padx=(0, 6))
        bfmt = ctk.CTkOptionMenu(f_bopts, values=["webp", "png", "jpg", "bmp", "gif", "ico"], width=100)
        bfmt.pack(side="left", padx=(0, 20))
        b_sub = ctk.CTkCheckBox(f_bopts, text="Include Subdirectories")
        b_sub.pack(side="left")

        f_bout = ctk.CTkFrame(c2, fg_color="transparent")
        f_bout.pack(fill="x", pady=4)
        e_bout = ctk.CTkEntry(f_bout, placeholder_text="Output folder...", height=36)
        e_bout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_bout, text="Browse Folder...", height=36, command=lambda: self._browse_folder(e_bout)).pack(side="right")

        log2 = ctk.CTkTextbox(c2, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log2.pack(fill="both", expand=True, pady=10)

        def on_batch_img():
            inp_dir = e_bin.get().strip().strip('"')
            f = bfmt.get().lower()
            out_dir = e_bout.get().strip().strip('"') or os.path.join(inp_dir, f"converted_{f}")
            self.run_task_async(batch_convert_images, log2, None, inp_dir, out_dir, f, recursive=b_sub.get() == 1)

        ctk.CTkButton(c2, text="Start Batch Image Conversion", height=36, font=ctk.CTkFont(weight="bold"), command=on_batch_img).pack(anchor="w")

        # Resize Image
        c3 = ctk.CTkFrame(t_resize, fg_color="transparent")
        c3.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c3, text="Resize Image by Scale % or Custom Pixel Dimensions", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        f_rin = ctk.CTkFrame(c3, fg_color="transparent")
        f_rin.pack(fill="x", pady=4)
        e_rin = ctk.CTkEntry(f_rin, placeholder_text="Select image...", height=36)
        e_rin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_rin, text="Browse...", height=36, command=lambda: self._browse_file(e_rin)).pack(side="right")

        f_ropts = ctk.CTkFrame(c3, fg_color="transparent")
        f_ropts.pack(fill="x", pady=6)
        ctk.CTkLabel(f_ropts, text="Scale %:").pack(side="left", padx=(0, 4))
        e_rpct = ctk.CTkEntry(f_ropts, width=70, height=32, placeholder_text="50")
        e_rpct.insert(0, "50")
        e_rpct.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_ropts, text="OR Width (px):").pack(side="left", padx=(0, 4))
        e_rw = ctk.CTkEntry(f_ropts, width=80, height=32, placeholder_text="1920")
        e_rw.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(f_ropts, text="Height (px):").pack(side="left", padx=(0, 4))
        e_rh = ctk.CTkEntry(f_ropts, width=80, height=32, placeholder_text="1080")
        e_rh.pack(side="left")

        f_rout = ctk.CTkFrame(c3, fg_color="transparent")
        f_rout.pack(fill="x", pady=4)
        e_rout = ctk.CTkEntry(f_rout, placeholder_text="Output resized image path...", height=36)
        e_rout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_rout, text="Save As...", height=36, command=lambda: self._save_file(e_rout)).pack(side="right")

        log3 = ctk.CTkTextbox(c3, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log3.pack(fill="both", expand=True, pady=10)

        def on_resize():
            inp = e_rin.get().strip().strip('"')
            out = e_rout.get().strip().strip('"') or f"{os.path.splitext(inp)[0]}_resized{os.path.splitext(inp)[1]}"
            w = int(e_rw.get().strip()) if e_rw.get().strip() else None
            h = int(e_rh.get().strip()) if e_rh.get().strip() else None
            pct = float(e_rpct.get().strip()) if e_rpct.get().strip() and not (w or h) else None
            self.run_task_async(resize_image, log3, None, inp, out, scale_pct=pct, width=w, height=h)

        ctk.CTkButton(c3, text="Resize Image", height=36, font=ctk.CTkFont(weight="bold"), command=on_resize).pack(anchor="w")

        # Compress Image
        c4 = ctk.CTkFrame(t_compress, fg_color="transparent")
        c4.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c4, text="Compress Image File Size", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        f_cin = ctk.CTkFrame(c4, fg_color="transparent")
        f_cin.pack(fill="x", pady=4)
        e_cin = ctk.CTkEntry(f_cin, placeholder_text="Select image to compress...", height=36)
        e_cin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_cin, text="Browse...", height=36, command=lambda: self._browse_file(e_cin)).pack(side="right")

        f_copts = ctk.CTkFrame(c4, fg_color="transparent")
        f_copts.pack(fill="x", pady=6)
        ctk.CTkLabel(f_copts, text="Compression Quality:").pack(side="left", padx=(0, 6))
        c_slider = ctk.CTkSlider(f_copts, from_=10, to=95, number_of_steps=17, width=180)
        c_slider.set(70)
        c_slider.pack(side="left", padx=(0, 6))
        c_lbl = ctk.CTkLabel(f_copts, text="70%", text_color="#38bdf8")
        c_lbl.pack(side="left")
        c_slider.configure(command=lambda val: c_lbl.configure(text=f"{int(val)}%"))

        f_cout = ctk.CTkFrame(c4, fg_color="transparent")
        f_cout.pack(fill="x", pady=4)
        e_cout = ctk.CTkEntry(f_cout, placeholder_text="Output compressed image path...", height=36)
        e_cout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_cout, text="Save As...", height=36, command=lambda: self._save_file(e_cout)).pack(side="right")

        log4 = ctk.CTkTextbox(c4, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log4.pack(fill="both", expand=True, pady=10)

        def on_compress():
            inp = e_cin.get().strip().strip('"')
            out = e_cout.get().strip().strip('"') or f"{os.path.splitext(inp)[0]}_compressed{os.path.splitext(inp)[1]}"
            self.run_task_async(compress_image, log4, None, inp, out, quality=int(c_slider.get()))

        ctk.CTkButton(c4, text="Compress Image", height=36, font=ctk.CTkFont(weight="bold"), command=on_compress).pack(anchor="w")

        return frame

    # ==========================================================================
    # VIEW 4: AUDIO DECK
    # ==========================================================================
    def build_audio_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        tabview = ctk.CTkTabview(frame, fg_color=("#ffffff", "#131a26"))
        tabview.pack(fill="both", expand=True)

        t_conv = tabview.add("🔄 Audio Converter")
        t_vid = tabview.add("🎬 Video to Audio")
        t_trim = tabview.add("✂️ Trim Audio")

        # Audio Converter
        c1 = ctk.CTkFrame(t_conv, fg_color="transparent")
        c1.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c1, text="Convert Audio Formats (MP3, WAV, AAC, FLAC, OGG, M4A, OPUS)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        badge1 = ctk.CTkLabel(c1, text="No audio selected", font=ctk.CTkFont(size=11), text_color="gray50")
        badge1.pack(anchor="w", pady=(0, 4))

        f_in1 = ctk.CTkFrame(c1, fg_color="transparent")
        f_in1.pack(fill="x", pady=4)
        e_in1 = ctk.CTkEntry(f_in1, placeholder_text="Select audio file...", height=36)
        e_in1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_in1, text="Browse Audio...", height=36, command=lambda: self._browse_and_badge(e_in1, badge1, [("Audio Files", "*.*")])).pack(side="right")

        f_opts1 = ctk.CTkFrame(c1, fg_color="transparent")
        f_opts1.pack(fill="x", pady=6)
        ctk.CTkLabel(f_opts1, text="Target Format:").pack(side="left", padx=(0, 6))
        afmt = ctk.CTkOptionMenu(f_opts1, values=["mp3", "wav", "aac", "ogg", "flac", "m4a", "opus"], width=100)
        afmt.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_opts1, text="Bitrate:").pack(side="left", padx=(0, 6))
        abit = ctk.CTkOptionMenu(f_opts1, values=["128k", "192k", "256k", "320k"], width=90)
        abit.set("192k")
        abit.pack(side="left")

        f_out1 = ctk.CTkFrame(c1, fg_color="transparent")
        f_out1.pack(fill="x", pady=4)
        e_out1 = ctk.CTkEntry(f_out1, placeholder_text="Output audio path (optional)...", height=36)
        e_out1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_out1, text="Save As...", height=36, command=lambda: self._save_file(e_out1)).pack(side="right")

        log1 = ctk.CTkTextbox(c1, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log1.pack(fill="both", expand=True, pady=10)

        def on_conv_aud():
            inp = e_in1.get().strip().strip('"')
            f = afmt.get().lower()
            out = e_out1.get().strip().strip('"') or f"{os.path.splitext(inp)[0]}.{f}"
            self.run_task_async(convert_audio, log1, badge1, inp, out, f, bitrate=abit.get())

        ctk.CTkButton(c1, text="Convert Audio", fg_color="#16a34a", hover_color="#15803d", height=36, font=ctk.CTkFont(weight="bold"), command=on_conv_aud).pack(anchor="w")

        # Video to Audio
        c2 = ctk.CTkFrame(t_vid, fg_color="transparent")
        c2.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c2, text="Extract Audio Soundtrack from Video (MP4, MKV, AVI, etc.)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        badge2 = ctk.CTkLabel(c2, text="No video selected", font=ctk.CTkFont(size=11), text_color="gray50")
        badge2.pack(anchor="w", pady=(0, 4))

        f_vin = ctk.CTkFrame(c2, fg_color="transparent")
        f_vin.pack(fill="x", pady=4)
        e_vin = ctk.CTkEntry(f_vin, placeholder_text="Select video file...", height=36)
        e_vin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_vin, text="Browse Video...", height=36, command=lambda: self._browse_and_badge(e_vin, badge2, [("Video Files", "*.*")])).pack(side="right")

        f_vout = ctk.CTkFrame(c2, fg_color="transparent")
        f_vout.pack(fill="x", pady=4)
        e_vout = ctk.CTkEntry(f_vout, placeholder_text="Output audio path...", height=36)
        e_vout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_vout, text="Save As...", height=36, command=lambda: self._save_file(e_vout)).pack(side="right")

        log2 = ctk.CTkTextbox(c2, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log2.pack(fill="both", expand=True, pady=10)

        def on_ext_aud():
            vin = e_vin.get().strip().strip('"')
            vout = e_vout.get().strip().strip('"') or f"{os.path.splitext(vin)[0]}.mp3"
            self.run_task_async(extract_audio_from_video, log2, badge2, vin, vout)

        ctk.CTkButton(c2, text="Extract Audio", height=36, font=ctk.CTkFont(weight="bold"), command=on_ext_aud).pack(anchor="w")

        # Trim Audio
        c3 = ctk.CTkFrame(t_trim, fg_color="transparent")
        c3.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c3, text="Trim Audio Track (Cut by Start & Duration)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        f_tin = ctk.CTkFrame(c3, fg_color="transparent")
        f_tin.pack(fill="x", pady=4)
        e_tin = ctk.CTkEntry(f_tin, placeholder_text="Select audio...", height=36)
        e_tin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_tin, text="Browse...", height=36, command=lambda: self._browse_file(e_tin)).pack(side="right")

        f_topts = ctk.CTkFrame(c3, fg_color="transparent")
        f_topts.pack(fill="x", pady=6)
        ctk.CTkLabel(f_topts, text="Start (sec):").pack(side="left", padx=(0, 4))
        e_tstart = ctk.CTkEntry(f_topts, width=80, height=32)
        e_tstart.insert(0, "0")
        e_tstart.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_topts, text="Duration (sec):").pack(side="left", padx=(0, 4))
        e_tdur = ctk.CTkEntry(f_topts, width=80, height=32)
        e_tdur.insert(0, "30")
        e_tdur.pack(side="left")

        f_tout = ctk.CTkFrame(c3, fg_color="transparent")
        f_tout.pack(fill="x", pady=4)
        e_tout = ctk.CTkEntry(f_tout, placeholder_text="Output trimmed audio path...", height=36)
        e_tout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_tout, text="Save As...", height=36, command=lambda: self._save_file(e_tout)).pack(side="right")

        log3 = ctk.CTkTextbox(c3, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log3.pack(fill="both", expand=True, pady=10)

        def on_trim():
            inp = e_tin.get().strip().strip('"')
            out = e_tout.get().strip().strip('"') or f"{os.path.splitext(inp)[0]}_trimmed{os.path.splitext(inp)[1]}"
            self.run_task_async(trim_audio, log3, None, inp, out, e_tstart.get(), e_tdur.get())

        ctk.CTkButton(c3, text="Trim Audio", height=36, font=ctk.CTkFont(weight="bold"), command=on_trim).pack(anchor="w")

        return frame

    # ==========================================================================
    # VIEW 5: SMART FOLDER SORTER
    # ==========================================================================
    def build_sorter_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(frame, fg_color=("#ffffff", "#131a26"))
        card.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(card, text="🗂️ Automated Categorized Folder Organizer", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            card,
            text="Scans any directory and groups files into clean categories: Images (JPG/PNG), Documents (PDF/DOCX/PPT), Audio, Videos, Code & Archives.",
            font=ctk.CTkFont(size=12), text_color="gray50"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        f_in = ctk.CTkFrame(card, fg_color="transparent")
        f_in.pack(fill="x", padx=16, pady=4)
        e_dir = ctk.CTkEntry(f_in, placeholder_text="Select folder to organize (e.g. C:/Users/Downloads)...", height=38)
        e_dir.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_in, text="Browse Folder...", height=38, command=lambda: self._browse_folder(e_dir)).pack(side="right")

        f_opts = ctk.CTkFrame(card, fg_color="transparent")
        f_opts.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(f_opts, text="Organization Mode:").pack(side="left", padx=(0, 6))
        s_mode = ctk.CTkOptionMenu(
            f_opts,
            values=["Category & Subtype (Images/JPG, Docs/PDF)", "Extension Only (JPG, PDF)", "Category Only (Images, Documents)"],
            width=320,
            height=32
        )
        s_mode.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(f_opts, text="Action:").pack(side="left", padx=(0, 6))
        s_act = ctk.CTkOptionMenu(f_opts, values=["Move Files", "Copy Files"], width=120, height=32)
        s_act.pack(side="left")

        log = ctk.CTkTextbox(card, height=300, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log.pack(fill="both", expand=True, padx=16, pady=10)

        f_acts = ctk.CTkFrame(card, fg_color="transparent")
        f_acts.pack(fill="x", padx=16, pady=(0, 16))

        def parse_style():
            v = s_mode.get()
            if "Extension Only" in v:
                return "extension_only"
            if "Category Only" in v:
                return "category_only"
            return "category_and_extension"

        def on_preview():
            d = e_dir.get().strip().strip('"')
            if not d or not os.path.isdir(d):
                messagebox.showerror("Error", "Please select a valid folder.")
                return

            def worker():
                self.status_pill.configure(text="ANALYZING...", text_color="#38bdf8", fg_color="#0c4a6e")
                log.configure(state="normal")
                log.delete("0.0", "end")
                log.insert("end", f"Scanning: {d}...\n\n")
                res = analyze_folder(d, organize_style=parse_style())
                if res["success"]:
                    self.status_pill.configure(text="PREVIEW READY", text_color="#4ade80", fg_color="#14532d")
                    log.insert("end", f"Total files identified to organize: {res['total_files']}\n")
                    log.insert("end", "=" * 55 + "\n")
                    for cat, count in sorted(res["breakdown"].items()):
                        log.insert("end", f"  • {cat.ljust(30)} : {count} files\n")
                    log.insert("end", "=" * 55 + "\n")
                    log.insert("end", "[DRY RUN] No files have been touched yet.\n")
                    log.insert("end", "Click '🚀 Organize Folder Now' below to execute.\n")
                else:
                    self.status_pill.configure(text="ERROR", text_color="#f87171", fg_color="#7f1d1d")
                    log.insert("end", f"Error: {res['error']}\n")
                log.see("end")
                log.configure(state="disabled")

            threading.Thread(target=worker, daemon=True).start()

        def on_sort():
            d = e_dir.get().strip().strip('"')
            if not d or not os.path.isdir(d):
                messagebox.showerror("Error", "Please select a valid folder.")
                return

            act = "copy" if "Copy" in s_act.get() else "move"
            if not messagebox.askyesno("Confirm Organize", f"Are you sure you want to {act.upper()} files into categorized subfolders?"):
                return

            self.run_task_async(sort_folder, log, None, d, action=act, organize_style=parse_style(), dry_run=False)

        ctk.CTkButton(f_acts, text="🔍 Preview & Analyze", height=38, command=on_preview).pack(side="left", padx=(0, 10))
        ctk.CTkButton(f_acts, text="🚀 Organize Folder Now", fg_color="#16a34a", hover_color="#15803d", height=38, font=ctk.CTkFont(weight="bold"), command=on_sort).pack(side="left", padx=(0, 10))
        ctk.CTkButton(f_acts, text="Open Folder", fg_color="#334155", hover_color="#475569", height=38, command=lambda: self.open_in_explorer(e_dir.get())).pack(side="left")

        return frame

    # ==========================================================================
    # VIEW 6: EXTRA UTILITIES
    # ==========================================================================
    def build_extra_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        tabview = ctk.CTkTabview(frame, fg_color=("#ffffff", "#131a26"))
        tabview.pack(fill="both", expand=True)

        t_hash = tabview.add("🔒 File Hash")
        t_dup = tabview.add("👥 Duplicate Finder")
        t_ren = tabview.add("🏷️ Batch Renamer")
        t_qr = tabview.add("📱 QR Code Generator")

        # Hash
        c1 = ctk.CTkFrame(t_hash, fg_color="transparent")
        c1.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c1, text="Calculate Cryptographic File Checksums (SHA-256, MD5, SHA-1)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        f_hin = ctk.CTkFrame(c1, fg_color="transparent")
        f_hin.pack(fill="x", pady=4)
        e_hin = ctk.CTkEntry(f_hin, placeholder_text="Select file to hash...", height=36)
        e_hin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_hin, text="Browse...", height=36, command=lambda: self._browse_file(e_hin)).pack(side="right")

        f_hopts = ctk.CTkFrame(c1, fg_color="transparent")
        f_hopts.pack(fill="x", pady=6)
        ctk.CTkLabel(f_hopts, text="Algorithm:").pack(side="left", padx=(0, 6))
        halgo = ctk.CTkOptionMenu(f_hopts, values=["sha256", "md5", "sha1"], width=100)
        halgo.pack(side="left")

        log1 = ctk.CTkTextbox(c1, height=160, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log1.pack(fill="both", expand=True, pady=10)

        def on_hash():
            inp = e_hin.get().strip().strip('"')
            self.run_task_async(calculate_file_hash, log1, None, inp, halgo.get().lower())

        ctk.CTkButton(c1, text="Calculate Checksum", height=36, font=ctk.CTkFont(weight="bold"), command=on_hash).pack(anchor="w")

        # Duplicate Finder
        c2 = ctk.CTkFrame(t_dup, fg_color="transparent")
        c2.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c2, text="Scan Directory for Exact Duplicate Files (Binary SHA-256 Check)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        f_din = ctk.CTkFrame(c2, fg_color="transparent")
        f_din.pack(fill="x", pady=4)
        e_din = ctk.CTkEntry(f_din, placeholder_text="Select folder to scan...", height=36)
        e_din.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_din, text="Browse Folder...", height=36, command=lambda: self._browse_folder(e_din)).pack(side="right")

        log2 = ctk.CTkTextbox(c2, height=200, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log2.pack(fill="both", expand=True, pady=10)

        def on_scan_dup():
            d = e_din.get().strip().strip('"')
            def worker():
                self.status_pill.configure(text="SCANNING...", text_color="#38bdf8", fg_color="#0c4a6e")
                log2.configure(state="normal")
                log2.delete("0.0", "end")
                log2.insert("end", f"Scanning for duplicates in: {d}...\n")
                res = find_duplicate_files(d)
                if res["success"]:
                    self.status_pill.configure(text="DONE", text_color="#4ade80", fg_color="#14532d")
                    log2.insert("end", f"Duplicate groups found: {res['duplicate_groups_count']}\n")
                    wasted_mb = res['total_wasted_bytes'] / (1024 * 1024)
                    log2.insert("end", f"Total storage wasted: {wasted_mb:.2f} MB\n\n")
                    for idx, grp in enumerate(res["groups"], start=1):
                        log2.insert("end", f"Group {idx} ({grp['count']} duplicates, {format_bytes(grp['size_per_file'])} each):\n")
                        for fp in grp["files"]:
                            log2.insert("end", f"  • {fp}\n")
                        log2.insert("end", "\n")
                else:
                    self.status_pill.configure(text="ERROR", text_color="#f87171", fg_color="#7f1d1d")
                    log2.insert("end", f"Error: {res['error']}\n")
                log2.see("end")
                log2.configure(state="disabled")
            threading.Thread(target=worker, daemon=True).start()

        ctk.CTkButton(c2, text="🔍 Scan For Duplicates", height=36, font=ctk.CTkFont(weight="bold"), command=on_scan_dup).pack(anchor="w")

        # Batch Renamer
        c3 = ctk.CTkFrame(t_ren, fg_color="transparent")
        c3.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c3, text="Batch Rename Files with Prefix, Suffix, Replace & Numbering", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        f_rdin = ctk.CTkFrame(c3, fg_color="transparent")
        f_rdin.pack(fill="x", pady=4)
        e_rdin = ctk.CTkEntry(f_rdin, placeholder_text="Select folder...", height=36)
        e_rdin.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_rdin, text="Browse Folder...", height=36, command=lambda: self._browse_folder(e_rdin)).pack(side="right")

        f_ropts = ctk.CTkFrame(c3, fg_color="transparent")
        f_ropts.pack(fill="x", pady=6)
        e_pre = ctk.CTkEntry(f_ropts, width=120, height=32, placeholder_text="Prefix")
        e_pre.pack(side="left", padx=(0, 8))
        e_suf = ctk.CTkEntry(f_ropts, width=120, height=32, placeholder_text="Suffix")
        e_suf.pack(side="left", padx=(0, 8))
        e_find = ctk.CTkEntry(f_ropts, width=120, height=32, placeholder_text="Find")
        e_find.pack(side="left", padx=(0, 8))
        e_rep = ctk.CTkEntry(f_ropts, width=120, height=32, placeholder_text="Replace")
        e_rep.pack(side="left", padx=(0, 8))
        c_num = ctk.CTkCheckBox(f_ropts, text="Numbering (_001)")
        c_num.pack(side="left")

        log3 = ctk.CTkTextbox(c3, height=160, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log3.pack(fill="both", expand=True, pady=10)

        def on_ren(dry: bool):
            d = e_rdin.get().strip().strip('"')
            self.run_task_async(
                batch_rename_files, log3, None, d,
                prefix=e_pre.get().strip(),
                suffix=e_suf.get().strip(),
                find_str=e_find.get().strip(),
                replace_str=e_rep.get().strip(),
                add_numbering=c_num.get() == 1,
                dry_run=dry
            )

        f_ract = ctk.CTkFrame(c3, fg_color="transparent")
        f_ract.pack(fill="x")
        ctk.CTkButton(f_ract, text="Preview Renames", height=36, command=lambda: on_ren(True)).pack(side="left", padx=(0, 10))
        ctk.CTkButton(f_ract, text="Apply Rename", fg_color="#16a34a", hover_color="#15803d", height=36, font=ctk.CTkFont(weight="bold"), command=lambda: on_ren(False)).pack(side="left")

        # QR Code
        c4 = ctk.CTkFrame(t_qr, fg_color="transparent")
        c4.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(c4, text="Generate High-Resolution Offline QR Code Image", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        e_qrtxt = ctk.CTkEntry(c4, placeholder_text="Enter text, URL, WiFi credentials, or phone number...", height=38)
        e_qrtxt.pack(fill="x", pady=6)

        f_qrout = ctk.CTkFrame(c4, fg_color="transparent")
        f_qrout.pack(fill="x", pady=4)
        e_qrout = ctk.CTkEntry(f_qrout, placeholder_text="Save QR Image path (PNG)...", height=36)
        e_qrout.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(f_qrout, text="Save As...", height=36, command=lambda: self._save_file(e_qrout, [("PNG Image", "*.png")])).pack(side="right")

        log4 = ctk.CTkTextbox(c4, height=140, fg_color=("#f8fafc", "#080c14"), font=ctk.CTkFont(family="Consolas", size=11))
        log4.pack(fill="both", expand=True, pady=10)

        def on_qr():
            txt = e_qrtxt.get().strip()
            out = e_qrout.get().strip().strip('"') or "my_qrcode.png"
            self.run_task_async(generate_qr, log4, None, txt, out)

        ctk.CTkButton(c4, text="Generate QR Code Image", fg_color="#16a34a", hover_color="#15803d", height=36, font=ctk.CTkFont(weight="bold"), command=on_qr).pack(anchor="w")

        return frame

    # Helpers
    def _browse_file(self, entry: ctk.CTkEntry, filetypes=None):
        f = filedialog.askopenfilename(filetypes=filetypes or [("All Files", "*.*")])
        if f:
            entry.delete(0, "end")
            entry.insert(0, os.path.normpath(f))

    def _browse_and_badge(self, entry: ctk.CTkEntry, badge: ctk.CTkLabel, filetypes=None):
        self._browse_file(entry, filetypes)
        p = entry.get().strip()
        if p:
            self.update_file_meta_badge(p, badge)

    def _browse_folder(self, entry: ctk.CTkEntry):
        f = filedialog.askdirectory()
        if f:
            entry.delete(0, "end")
            entry.insert(0, os.path.normpath(f))

    def _save_file(self, entry: ctk.CTkEntry, filetypes=None):
        f = filedialog.asksaveasfilename(filetypes=filetypes or [("All Files", "*.*")])
        if f:
            entry.delete(0, "end")
            entry.insert(0, os.path.normpath(f))


def launch_gui():
    app = OmniToolsApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
