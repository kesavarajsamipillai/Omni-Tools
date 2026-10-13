"""
OmniTools Studio Pro — Main Launcher
Supports:
  1. High-Spec Desktop GUI (default): python main.py
  2. Moviebox-TUI Terminal UI:         python main.py --tui (or --cli)
  3. Direct Terminal Script Runner:    python cli.py <command>
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="OmniTools Studio Pro — 100% Offline Python Suite",
        add_help=False
    )
    parser.add_argument("--tui", "-t", action="store_true", help="Launch Moviebox-style Terminal User Interface")
    parser.add_argument("--cli", "-c", action="store_true", help="Launch Moviebox Terminal User Interface")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch High-Spec Desktop Application GUI")
    parser.add_argument("--help", "-h", action="store_true", help="Show help information")

    args, unknown = parser.parse_known_args()

    if args.help:
        print("""
==============================================================
         ⚡ OmniTools Studio Pro — 100% Offline ⚡
==============================================================
Usage:
  python main.py             # Launches Modern Desktop Application GUI (Default)
  python main.py --tui       # Launches Moviebox-style Terminal TUI
  python main.py --cli       # Launches Moviebox-style Terminal TUI
  python cli.py <command>    # Direct Terminal CLI Runner

Direct CLI Commands:
  python cli.py pdf-unlock -i input.pdf -p password -o out.pdf
  python cli.py pdf-lock -i input.pdf -p password -o out.pdf
  python cli.py pdf-merge -i doc1.pdf doc2.pdf -o merged.pdf
  python cli.py pdf2docx -i doc.pdf -o doc.docx
  python cli.py docx2pdf -i doc.docx -o doc.pdf
  python cli.py img-convert -i img.png -f jpg -o img.jpg
  python cli.py img-batch -i ./images -f webp -o ./out
  python cli.py audio-convert -i song.wav -f mp3 -o song.mp3
  python cli.py video-audio -i video.mp4 -o audio.mp3
  python cli.py sort-folder -i ./Downloads --dry-run
  python cli.py hash -i file.iso --algo sha256
  python cli.py qr -t "Hello" -o qr.png
""")
        return

    # Check for direct CLI subcommands
    if unknown and unknown[0] in [
        "pdf-unlock", "pdf-lock", "pdf-merge", "pdf2docx", "docx2pdf",
        "img-convert", "img-batch", "audio-convert", "video-audio",
        "sort-folder", "hash", "qr"
    ]:
        import cli
        cli.main()
    elif args.tui or args.cli:
        import tui_app
        tui_app.launch_tui()
    else:
        # Default: High-Spec Desktop GUI
        import app_gui
        app_gui.launch_gui()


if __name__ == "__main__":
    main()
