"""
OmniTools Studio Pro — Main Launcher
Supports:
  1. High-Spec Desktop GUI (default): python main.py
  2. Terminal UI (TUI):                python main.py --tui (or --cli)
  3. Direct Terminal Script Runner:    python cli.py <command>
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="OmniTools Studio Pro — 100% Offline Python Suite",
        add_help=False
    )
    parser.add_argument("--tui", "-t", action="store_true", help="Launch Terminal User Interface (TUI)")
    parser.add_argument("--cli", "-c", action="store_true", help="Launch Terminal User Interface")
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
  python main.py --tui       # Launches Terminal User Interface (TUI)
  python main.py --cli       # Launches Terminal User Interface
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
        from modules.handlers_bridge import HANDLERS
        import sys
        from pathlib import Path
        tui_dir = Path(__file__).parent / "omnitools_textual_tui_splash"
        if str(tui_dir) not in sys.path:
            sys.path.insert(0, str(tui_dir))
        from omnitools_tui.app import launch
        launch(
            handlers=HANDLERS,
            brand_name="Kesavaraj Samipillai",
            github_id="kesavarajsamipillai",
            show_splash=True
        )
    else:
        # Default: High-Spec Desktop GUI
        from modules.handlers_bridge import HANDLERS
        import sys
        from pathlib import Path
        ui_dir = Path(__file__).parent / "omnitools_ui_starter"
        if str(ui_dir) not in sys.path:
            sys.path.insert(0, str(ui_dir))
        from omnitools_ui.app import launch
        launch(handlers=HANDLERS)


if __name__ == "__main__":
    main()
