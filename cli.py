"""
OmniTools Offline CLI
Interactive Terminal Interface & Command-Line Runner
"""

import os
import sys
import argparse
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

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
    SUPPORTED_AUDIO_FORMATS
)
from modules.folder_sorter import analyze_folder, sort_folder
from modules.extra_tools import (
    calculate_file_hash, find_duplicate_files, batch_rename_files, generate_qr
)

console = Console()


def clean_path(p: str) -> str:
    """Strips quotes and whitespace often pasted into terminal."""
    return p.strip().strip('"').strip("'")


def show_banner():
    console.print(Panel.fit(
        "[bold cyan]🛠️  OmniTools Offline Suite (Terminal Edition)[/bold cyan]\n"
        "[italic green]100% Offline • High-Performance • No Internet Required[/italic green]",
        border_style="bright_blue"
    ))


# ==============================================================================
# SUBMENU HANDLERS (INTERACTIVE)
# ==============================================================================

def menu_pdf():
    while True:
        console.clear()
        show_banner()
        table = Table(title="📄 PDF Tools", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Tool Description", style="white")
        table.add_row("1", "🔓 Remove PDF Password (Unlock / Decrypt)")
        table.add_row("2", "🔒 Set PDF Password (Protect / Encrypt)")
        table.add_row("3", "📑 Merge Multiple PDFs into One")
        table.add_row("4", "✂️ Split PDF / Extract Pages")
        table.add_row("5", "🖼️ Convert PDF Pages to Images (PNG/JPG)")
        table.add_row("6", "📄 Convert Images to Single PDF")
        table.add_row("0", "⬅️ Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("\n[bold yellow]Select an option[/bold yellow]", default="0")
        if choice == "0":
            break

        if choice == "1":
            inp = clean_path(Prompt.ask("Enter encrypted PDF file path"))
            pwd = Prompt.ask("Enter PDF password (leave empty if none)", default="", password=True)
            default_out = os.path.splitext(inp)[0] + "_unlocked.pdf" if inp else ""
            out = clean_path(Prompt.ask("Enter output PDF path", default=default_out))
            with console.status("[bold green]Decrypting PDF...[/bold green]"):
                res = remove_pdf_password(inp, out, pwd)
            if res["success"]:
                console.print(f"[bold green]✓ Success![/bold green] Saved unlocked PDF: [cyan]{res['output']}[/cyan] ({res['pages']} pages)")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "2":
            inp = clean_path(Prompt.ask("Enter PDF file path"))
            pwd = Prompt.ask("Enter new password to set", password=True)
            default_out = os.path.splitext(inp)[0] + "_protected.pdf" if inp else ""
            out = clean_path(Prompt.ask("Enter output PDF path", default=default_out))
            with console.status("[bold green]Protecting PDF...[/bold green]"):
                res = set_pdf_password(inp, out, pwd)
            if res["success"]:
                console.print(f"[bold green]✓ Success![/bold green] Saved protected PDF: [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "3":
            console.print("[dim]Enter PDF paths separated by semicolons (;) or commas (,)[/dim]")
            inputs = Prompt.ask("PDF file paths")
            pdf_list = [clean_path(p) for p in inputs.replace(";", ",").split(",") if p.strip()]
            out = clean_path(Prompt.ask("Enter output merged PDF path"))
            with console.status("[bold green]Merging PDFs...[/bold green]"):
                res = merge_pdfs(pdf_list, out)
            if res["success"]:
                console.print(f"[bold green]✓ Merged {res['files_merged']} files ({res['total_pages']} pages):[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "4":
            inp = clean_path(Prompt.ask("Enter PDF file path"))
            out_folder = clean_path(Prompt.ask("Enter output folder"))
            ranges = Prompt.ask("Page ranges (e.g. '1-3, 5' or leave empty for all individual pages)", default="")
            with console.status("[bold green]Splitting PDF...[/bold green]"):
                res = split_pdf(inp, out_folder, ranges if ranges else None)
            if res["success"]:
                console.print(f"[bold green]✓ Successfully generated {res['count']} PDF files in:[/bold green] [cyan]{out_folder}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "5":
            inp = clean_path(Prompt.ask("Enter PDF file path"))
            out_folder = clean_path(Prompt.ask("Enter output images folder"))
            fmt = Prompt.ask("Image format (png / jpg / webp)", default="png")
            dpi = int(Prompt.ask("DPI resolution (e.g. 150, 200, 300)", default="200"))
            with console.status("[bold green]Rendering PDF pages to images...[/bold green]"):
                res = pdf_to_images(inp, out_folder, fmt, dpi)
            if res["success"]:
                console.print(f"[bold green]✓ Generated {res['count']} images in:[/bold green] [cyan]{out_folder}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "6":
            console.print("[dim]Enter image paths separated by semicolons (;) or commas (,)[/dim]")
            inputs = Prompt.ask("Image file paths")
            img_list = [clean_path(p) for p in inputs.replace(";", ",").split(",") if p.strip()]
            out = clean_path(Prompt.ask("Enter output PDF path"))
            with console.status("[bold green]Creating PDF from images...[/bold green]"):
                res = images_to_pdf(img_list, out)
            if res["success"]:
                console.print(f"[bold green]✓ Created PDF with {res['images_count']} images:[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")


def menu_docs():
    while True:
        console.clear()
        show_banner()
        table = Table(title="📝 Document Converter", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Tool Description", style="white")
        table.add_row("1", "📄 -> 📝 Convert PDF to Word DOCX")
        table.add_row("2", "📝 -> 📄 Convert Word DOCX to PDF")
        table.add_row("3", "📄 -> 📄 Convert Text (.txt) to Formatted PDF")
        table.add_row("0", "⬅️ Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("\n[bold yellow]Select an option[/bold yellow]", default="0")
        if choice == "0":
            break

        if choice == "1":
            inp = clean_path(Prompt.ask("Enter PDF file path"))
            default_out = os.path.splitext(inp)[0] + ".docx" if inp else ""
            out = clean_path(Prompt.ask("Enter output DOCX path", default=default_out))
            with console.status("[bold green]Converting PDF to DOCX...[/bold green]"):
                res = pdf_to_docx(inp, out)
            if res["success"]:
                console.print(f"[bold green]✓ Successfully converted to DOCX:[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "2":
            inp = clean_path(Prompt.ask("Enter DOCX file path"))
            default_out = os.path.splitext(inp)[0] + ".pdf" if inp else ""
            out = clean_path(Prompt.ask("Enter output PDF path", default=default_out))
            with console.status("[bold green]Converting DOCX to PDF...[/bold green]"):
                res = docx_to_pdf(inp, out)
            if res["success"]:
                engine_msg = f" (Engine: {res.get('engine')})" if 'engine' in res else ""
            Prompt.ask("\nPress Enter to continue")

        elif choice == "3":
            inp = clean_path(Prompt.ask("Enter TXT file path"))
            default_out = os.path.splitext(inp)[0] + ".pdf" if inp else ""
            out = clean_path(Prompt.ask("Enter output PDF path", default=default_out))
            with console.status("[bold green]Converting TXT to PDF...[/bold green]"):
                res = text_to_pdf(inp, out)
            if res["success"]:
                console.print(f"[bold green]✓ Successfully converted {res['lines_processed']} lines:[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")


def menu_images():
    while True:
        console.clear()
        show_banner()
        table = Table(title="🖼️ Image Converter & Processing", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Tool Description", style="white")
        table.add_row("1", "🔄 Convert Single Image (PNG, JPG, WEBP, BMP, GIF, TIFF, ICO)")
        table.add_row("2", "📁 Batch Convert Folder of Images")
        table.add_row("3", "📐 Resize Image (Percentage or Custom Dimensions)")
        table.add_row("4", "🗜️ Compress Image (Reduce File Size)")
        table.add_row("0", "⬅️ Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("\n[bold yellow]Select an option[/bold yellow]", default="0")
        if choice == "0":
            break

        if choice == "1":
            inp = clean_path(Prompt.ask("Enter input image path"))
            target_fmt = Prompt.ask(f"Target format ({'/'.join(SUPPORTED_IMAGE_FORMATS)})", default="jpg").lower()
            default_out = os.path.splitext(inp)[0] + f".{target_fmt}" if inp else ""
            out = clean_path(Prompt.ask("Enter output image path", default=default_out))
            quality = int(Prompt.ask("Quality (1-100)", default="95"))
            with console.status("[bold green]Converting image...[/bold green]"):
                res = convert_image(inp, out, target_fmt, quality=quality)
            if res["success"]:
                console.print(f"[bold green]✓ Image converted successfully:[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "2":
            inp_folder = clean_path(Prompt.ask("Enter input images folder"))
            target_fmt = Prompt.ask(f"Target format ({'/'.join(SUPPORTED_IMAGE_FORMATS)})", default="png").lower()
            out_folder = clean_path(Prompt.ask("Enter output folder", default=os.path.join(inp_folder, f"converted_{target_fmt}")))
            recursive = Confirm.ask("Include subfolders?", default=False)
            with console.status("[bold green]Batch converting images...[/bold green]"):
                res = batch_convert_images(inp_folder, out_folder, target_fmt, recursive=recursive)
            if res["success"]:
                console.print(f"[bold green]✓ Converted {res['converted_count']} of {res['total_found']} images to:[/bold green] [cyan]{out_folder}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "3":
            inp = clean_path(Prompt.ask("Enter input image path"))
            mode = Prompt.ask("Resize by: (1) Percentage (2) Dimensions WxH", choices=["1", "2"], default="1")
            default_out = os.path.splitext(inp)[0] + "_resized" + os.path.splitext(inp)[1]
            out = clean_path(Prompt.ask("Enter output image path", default=default_out))

            if mode == "1":
                pct = float(Prompt.ask("Percentage scale (e.g. 50 for 50%, 200 for 2x)", default="50"))
                res = resize_image(inp, out, scale_pct=pct)
            else:
                w = int(Prompt.ask("Target Width (px)"))
                h = int(Prompt.ask("Target Height (px)"))
                keep_aspect = Confirm.ask("Maintain aspect ratio?", default=True)
                res = resize_image(inp, out, width=w, height=h, maintain_aspect=keep_aspect)

            if res["success"]:
                console.print(f"[bold green]✓ Resized ({res['orig_size']} -> {res['new_size']}):[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "4":
            inp = clean_path(Prompt.ask("Enter image path to compress"))
            quality = int(Prompt.ask("Compression quality (10-90, lower = smaller file)", default="70"))
            default_out = os.path.splitext(inp)[0] + "_compressed" + os.path.splitext(inp)[1]
            out = clean_path(Prompt.ask("Enter output path", default=default_out))
            res = compress_image(inp, out, quality=quality)
            if res["success"]:
                console.print(f"[bold green]✓ Compressed ({res['orig_bytes']:,} B -> {res['new_bytes']:,} B, saved {res['saved_pct']}%):[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")


def menu_audio():
    while True:
        console.clear()
        show_banner()
        table = Table(title="🎵 Audio Converter & Video Extractor", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Tool Description", style="white")
        table.add_row("1", "🔄 Convert Single Audio File (MP3, WAV, AAC, FLAC, OGG, M4A, OPUS)")
        table.add_row("2", "📁 Batch Convert Audio Folder")
        table.add_row("3", "🎬 Extract Audio from Video (MP4, MKV, AVI -> MP3/WAV)")
        table.add_row("4", "✂️ Trim / Cut Audio File")
        table.add_row("0", "⬅️ Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("\n[bold yellow]Select an option[/bold yellow]", default="0")
        if choice == "0":
            break

        if choice == "1":
            inp = clean_path(Prompt.ask("Enter input audio path"))
            target_fmt = Prompt.ask(f"Target format ({'/'.join(SUPPORTED_AUDIO_FORMATS)})", default="mp3").lower()
            default_out = os.path.splitext(inp)[0] + f".{target_fmt}" if inp else ""
            out = clean_path(Prompt.ask("Enter output audio path", default=default_out))
            bitrate = Prompt.ask("Bitrate (e.g. 128k, 192k, 320k)", default="192k")
            with console.status("[bold green]Converting audio offline...[/bold green]"):
                res = convert_audio(inp, out, target_fmt, bitrate=bitrate)
            if res["success"]:
                console.print(f"[bold green]✓ Audio converted successfully:[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "2":
            inp_folder = clean_path(Prompt.ask("Enter audio folder"))
            target_fmt = Prompt.ask(f"Target format ({'/'.join(SUPPORTED_AUDIO_FORMATS)})", default="mp3").lower()
            out_folder = clean_path(Prompt.ask("Enter output folder", default=os.path.join(inp_folder, f"converted_{target_fmt}")))
            with console.status("[bold green]Batch converting audio files...[/bold green]"):
                res = batch_convert_audio(inp_folder, out_folder, target_fmt)
            if res["success"]:
                console.print(f"[bold green]✓ Converted {res['converted_count']} audio files to:[/bold green] [cyan]{out_folder}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "3":
            inp = clean_path(Prompt.ask("Enter video file path (MP4, MKV, AVI, etc.)"))
            target_fmt = Prompt.ask("Output audio format (mp3 / wav / aac)", default="mp3").lower()
            default_out = os.path.splitext(inp)[0] + f".{target_fmt}" if inp else ""
            out = clean_path(Prompt.ask("Enter output audio path", default=default_out))
            with console.status("[bold green]Extracting audio track from video...[/bold green]"):
                res = extract_audio_from_video(inp, out, target_fmt)
            if res["success"]:
                console.print(f"[bold green]✓ Audio soundtrack extracted:[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "4":
            inp = clean_path(Prompt.ask("Enter audio file path"))
            start = Prompt.ask("Start time (seconds or HH:MM:SS, e.g. 10 or 00:01:30)", default="0")
            dur = Prompt.ask("Duration in seconds (e.g. 30)", default="30")
            default_out = os.path.splitext(inp)[0] + "_trimmed" + os.path.splitext(inp)[1]
            out = clean_path(Prompt.ask("Enter output audio path", default=default_out))
            with console.status("[bold green]Trimming audio...[/bold green]"):
                res = trim_audio(inp, out, start, dur)
            if res["success"]:
                console.print(f"[bold green]✓ Audio trimmed successfully:[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")


def menu_sorter():
    while True:
        console.clear()
        show_banner()
        table = Table(title="🗂️ Smart Folder Sorter & Organizer", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Tool Description", style="white")
        table.add_row("1", "🔍 Analyze & Preview Folder (Dry-Run: see breakdown without touching files)")
        table.add_row("2", "🚀 Sort Folder (Move files into Images/JPG, Documents/PDF, Audio/MP3...)")
        table.add_row("3", "📋 Sort Folder by Copying (Keep original files safe)")
        table.add_row("0", "⬅️ Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("\n[bold yellow]Select an option[/bold yellow]", default="0")
        if choice == "0":
            break

        if choice in ("1", "2", "3"):
            folder = clean_path(Prompt.ask("Enter folder path to organize"))
            style_choice = Prompt.ask(
                "Organize style: [1] Category & Extension (Images/JPG) [2] Extension Only (JPG, PDF) [3] Category Only (Images, Documents)",
                choices=["1", "2", "3"],
                default="1"
            )
            style_map = {
                "1": "category_and_extension",
                "2": "extension_only",
                "3": "category_only"
            }
            organize_style = style_map[style_choice]

            # First show analysis table
            analysis = analyze_folder(folder, organize_style=organize_style)
            if not analysis["success"]:
                console.print(f"[bold red]✗ Error:[/bold red] {analysis['error']}")
                Prompt.ask("\nPress Enter to continue")
                continue

            stat_table = Table(title=f"Folder Analysis: {folder} ({analysis['total_files']} files found)")
            stat_table.add_column("Type / Category", style="cyan")
            stat_table.add_column("File Count", style="green", justify="right")
            for k, v in sorted(analysis["breakdown"].items()):
                stat_table.add_row(k, str(v))
            console.print(stat_table)

            if choice == "1":
                console.print("[dim]This was a dry-run preview. No files were modified.[/dim]")
                Prompt.ask("\nPress Enter to continue")
                continue

            action = "copy" if choice == "3" else "move"
            if not Confirm.ask(f"Ready to {action.upper()} {analysis['total_files']} files into organized folders?", default=True):
                continue

            with console.status(f"[bold green]Organizing files ({action})...[/bold green]"):
                res = sort_folder(folder, action=action, organize_style=organize_style)

            if res["success"]:
                console.print(f"[bold green]✓ Successfully organized {res['total_processed']} files![/bold green]")
                if res['failed_count'] > 0:
                    console.print(f"[yellow]⚠️ {res['failed_count']} files had issues.[/yellow]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")


def menu_extra():
    while True:
        console.clear()
        show_banner()
        table = Table(title="🧰 Extra Offline Utilities", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Tool Description", style="white")
        table.add_row("1", "🔒 Calculate File Hash (SHA-256 / MD5 / SHA-1)")
        table.add_row("2", "👥 Find Duplicate Files in Folder (Offline SHA-256 binary check)")
        table.add_row("3", "🏷️ Batch File Renamer (Prefix, Suffix, Replace, Numbering)")
        table.add_row("4", "📱 Offline QR Code Generator")
        table.add_row("0", "⬅️ Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("\n[bold yellow]Select an option[/bold yellow]", default="0")
        if choice == "0":
            break

        if choice == "1":
            inp = clean_path(Prompt.ask("Enter file path"))
            algo = Prompt.ask("Algorithm (sha256 / md5 / sha1)", default="sha256").lower()
            res = calculate_file_hash(inp, algo)
            if res["success"]:
                console.print(f"[bold green]Algorithm:[/bold green] {res['algorithm'].upper()}")
                console.print(f"[bold green]Hash Digest:[/bold green] [bold yellow]{res['hash']}[/bold yellow]")
                console.print(f"[bold green]File Size:[/bold green] {res['size_bytes']:,} bytes")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "2":
            folder = clean_path(Prompt.ask("Enter folder path to scan for duplicates"))
            with console.status("[bold green]Scanning files and calculating hashes...[/bold green]"):
                res = find_duplicate_files(folder)
            if res["success"]:
                dup_table = Table(title=f"Duplicate Report: {res['duplicate_groups_count']} duplicate sets found")
                dup_table.add_column("Group #", style="cyan")
                dup_table.add_column("Copies", style="magenta")
                dup_table.add_column("Size Each", style="green")
                dup_table.add_column("File Paths", style="white")

                for idx, grp in enumerate(res["groups"], start=1):
                    files_str = "\n".join(grp["files"])
                    dup_table.add_row(str(idx), str(grp["count"]), f"{grp['size_per_file']:,} B", files_str)

                console.print(dup_table)
                wasted_mb = res['total_wasted_bytes'] / (1024 * 1024)
                console.print(f"[bold yellow]Total duplicate storage wasted: {wasted_mb:.2f} MB[/bold yellow]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "3":
            folder = clean_path(Prompt.ask("Enter folder path containing files to rename"))
            prefix = Prompt.ask("Prefix to prepend (or empty)", default="")
            suffix = Prompt.ask("Suffix to append (or empty)", default="")
            find_str = Prompt.ask("Text to find (or empty)", default="")
            replace_str = Prompt.ask("Replace with (or empty)", default="")
            numbering = Confirm.ask("Add sequential numbering (_001, _002...)?", default=False)

            plan_res = batch_rename_files(
                folder, prefix=prefix, suffix=suffix, find_str=find_str,
                replace_str=replace_str, add_numbering=numbering, dry_run=True
            )

            if not plan_res["success"]:
                console.print(f"[bold red]✗ Error:[/bold red] {plan_res['error']}")
                Prompt.ask("\nPress Enter to continue")
                continue

            rename_table = Table(title=f"Rename Preview ({plan_res['total_to_rename']} files)")
            rename_table.add_column("Original Name", style="red")
            rename_table.add_column("→", style="yellow")
            rename_table.add_column("New Name", style="green")

            for item in plan_res["plan"][:15]:
                rename_table.add_row(item["old_name"], "→", item["new_name"])
            if len(plan_res["plan"]) > 15:
                rename_table.add_row("...", "...", f"(and {len(plan_res['plan']) - 15} more)")

            console.print(rename_table)

            if Confirm.ask("Apply these renames?", default=True):
                exec_res = batch_rename_files(
                    folder, prefix=prefix, suffix=suffix, find_str=find_str,
                    replace_str=replace_str, add_numbering=numbering, dry_run=False
                )
                console.print(f"[bold green]✓ Renamed {exec_res['renamed_count']} files successfully![/bold green]")
            Prompt.ask("\nPress Enter to continue")

        elif choice == "4":
            text = Prompt.ask("Enter text or URL to encode into QR code")
            out = clean_path(Prompt.ask("Enter output QR image path (PNG)", default="my_qrcode.png"))
            res = generate_qr(text, out)
            if res["success"]:
                console.print(f"[bold green]✓ Generated QR Code image:[/bold green] [cyan]{res['output']}[/cyan]")
            else:
                console.print(f"[bold red]✗ Error:[/bold red] {res['error']}")
            Prompt.ask("\nPress Enter to continue")


# ==============================================================================
# MAIN INTERACTIVE DISPATCHER
# ==============================================================================

def interactive_loop():
    while True:
        console.clear()
        show_banner()
        table = Table(title="Select a Tool Category", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="bold cyan", width=10)
        table.add_column("Included Utilities", style="white")

        table.add_row("[1] PDF", "Unlock PDF, Set Password, Merge, Split, PDF<->Images")
        table.add_row("[2] Docs", "PDF to Word (DOCX), Word (DOCX) to PDF, TXT to PDF")
        table.add_row("[3] Images", "Convert formats (PNG, JPG, WEBP, BMP, GIF, ICO), Batch, Resize, Compress")
        table.add_row("[4] Audio", "Convert formats (MP3, WAV, AAC, FLAC...), Extract from Video, Trim")
        table.add_row("[5] Sorter", "Sort Folder by Images (JPG/PNG), Audio, PDF, DOCX, PPT, Videos...")
        table.add_row("[6] Extra", "File Hashes, Duplicate Finder, Batch Renamer, QR Code")
        table.add_row("[0] Exit", "Quit OmniTools")
        console.print(table)

        choice = Prompt.ask("\n[bold yellow]Enter Category Number[/bold yellow]", default="0")
        if choice == "0":
            console.print("[bold cyan]Goodbye! Have a productive day.[/bold cyan]")
            break
        elif choice == "1":
            menu_pdf()
        elif choice == "2":
            menu_docs()
        elif choice == "3":
            menu_images()
        elif choice == "4":
            menu_audio()
        elif choice == "5":
            menu_sorter()
        elif choice == "6":
            menu_extra()


# ==============================================================================
# DIRECT COMMAND-LINE ARGUMENT PARSER
# ==============================================================================

def main():
    if len(sys.argv) == 1:
        interactive_loop()
        return

    parser = argparse.ArgumentParser(description="OmniTools Offline Suite CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # PDF Unlock
    p_un = subparsers.add_parser("pdf-unlock", help="Remove password from PDF")
    p_un.add_argument("--input", "-i", required=True)
    p_un.add_argument("--password", "-p", default="")
    p_un.add_argument("--output", "-o", required=True)

    # PDF Lock
    p_lk = subparsers.add_parser("pdf-lock", help="Encrypt PDF with password")
    p_lk.add_argument("--input", "-i", required=True)
    p_lk.add_argument("--password", "-p", required=True)
    p_lk.add_argument("--output", "-o", required=True)

    # PDF Merge
    p_mg = subparsers.add_parser("pdf-merge", help="Merge multiple PDFs")
    p_mg.add_argument("--inputs", "-i", nargs="+", required=True)
    p_mg.add_argument("--output", "-o", required=True)

    # PDF2DOCX
    p_p2d = subparsers.add_parser("pdf2docx", help="Convert PDF to Word DOCX")
    p_p2d.add_argument("--input", "-i", required=True)
    p_p2d.add_argument("--output", "-o", required=True)

    # DOCX2PDF
    p_d2p = subparsers.add_parser("docx2pdf", help="Convert Word DOCX to PDF")
    p_d2p.add_argument("--input", "-i", required=True)
    p_d2p.add_argument("--output", "-o", required=True)

    # Image Convert
    p_ic = subparsers.add_parser("img-convert", help="Convert single image")
    p_ic.add_argument("--input", "-i", required=True)
    p_ic.add_argument("--format", "-f", default=None)
    p_ic.add_argument("--output", "-o", required=True)
    p_ic.add_argument("--quality", "-q", type=int, default=95)

    # Image Batch
    p_ib = subparsers.add_parser("img-batch", help="Batch convert images in folder")
    p_ib.add_argument("--folder", "-i", required=True)
    p_ib.add_argument("--format", "-f", required=True)
    p_ib.add_argument("--output", "-o", required=True)
    p_ib.add_argument("--recursive", "-r", action="store_true")

    # Audio Convert
    p_ac = subparsers.add_parser("audio-convert", help="Convert audio file")
    p_ac.add_argument("--input", "-i", required=True)
    p_ac.add_argument("--format", "-f", default=None)
    p_ac.add_argument("--output", "-o", required=True)
    p_ac.add_argument("--bitrate", "-b", default="192k")

    # Extract Video Audio
    p_va = subparsers.add_parser("video-audio", help="Extract audio track from video")
    p_va.add_argument("--input", "-i", required=True)
    p_va.add_argument("--format", "-f", default="mp3")
    p_va.add_argument("--output", "-o", required=True)

    # Sort Folder
    p_sf = subparsers.add_parser("sort-folder", help="Sort folder by file types")
    p_sf.add_argument("--folder", "-i", required=True)
    p_sf.add_argument("--action", "-a", choices=["move", "copy"], default="move")
    p_sf.add_argument("--style", "-s", choices=["category_and_extension", "extension_only", "category_only"], default="category_and_extension")
    p_sf.add_argument("--dry-run", action="store_true")

    # Hash
    p_hs = subparsers.add_parser("hash", help="Calculate file hash")
    p_hs.add_argument("--input", "-i", required=True)
    p_hs.add_argument("--algo", "-a", default="sha256")

    # QR Code
    p_qr = subparsers.add_parser("qr", help="Generate QR code")
    p_qr.add_argument("--text", "-t", required=True)
    p_qr.add_argument("--output", "-o", required=True)

    args = parser.parse_args()

    if args.command == "pdf-unlock":
        res = remove_pdf_password(args.input, args.output, args.password)
        console.print(res)
    elif args.command == "pdf-lock":
        res = set_pdf_password(args.input, args.output, args.password)
        console.print(res)
    elif args.command == "pdf-merge":
        res = merge_pdfs(args.inputs, args.output)
        console.print(res)
    elif args.command == "pdf2docx":
        res = pdf_to_docx(args.input, args.output)
        console.print(res)
    elif args.command == "docx2pdf":
        res = docx_to_pdf(args.input, args.output)
        console.print(res)
    elif args.command == "img-convert":
        res = convert_image(args.input, args.output, args.format, quality=args.quality)
        console.print(res)
    elif args.command == "img-batch":
        res = batch_convert_images(args.folder, args.output, args.format, recursive=args.recursive)
        console.print(res)
    elif args.command == "audio-convert":
        res = convert_audio(args.input, args.output, args.format, bitrate=args.bitrate)
        console.print(res)
    elif args.command == "video-audio":
        res = extract_audio_from_video(args.input, args.output, args.format)
        console.print(res)
    elif args.command == "sort-folder":
        res = sort_folder(args.folder, action=args.action, organize_style=args.style, dry_run=args.dry_run)
        console.print(res)
    elif args.command == "hash":
        res = calculate_file_hash(args.input, args.algo)
        console.print(res)
    elif args.command == "qr":
        res = generate_qr(args.text, args.output)
        console.print(res)
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
