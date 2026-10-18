# ⚡ OmniTools — 100% Offline Python Suite

[![GitHub Release](https://img.shields.io/badge/release-v1.1.0-blue.svg)](https://github.com/kesavarajsamipillai/Omni-Tools/releases)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Author](https://img.shields.io/badge/created%20by-Kesavaraj%20Samipillai-orange.svg)](https://github.com/kesavarajsamipillai)

A complete, high-performance, **completely offline** desktop & terminal toolkit for file conversion, security, organization, and audio/image processing. Pure local execution — zero cloud reliance, 100% privacy.

---

## 🌟 Key Features

| Category | Offline Tools Included |
| :--- | :--- |
| **📄 PDF Tools** | • Unlock encrypted PDFs (remove known passwords)<br>• Protect/Encrypt PDFs with passwords<br>• Merge multiple PDFs into one<br>• Split PDFs or extract custom page ranges<br>• Convert PDF pages into high-res images (PNG/JPG/WEBP)<br>• Combine images into a single PDF |
| **📝 Document Converter** | • Convert PDF to editable Word DOCX (`pdf2docx`)<br>• Convert Word DOCX to PDF (`docx2pdf` + ReportLab fallback)<br>• Convert Plain Text (`.txt`) to clean PDF |
| **🖼️ Universal Image Converter** | • Universal conversion across **PNG, JPG/JPEG, WEBP, BMP, GIF, TIFF, ICO**<br>• Handles alpha transparency cleanly (RGBA to RGB with white canvas)<br>• Batch convert entire folders of images<br>• Image Resizer (by percentage or custom dimensions with aspect lock)<br>• Image Compressor (reduce file size) |
| **🎵 Audio & Video Tools** | • Convert audio formats (**MP3, WAV, AAC, FLAC, OGG, M4A, OPUS**)<br>• Batch convert audio folders<br>• Extract audio soundtrack from videos (**MP4, MKV, AVI** &rarr; MP3/WAV)<br>• Audio Trimmer (cut by start time and duration) |
| **🗂️ Smart Folder Sorter** | • Automatically sort folders into neat categories and subfolders:<br>  - `Images/JPG`, `Images/PNG`, `Images/WEBP`...<br>  - `Documents/PDF`, `Documents/DOCX`, `Documents/PPTX`...<br>  - `Audio/MP3`, `Audio/WAV`...<br>  - `Videos/MP4`, `Videos/MKV`...<br>  - `Archives/ZIP`, `Archives/RAR`...<br>  - `Code & Data/Python`, `Code & Data/JSON`...<br>• **Dry-Run Preview**: Inspect breakdown before moving files<br>• **Collision Safety**: Never overwrites files with identical names |
| **🧰 Extra Utilities** | • Cryptographic File Hash Calculator (SHA-256, MD5, SHA-1)<br>• Offline Duplicate File Finder (fast 2-tier size & hash match)<br>• Batch File Renamer (prefix, suffix, find & replace, sequential numbering)<br>• Offline QR Code Generator |

---

## 🚀 Quick Setup & Commands

Anyone cloning or downloading this repository can install the command once via:
```bash
pip install -e .
```
After that, the `omni-tools` command is available everywhere on the system:

### 1. Launch Terminal UI (TUI)
```bash
omni-tools -tui
```
*(Or double-click `run_cli.bat`)*

### 2. Launch Desktop Application (GUI)
```bash
omni-tools
# or
omni-tools -gui
```
*(Or double-click `run_gui.bat`)*

### 3. Direct Command-Line Execution
You can also run commands directly in scripts or terminal:

```bash
# Unlock PDF
python cli.py pdf-unlock -i input.pdf -p password123 -o unlocked.pdf

# Protect PDF
python cli.py pdf-lock -i input.pdf -p secret123 -o protected.pdf

# Merge PDFs
python cli.py pdf-merge -i file1.pdf file2.pdf -o merged.pdf

# Convert PDF to Word
python cli.py pdf2docx -i report.pdf -o report.docx

# Convert Word to PDF
python cli.py docx2pdf -i document.docx -o document.pdf

# Convert image format
python cli.py img-convert -i photo.png -f jpg -o photo.jpg

# Batch convert folder of images
python cli.py img-batch -i ./my_photos -f webp -o ./webp_photos

# Convert audio format
python cli.py audio-convert -i song.wav -f mp3 -o song.mp3

# Extract audio from video
python cli.py video-audio -i movie.mp4 -f mp3 -o soundtrack.mp3

# Preview sorting a folder (Dry run)
python cli.py sort-folder -i ./Downloads --dry-run

# Organize a folder (Move into Images/JPG, Documents/PDF, etc.)
python cli.py sort-folder -i ./Downloads -a move

# Generate QR code
python cli.py qr -t "https://example.com" -o qr.png

# Calculate file hash
python cli.py hash -i installer.exe --algo sha256
```

---

## 🔒 100% Offline & Private Guarantee
- **No API keys or cloud services required.**
- **No data leaves your local machine.**
- All processing is done locally via Python libraries and your local `ffmpeg` installation.
