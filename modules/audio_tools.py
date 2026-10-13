"""
Audio Processing & Conversion Module (Completely Offline)
Features:
- Convert audio files between any formats (MP3, WAV, AAC, OGG, FLAC, M4A, WMA, OPUS)
- Batch audio format converter
- Extract audio soundtrack from videos (MP4, MKV, AVI, MOV, WEBM -> MP3/WAV/AAC)
- Audio trimmer (cut by start time and duration/end time)
- Audio volume booster / normalizer
"""

import os
import shutil
import subprocess
from typing import List, Optional

SUPPORTED_AUDIO_FORMATS = ["mp3", "wav", "aac", "ogg", "flac", "m4a", "wma", "opus"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"]


def get_ffmpeg_path() -> Optional[str]:
    """Finds ffmpeg executable in PATH, WinGet, or standard Windows locations."""
    for binary_name in ("ffmpeg", "ffmpeg.exe"):
        which_p = shutil.which(binary_name)
        if which_p and os.path.exists(which_p):
            return which_p

    # Check WinGet Links and Packages
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        winget_links = os.path.join(local_app, "Microsoft", "WinGet", "Links", "ffmpeg.exe")
        if os.path.islink(winget_links):
            try:
                target = os.readlink(winget_links)
                if target.startswith(r"\\?\\"):
                    target = target[4:]
                if os.path.exists(target):
                    return target
            except Exception:
                pass
        if os.path.exists(winget_links):
            return winget_links

        # Search WinGet packages directory for any ffmpeg.exe
        winget_pkgs = os.path.join(local_app, "Microsoft", "WinGet", "Packages")
        if os.path.isdir(winget_pkgs):
            for root, _, files in os.walk(winget_pkgs):
                if "ffmpeg.exe" in files:
                    found = os.path.join(root, "ffmpeg.exe")
                    if os.path.isfile(found):
                        return found

    candidates = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def convert_audio(
    input_file: str,
    output_file: str,
    target_format: Optional[str] = None,
    bitrate: str = "192k"
) -> dict:
    """Converts an audio file into target format using offline FFmpeg."""
    if not os.path.exists(input_file):
        return {"success": False, "error": f"Audio file not found: {input_file}"}

    ffmpeg_bin = get_ffmpeg_path()
    if not ffmpeg_bin:
        return {"success": False, "error": "FFmpeg executable was not found on your system."}

    if not target_format:
        ext = os.path.splitext(output_file)[1].lower().lstrip(".")
        target_format = ext if ext else "mp3"

    target_format = target_format.lower().lstrip(".")
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    cmd = [
        ffmpeg_bin,
        "-y",               # Overwrite output
        "-i", input_file,   # Input
    ]

    # Specific format codec mapping for best compatibility
    if target_format == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-b:a", bitrate])
    elif target_format == "aac":
        cmd.extend(["-c:a", "aac", "-b:a", bitrate])
    elif target_format == "ogg":
        cmd.extend(["-c:a", "libvorbis", "-q:a", "5"])
    elif target_format == "flac":
        cmd.extend(["-c:a", "flac"])
    elif target_format == "wav":
        cmd.extend(["-c:a", "pcm_s16le"])
    elif target_format == "opus":
        cmd.extend(["-c:a", "libopus", "-b:a", bitrate])
    elif target_format == "m4a":
        cmd.extend(["-c:a", "aac", "-b:a", bitrate])
    else:
        cmd.extend(["-b:a", bitrate])

    cmd.append(output_file)

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return {"success": False, "error": f"FFmpeg error: {proc.stderr[-300:]}"}
        return {"success": True, "output": output_file, "format": target_format}
    except Exception as e:
        return {"success": False, "error": str(e)}


def batch_convert_audio(
    input_folder: str,
    output_folder: str,
    target_format: str = "mp3",
    bitrate: str = "192k"
) -> dict:
    """Batch converts all audio files in a directory."""
    if not os.path.isdir(input_folder):
        return {"success": False, "error": f"Folder not found: {input_folder}"}

    target_format = target_format.lower().lstrip(".")
    valid_exts = tuple(f".{fmt}" for fmt in SUPPORTED_AUDIO_FORMATS)

    files = [f for f in os.listdir(input_folder) if f.lower().endswith(valid_exts)]
    os.makedirs(output_folder, exist_ok=True)

    converted = []
    failed = []

    for f in files:
        in_p = os.path.join(input_folder, f)
        base = os.path.splitext(f)[0]
        out_p = os.path.join(output_folder, f"{base}.{target_format}")

        res = convert_audio(in_p, out_p, target_format, bitrate=bitrate)
        if res["success"]:
            converted.append(out_p)
        else:
            failed.append({"file": f, "error": res["error"]})

    return {
        "success": True,
        "total_found": len(files),
        "converted_count": len(converted),
        "failed_count": len(failed),
        "converted": converted,
        "failed": failed
    }


def extract_audio_from_video(
    video_file: str,
    output_audio_file: str,
    target_format: str = "mp3",
    bitrate: str = "192k"
) -> dict:
    """Extracts the audio track from any video file."""
    if not os.path.exists(video_file):
        return {"success": False, "error": f"Video file not found: {video_file}"}

    ffmpeg_bin = get_ffmpeg_path()
    if not ffmpeg_bin:
        return {"success": False, "error": "FFmpeg executable not found."}

    os.makedirs(os.path.dirname(os.path.abspath(output_audio_file)), exist_ok=True)
    target_format = target_format.lower().lstrip(".")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", video_file,
        "-vn",  # Disable video stream
    ]

    if target_format == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-b:a", bitrate])
    elif target_format == "wav":
        cmd.extend(["-c:a", "pcm_s16le"])
    else:
        cmd.extend(["-c:a", "aac", "-b:a", bitrate])

    cmd.append(output_audio_file)

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return {"success": False, "error": f"FFmpeg error: {proc.stderr[-300:]}"}
        return {"success": True, "output": output_audio_file}
    except Exception as e:
        return {"success": False, "error": str(e)}


def trim_audio(input_file: str, output_file: str, start_time: str, duration_or_end: str, is_duration: bool = True) -> dict:
    """
    Trims an audio file.
    start_time: e.g. '00:00:10' or '10' (in seconds)
    duration_or_end: duration if is_duration=True, or end timestamp if False.
    """
    if not os.path.exists(input_file):
        return {"success": False, "error": f"File not found: {input_file}"}

    ffmpeg_bin = get_ffmpeg_path()
    if not ffmpeg_bin:
        return {"success": False, "error": "FFmpeg executable not found."}

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss", str(start_time),
        "-i", input_file,
    ]

    if is_duration:
        cmd.extend(["-t", str(duration_or_end)])
    else:
        cmd.extend(["-to", str(duration_or_end)])

    cmd.extend(["-c", "copy", output_file])

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return {"success": False, "error": f"FFmpeg error: {proc.stderr[-300:]}"}
        return {"success": True, "output": output_file}
    except Exception as e:
        return {"success": False, "error": str(e)}
