"""
OmniTools — Terminal User Interface (TUI)
A full-screen, keyboard & mouse-driven modern Terminal UI.
Powered by Textual.
"""

import os
import sys
import asyncio
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, Select, Label,
    TabbedContent, TabPane, RichLog, Checkbox
)
from textual.binding import Binding

import modules.pdf_tools as pdf_tools
import modules.doc_tools as doc_tools
import modules.image_tools as image_tools
import modules.audio_tools as audio_tools
import modules.folder_sorter as folder_sorter
import modules.extra_tools as extra_tools


TUI_CSS = """
Screen {
    background: #0f141c;
    color: #e2e8f0;
}

#header-box {
    dock: top;
    height: 3;
    background: #1a2233;
    color: #38bdf8;
    content-align: center middle;
    text-style: bold;
    border-bottom: heavy #38bdf8;
}

#main-container {
    height: 1fr;
    layout: horizontal;
}

#left-panel {
    width: 60%;
    height: 100%;
    border-right: tall #2a374f;
    padding: 1 2;
}

#right-panel {
    width: 40%;
    height: 100%;
    padding: 1;
    background: #0b0f17;
}

.card {
    background: #161f30;
    border: round #334155;
    padding: 1 2;
    margin-bottom: 1;
}

.title-label {
    text-style: bold;
    color: #38bdf8;
    margin-bottom: 1;
}

.field-label {
    color: #94a3b8;
    margin-top: 1;
}

Input {
    background: #0f172a;
    border: tall #475569;
    color: #f8fafc;
    margin-bottom: 1;
}

Input:focus {
    border: tall #38bdf8;
}

Select {
    background: #0f172a;
    border: tall #475569;
    color: #f8fafc;
    margin-bottom: 1;
}

Button {
    background: #2563eb;
    color: #ffffff;
    text-style: bold;
    border: none;
    margin-top: 1;
    margin-right: 1;
}

Button:hover {
    background: #3b82f6;
}

.btn-secondary {
    background: #334155;
    color: #e2e8f0;
}

.btn-secondary:hover {
    background: #475569;
}

.btn-success {
    background: #16a34a;
}

.btn-success:hover {
    background: #22c55e;
}

RichLog {
    height: 100%;
    background: #050810;
    border: round #1e293b;
    color: #cbd5e1;
}
"""


class OmniTuiApp(App):
    CSS = TUI_CSS
    TITLE = "⚡ OmniTools • Terminal UI"
    SUB_TITLE = "Offline High-Performance Toolkit"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "clear_log", "Clear Log", show=True),
        Binding("d", "toggle_dark", "Toggle Theme", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            with Vertical(id="left-panel"):
                with TabbedContent():
                    with TabPane("📄 PDF Hub", id="tab-pdf"):
                        yield from self.compose_pdf_pane()
                    with TabPane("📝 Doc Hub", id="tab-doc"):
                        yield from self.compose_doc_pane()
                    with TabPane("🖼️ Image Studio", id="tab-img"):
                        yield from self.compose_img_pane()
                    with TabPane("🎵 Audio Deck", id="tab-audio"):
                        yield from self.compose_audio_pane()
                    with TabPane("🗂️ Sorter", id="tab-sorter"):
                        yield from self.compose_sorter_pane()
                    with TabPane("🧰 Extras", id="tab-extras"):
                        yield from self.compose_extras_pane()

            with Vertical(id="right-panel"):
                yield Label("📟 Real-Time Execution Console", classes="title-label")
                yield RichLog(id="console-log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#console-log", RichLog)
        log.write("[bold cyan]====================================================[/bold cyan]")
        log.write("[bold green]⚡ Welcome to OmniTools — Terminal Edition ⚡[/bold green]")
        log.write("[dim]• 100% Offline • High-Performance • Pure Local Processing[/dim]")
        log.write("[dim]• Use Tab / Shift+Tab to navigate inputs, or click with mouse[/dim]")
        log.write("[bold cyan]====================================================[/bold cyan]\n")

    def action_clear_log(self) -> None:
        self.query_one("#console-log", RichLog).clear()

    # --------------------------------------------------------------------------
    # PANE BUILDERS
    # --------------------------------------------------------------------------
    def compose_pdf_pane(self):
        with ScrollableContainer():
            with Vertical(classes="card"):
                yield Label("🔓 Unlock Encrypted PDF", classes="title-label")
                yield Label("Input Encrypted PDF Path:", classes="field-label")
                yield Input(placeholder="Path to encrypted PDF...", id="pdf-unlock-in")
                yield Label("Password (leave blank if known empty):", classes="field-label")
                yield Input(placeholder="Password (e.g. KESA1998)", password=True, id="pdf-unlock-pwd")
                yield Label("Output PDF Path (optional):", classes="field-label")
                yield Input(placeholder="Output unlocked PDF path...", id="pdf-unlock-out")
                yield Button("Unlock PDF Now", id="btn-pdf-unlock", classes="btn-success")

            with Vertical(classes="card"):
                yield Label("📑 Merge Multiple PDFs", classes="title-label")
                yield Label("PDF Files (comma-separated paths):", classes="field-label")
                yield Input(placeholder="file1.pdf, file2.pdf, file3.pdf...", id="pdf-merge-in")
                yield Label("Output Merged PDF Path:", classes="field-label")
                yield Input(placeholder="merged_output.pdf", id="pdf-merge-out")
                yield Button("Merge PDFs", id="btn-pdf-merge")

    def compose_doc_pane(self):
        with ScrollableContainer():
            with Vertical(classes="card"):
                yield Label("📄 PDF to Word DOCX", classes="title-label")
                yield Label("Input PDF Path:", classes="field-label")
                yield Input(placeholder="Path to PDF...", id="doc-p2d-in")
                yield Label("Output DOCX Path:", classes="field-label")
                yield Input(placeholder="output.docx...", id="doc-p2d-out")
                yield Button("Convert to DOCX", id="btn-doc-p2d", classes="btn-success")

            with Vertical(classes="card"):
                yield Label("📝 Word DOCX to PDF", classes="title-label")
                yield Label("Input DOCX Path:", classes="field-label")
                yield Input(placeholder="Path to DOCX...", id="doc-d2p-in")
                yield Label("Output PDF Path:", classes="field-label")
                yield Input(placeholder="output.pdf...", id="doc-d2p-out")
                yield Button("Convert to PDF", id="btn-doc-d2p")

    def compose_img_pane(self):
        with ScrollableContainer():
            with Vertical(classes="card"):
                yield Label("🔄 Universal Image Converter", classes="title-label")
                yield Label("Input Image Path:", classes="field-label")
                yield Input(placeholder="Path to image...", id="img-in")
                yield Label("Target Format:", classes="field-label")
                yield Select(
                    [(fmt.upper(), fmt) for fmt in image_tools.SUPPORTED_IMAGE_FORMATS],
                    value="jpg", id="img-fmt"
                )
                yield Label("Output Image Path (optional):", classes="field-label")
                yield Input(placeholder="Converted output path...", id="img-out")
                yield Button("Convert Image", id="btn-img-conv", classes="btn-success")

            with Vertical(classes="card"):
                yield Label("📁 Batch Folder Image Converter", classes="title-label")
                yield Label("Images Folder:", classes="field-label")
                yield Input(placeholder="Folder path...", id="img-batch-in")
                yield Label("Target Format:", classes="field-label")
                yield Select(
                    [(fmt.upper(), fmt) for fmt in image_tools.SUPPORTED_IMAGE_FORMATS],
                    value="webp", id="img-batch-fmt"
                )
                yield Label("Output Folder:", classes="field-label")
                yield Input(placeholder="Output folder path...", id="img-batch-out")
                yield Button("Start Batch Conversion", id="btn-img-batch")

    def compose_audio_pane(self):
        with ScrollableContainer():
            with Vertical(classes="card"):
                yield Label("🔄 Audio Converter (Offline FFmpeg)", classes="title-label")
                yield Label("Input Audio Path:", classes="field-label")
                yield Input(placeholder="Path to audio (MP3, WAV, FLAC...)...", id="aud-in")
                yield Label("Target Format:", classes="field-label")
                yield Select(
                    [(fmt.upper(), fmt) for fmt in audio_tools.SUPPORTED_AUDIO_FORMATS],
                    value="mp3", id="aud-fmt"
                )
                yield Label("Output Audio Path (optional):", classes="field-label")
                yield Input(placeholder="Output path...", id="aud-out")
                yield Button("Convert Audio", id="btn-aud-conv", classes="btn-success")

            with Vertical(classes="card"):
                yield Label("🎬 Extract Audio from Video", classes="title-label")
                yield Label("Input Video Path (MP4, MKV, AVI...):", classes="field-label")
                yield Input(placeholder="Path to video...", id="aud-vid-in")
                yield Label("Output Audio Path:", classes="field-label")
                yield Input(placeholder="soundtrack.mp3", id="aud-vid-out")
                yield Button("Extract Soundtrack", id="btn-aud-vid")

    def compose_sorter_pane(self):
        with ScrollableContainer():
            with Vertical(classes="card"):
                yield Label("🗂️ Smart Folder Sorter", classes="title-label")
                yield Label("Target Directory to Organize:", classes="field-label")
                yield Input(placeholder="Folder path (e.g. C:/Users/Downloads)...", id="sort-in")
                yield Label("Organization Style:", classes="field-label")
                yield Select(
                    [
                        ("Category & Subtype (Images/JPG, Docs/PDF...)", "category_and_extension"),
                        ("Extension Only (JPG, PDF, MP3...)", "extension_only"),
                        ("Category Only (Images, Documents...)", "category_only"),
                    ],
                    value="category_and_extension", id="sort-style"
                )
                with Horizontal():
                    yield Button("🔍 Preview (Dry-Run)", id="btn-sort-preview", classes="btn-secondary")
                    yield Button("🚀 Sort Folder Now", id="btn-sort-exec", classes="btn-success")

    def compose_extras_pane(self):
        with ScrollableContainer():
            with Vertical(classes="card"):
                yield Label("🔒 Cryptographic File Hash", classes="title-label")
                yield Label("File Path:", classes="field-label")
                yield Input(placeholder="Path to file...", id="extra-hash-in")
                yield Label("Algorithm:", classes="field-label")
                yield Select([("SHA-256", "sha256"), ("MD5", "md5"), ("SHA-1", "sha1")], value="sha256", id="extra-hash-algo")
                yield Button("Calculate Hash", id="btn-extra-hash")

            with Vertical(classes="card"):
                yield Label("📱 Offline QR Code Generator", classes="title-label")
                yield Label("Content (Text / URL):", classes="field-label")
                yield Input(placeholder="Enter content...", id="extra-qr-in")
                yield Label("Output Image Path (PNG):", classes="field-label")
                yield Input(placeholder="my_qr.png", id="extra-qr-out")
                yield Button("Generate QR Code", id="btn-extra-qr", classes="btn-success")

    # --------------------------------------------------------------------------
    # BUTTON EVENT DISPATCHER
    # --------------------------------------------------------------------------
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        log = self.query_one("#console-log", RichLog)

        def log_info(msg: str):
            log.write(f"[cyan][INFO][/cyan] {msg}")

        def log_success(msg: str):
            log.write(f"[bold green][SUCCESS][/bold green] {msg}")

        def log_error(msg: str):
            log.write(f"[bold red][ERROR][/bold red] {msg}")

        # PDF Unlock
        if btn_id == "btn-pdf-unlock":
            inp = self.query_one("#pdf-unlock-in", Input).value.strip().strip('"')
            pwd = self.query_one("#pdf-unlock-pwd", Input).value
            out = self.query_one("#pdf-unlock-out", Input).value.strip().strip('"') or (os.path.splitext(inp)[0] + "_unlocked.pdf")
            log_info(f"Unlocking PDF: {inp}...")
            res = await asyncio.to_thread(pdf_tools.remove_pdf_password, inp, out, pwd)
            if res["success"]:
                log_success(f"Unlocked! Saved to: [bold white]{res['output']}[/bold white] ({res['pages']} pages)")
            else:
                log_error(res["error"])

        # PDF Merge
        elif btn_id == "btn-pdf-merge":
            raw_in = self.query_one("#pdf-merge-in", Input).value
            files = [p.strip().strip('"') for p in raw_in.split(",") if p.strip()]
            out = self.query_one("#pdf-merge-out", Input).value.strip().strip('"')
            log_info(f"Merging {len(files)} PDFs...")
            res = await asyncio.to_thread(pdf_tools.merge_pdfs, files, out)
            if res["success"]:
                log_success(f"Merged {res['files_merged']} files ({res['total_pages']} pages) -> {res['output']}")
            else:
                log_error(res["error"])

        # Doc P2D
        elif btn_id == "btn-doc-p2d":
            inp = self.query_one("#doc-p2d-in", Input).value.strip().strip('"')
            out = self.query_one("#doc-p2d-out", Input).value.strip().strip('"') or (os.path.splitext(inp)[0] + ".docx")
            log_info(f"Converting PDF to Word DOCX: {inp}...")
            res = await asyncio.to_thread(doc_tools.pdf_to_docx, inp, out)
            if res["success"]:
                log_success(f"DOCX created: {res['output']}")
            else:
                log_error(res["error"])

        # Doc D2P
        elif btn_id == "btn-doc-d2p":
            inp = self.query_one("#doc-d2p-in", Input).value.strip().strip('"')
            out = self.query_one("#doc-d2p-out", Input).value.strip().strip('"') or (os.path.splitext(inp)[0] + ".pdf")
            log_info(f"Converting DOCX to PDF: {inp}...")
            res = await asyncio.to_thread(doc_tools.docx_to_pdf, inp, out)
            if res["success"]:
                log_success(f"PDF created ({res.get('engine', 'OK')}): {res['output']}")
            else:
                log_error(res["error"])

        # Image Convert
        elif btn_id == "btn-img-conv":
            inp = self.query_one("#img-in", Input).value.strip().strip('"')
            fmt = str(self.query_one("#img-fmt", Select).value)
            out = self.query_one("#img-out", Input).value.strip().strip('"') or f"{os.path.splitext(inp)[0]}.{fmt}"
            log_info(f"Converting image to {fmt.upper()}...")
            res = await asyncio.to_thread(image_tools.convert_image, inp, out, fmt)
            if res["success"]:
                log_success(f"Image converted: {res['output']}")
            else:
                log_error(res["error"])

        # Image Batch
        elif btn_id == "btn-img-batch":
            inp = self.query_one("#img-batch-in", Input).value.strip().strip('"')
            fmt = str(self.query_one("#img-batch-fmt", Select).value)
            out = self.query_one("#img-batch-out", Input).value.strip().strip('"') or os.path.join(inp, f"converted_{fmt}")
            log_info(f"Batch converting images in {inp} to {fmt.upper()}...")
            res = await asyncio.to_thread(image_tools.batch_convert_images, inp, out, fmt)
            if res["success"]:
                log_success(f"Converted {res['converted_count']} of {res['total_found']} images to: {out}")
            else:
                log_error(res["error"])

        # Audio Convert
        elif btn_id == "btn-aud-conv":
            inp = self.query_one("#aud-in", Input).value.strip().strip('"')
            fmt = str(self.query_one("#aud-fmt", Select).value)
            out = self.query_one("#aud-out", Input).value.strip().strip('"') or f"{os.path.splitext(inp)[0]}.{fmt}"
            log_info(f"Converting audio to {fmt.upper()} (via offline FFmpeg)...")
            res = await asyncio.to_thread(audio_tools.convert_audio, inp, out, fmt)
            if res["success"]:
                log_success(f"Audio converted: {res['output']}")
            else:
                log_error(res["error"])

        # Audio Extract from Video
        elif btn_id == "btn-aud-vid":
            inp = self.query_one("#aud-vid-in", Input).value.strip().strip('"')
            out = self.query_one("#aud-vid-out", Input).value.strip().strip('"') or f"{os.path.splitext(inp)[0]}.mp3"
            log_info(f"Extracting audio track from: {inp}...")
            res = await asyncio.to_thread(audio_tools.extract_audio_from_video, inp, out)
            if res["success"]:
                log_success(f"Audio extracted: {res['output']}")
            else:
                log_error(res["error"])

        # Sorter Preview
        elif btn_id == "btn-sort-preview":
            folder = self.query_one("#sort-in", Input).value.strip().strip('"')
            style = str(self.query_one("#sort-style", Select).value)
            log_info(f"Scanning & analyzing directory: {folder}...")
            res = await asyncio.to_thread(folder_sorter.analyze_folder, folder, organize_style=style)
            if res["success"]:
                log_success(f"Analysis complete: {res['total_files']} files found.")
                for cat, count in sorted(res["breakdown"].items()):
                    log.write(f"  • [yellow]{cat.ljust(28)}[/yellow] : [bold green]{count}[/bold green] files")
                log.write("[dim]Dry run only. Click 'Sort Folder Now' to move files.[/dim]")
            else:
                log_error(res["error"])

        # Sorter Execute
        elif btn_id == "btn-sort-exec":
            folder = self.query_one("#sort-in", Input).value.strip().strip('"')
            style = str(self.query_one("#sort-style", Select).value)
            log_info(f"Organizing files into structured subfolders in: {folder}...")
            res = await asyncio.to_thread(folder_sorter.sort_folder, folder, action="move", organize_style=style)
            if res["success"]:
                log_success(f"Organized {res['total_processed']} files cleanly!")
            else:
                log_error(res["error"])

        # Extras Hash
        elif btn_id == "btn-extra-hash":
            inp = self.query_one("#extra-hash-in", Input).value.strip().strip('"')
            algo = str(self.query_one("#extra-hash-algo", Select).value)
            log_info(f"Calculating {algo.upper()} checksum...")
            res = await asyncio.to_thread(extra_tools.calculate_file_hash, inp, algo)
            if res["success"]:
                log_success(f"{algo.upper()}: [bold yellow]{res['hash']}[/bold yellow] ({res['size_bytes']:,} bytes)")
            else:
                log_error(res["error"])

        # Extras QR
        elif btn_id == "btn-extra-qr":
            txt = self.query_one("#extra-qr-in", Input).value.strip()
            out = self.query_one("#extra-qr-out", Input).value.strip().strip('"') or "my_qr.png"
            log_info(f"Generating QR Code...")
            res = await asyncio.to_thread(extra_tools.generate_qr, txt, out)
            if res["success"]:
                log_success(f"QR image created: {res['output']}")
            else:
                log_error(res["error"])


def launch_tui():
    app = OmniTuiApp()
    app.run()


if __name__ == "__main__":
    launch_tui()
