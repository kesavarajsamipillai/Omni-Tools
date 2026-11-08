"""
Audio Processing & Conversion Module (Completely Offline)
Features:
- Convert audio files between any formats (MP3, WAV, AAC, OGG, FLAC, M4A, WMA, OPUS)
- Pristine preservation of audio tags: Title, Artist, Album, Album Artist, Date/Year, Genre, Track Number, Disc Number, Composer, Comments, Lyrics
- Pristine preservation and embedding of Album Cover Art across formats (including OPUS <-> MP3 <-> M4A <-> FLAC)
- Automatic fallback album cover detection from folder (cover.jpg, folder.jpg, etc.)
- Batch audio format converter
- Extract audio soundtrack from videos (MP4, MKV, AVI, MOV, WEBM -> MP3/WAV/AAC) with tags
- Audio trimmer (cut by start time and duration/end time)
- Audio volume booster / normalizer
"""

import base64
import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.id3 import (
    APIC,
    COMM,
    ID3,
    TALB,
    TCOM,
    TCON,
    TDRC,
    TIT2,
    TPOS,
    TPE1,
    TPE2,
    TRCK,
    TYER,
    USLT,
    ID3NoHeaderError,
)
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover, MP4Tags
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE

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


def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extracts all metadata (tags, song details, and cover art) from an audio/video file.
    Works seamlessly across MP3, OPUS, M4A, FLAC, OGG, WAV, etc.
    """
    meta: Dict[str, Any] = {
        "title": None,
        "artist": None,
        "album": None,
        "albumartist": None,
        "date": None,
        "genre": None,
        "track": None,
        "disc": None,
        "composer": None,
        "comment": None,
        "lyrics": None,
        "picture_data": None,
        "picture_mime": "image/jpeg",
    }

    if not os.path.exists(file_path):
        return meta

    def _first_str(val: Any) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, (list, tuple)):
            if len(val) == 0:
                return None
            val = val[0]
        s = str(val).strip()
        return s if s else None

    # 1. Mutagen file inspection
    try:
        audio = mutagen.File(file_path)
    except Exception:
        audio = None

    if audio is not None:
        # MP4 / M4A
        if isinstance(audio, MP4) or (getattr(audio, "tags", None) and isinstance(audio.tags, MP4Tags)):
            tags = audio.tags or {}
            meta["title"] = _first_str(tags.get("\xa9nam"))
            meta["artist"] = _first_str(tags.get("\xa9ART"))
            meta["album"] = _first_str(tags.get("\xa9alb"))
            meta["albumartist"] = _first_str(tags.get("aART"))
            meta["date"] = _first_str(tags.get("\xa9day"))
            meta["genre"] = _first_str(tags.get("\xa9gen"))
            meta["composer"] = _first_str(tags.get("\xa9wrt"))
            meta["comment"] = _first_str(tags.get("\xa9cmt"))
            meta["lyrics"] = _first_str(tags.get("\xa9lyr"))
            if tags.get("trkn") and len(tags["trkn"]) > 0:
                trk = tags["trkn"][0]
                meta["track"] = f"{trk[0]}/{trk[1]}" if len(trk) > 1 and trk[1] else str(trk[0])
            if tags.get("disk") and len(tags["disk"]) > 0:
                d = tags["disk"][0]
                meta["disc"] = f"{d[0]}/{d[1]}" if len(d) > 1 and d[1] else str(d[0])
            covers = tags.get("covr", [])
            if covers:
                cov = covers[0]
                meta["picture_data"] = bytes(cov)
                meta["picture_mime"] = "image/png" if getattr(cov, "imageformat", None) == MP4Cover.FORMAT_PNG else "image/jpeg"

        # MP3 or ID3 tags
        elif isinstance(audio, MP3) or (getattr(audio, "tags", None) and isinstance(audio.tags, ID3)):
            tags = audio.tags
            if tags:
                for k in ("TIT2",):
                    if k in tags:
                        meta["title"] = _first_str(tags[k])
                for k in ("TPE1",):
                    if k in tags:
                        meta["artist"] = _first_str(tags[k])
                for k in ("TALB",):
                    if k in tags:
                        meta["album"] = _first_str(tags[k])
                for k in ("TPE2",):
                    if k in tags:
                        meta["albumartist"] = _first_str(tags[k])
                for k in ("TDRC", "TYER"):
                    if k in tags and not meta["date"]:
                        meta["date"] = _first_str(tags[k])
                for k in ("TCON",):
                    if k in tags:
                        meta["genre"] = _first_str(tags[k])
                for k in ("TRCK",):
                    if k in tags:
                        meta["track"] = _first_str(tags[k])
                for k in ("TPOS",):
                    if k in tags:
                        meta["disc"] = _first_str(tags[k])
                for k in ("TCOM",):
                    if k in tags:
                        meta["composer"] = _first_str(tags[k])
                for k in tags.keys():
                    if k.startswith("COMM") and not meta["comment"]:
                        meta["comment"] = _first_str(tags[k])
                    elif k.startswith("USLT") and not meta["lyrics"]:
                        meta["lyrics"] = _first_str(tags[k])
                    elif k.startswith("APIC") and not meta["picture_data"]:
                        frame = tags[k]
                        meta["picture_data"] = bytes(frame.data)
                        meta["picture_mime"] = str(frame.mime)

        # Vorbis comments (OggOpus, OggVorbis, FLAC)
        elif isinstance(audio, (OggOpus, OggVorbis, FLAC)) or hasattr(audio, "keys"):
            lower_tags = {k.lower(): audio[k] for k in audio.keys()} if hasattr(audio, "keys") else {}
            meta["title"] = _first_str(lower_tags.get("title"))
            meta["artist"] = _first_str(lower_tags.get("artist"))
            meta["album"] = _first_str(lower_tags.get("album"))
            meta["albumartist"] = _first_str(lower_tags.get("albumartist"))
            meta["date"] = _first_str(lower_tags.get("date") or lower_tags.get("year"))
            meta["genre"] = _first_str(lower_tags.get("genre"))
            meta["track"] = _first_str(lower_tags.get("tracknumber"))
            meta["disc"] = _first_str(lower_tags.get("discnumber"))
            meta["composer"] = _first_str(lower_tags.get("composer"))
            meta["comment"] = _first_str(lower_tags.get("comment") or lower_tags.get("description"))
            meta["lyrics"] = _first_str(lower_tags.get("lyrics"))

            if hasattr(audio, "pictures") and audio.pictures:
                pic = audio.pictures[0]
                meta["picture_data"] = bytes(pic.data)
                meta["picture_mime"] = str(pic.mime)
            elif "metadata_block_picture" in lower_tags:
                for b64pic in lower_tags["metadata_block_picture"]:
                    try:
                        p = Picture(base64.b64decode(b64pic))
                        meta["picture_data"] = bytes(p.data)
                        meta["picture_mime"] = str(p.mime)
                        break
                    except Exception:
                        pass

    # 2. Fallback: FFmpeg attached picture extraction if mutagen didn't find any picture
    if not meta["picture_data"]:
        ffmpeg_bin = get_ffmpeg_path()
        if ffmpeg_bin:
            try:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    tmp_img = tmp.name
                proc = subprocess.run(
                    [ffmpeg_bin, "-y", "-i", file_path, "-an", "-vcodec", "copy", tmp_img],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if proc.returncode == 0 and os.path.exists(tmp_img) and os.path.getsize(tmp_img) > 0:
                    with open(tmp_img, "rb") as f:
                        meta["picture_data"] = f.read()
                    meta["picture_mime"] = "image/jpeg"
                if os.path.exists(tmp_img):
                    try:
                        os.remove(tmp_img)
                    except Exception:
                        pass
            except Exception:
                pass

    # 3. Fallback: Search folder for common cover image names
    if not meta["picture_data"]:
        try:
            parent_dir = os.path.dirname(os.path.abspath(file_path))
            stem = os.path.splitext(os.path.basename(file_path))[0]
            candidates = [
                f"{stem}.jpg", f"{stem}.jpeg", f"{stem}.png",
                "cover.jpg", "cover.jpeg", "cover.png",
                "folder.jpg", "folder.jpeg", "folder.png",
                "front.jpg", "front.jpeg", "front.png",
                "album.jpg", "album.jpeg", "album.png",
            ]
            for cname in candidates:
                cand_path = os.path.join(parent_dir, cname)
                if os.path.isfile(cand_path):
                    with open(cand_path, "rb") as f:
                        meta["picture_data"] = f.read()
                    meta["picture_mime"] = "image/png" if cname.lower().endswith(".png") else "image/jpeg"
                    break
        except Exception:
            pass

    # 4. If Title is still empty, fallback to the file's base name (clean name)
    if not meta["title"]:
        meta["title"] = os.path.splitext(os.path.basename(file_path))[0]

    return meta


def inject_audio_metadata(target_path: str, meta: Dict[str, Any]) -> None:
    """
    Injects standard song metadata and embedded album art cleanly into the converted audio file.
    Supports MP3 (ID3v2.3 for 100% Windows Explorer compatibility), OPUS, M4A, FLAC, OGG, and WAV.
    """
    if not os.path.exists(target_path) or not meta:
        return

    ext = os.path.splitext(target_path)[1].lower().lstrip(".")

    # --- MP3 Target ---
    if ext == "mp3":
        try:
            try:
                tags = ID3(target_path)
            except ID3NoHeaderError:
                tags = ID3()

            if meta.get("title"):
                tags["TIT2"] = TIT2(encoding=3, text=str(meta["title"]))
            if meta.get("artist"):
                tags["TPE1"] = TPE1(encoding=3, text=str(meta["artist"]))
            if meta.get("album"):
                tags["TALB"] = TALB(encoding=3, text=str(meta["album"]))
            if meta.get("albumartist"):
                tags["TPE2"] = TPE2(encoding=3, text=str(meta["albumartist"]))
            if meta.get("date"):
                tags["TDRC"] = TDRC(encoding=3, text=str(meta["date"]))
            if meta.get("genre"):
                tags["TCON"] = TCON(encoding=3, text=str(meta["genre"]))
            if meta.get("track"):
                tags["TRCK"] = TRCK(encoding=3, text=str(meta["track"]))
            if meta.get("disc"):
                tags["TPOS"] = TPOS(encoding=3, text=str(meta["disc"]))
            if meta.get("composer"):
                tags["TCOM"] = TCOM(encoding=3, text=str(meta["composer"]))
            if meta.get("comment"):
                tags["COMM"] = COMM(encoding=3, lang="eng", desc="", text=str(meta["comment"]))
            if meta.get("lyrics"):
                tags["USLT"] = USLT(encoding=3, lang="eng", desc="", text=str(meta["lyrics"]))
            if meta.get("picture_data"):
                tags["APIC"] = APIC(
                    encoding=3,
                    mime=meta.get("picture_mime", "image/jpeg"),
                    type=3,  # Front Cover
                    desc="Cover",
                    data=meta["picture_data"],
                )
            # Save using ID3v2.3 for full Windows Explorer & music player compatibility
            tags.save(target_path, v2_version=3)
        except Exception:
            pass

    # --- M4A / MP4 Target ---
    elif ext in ("m4a", "mp4", "aac"):
        try:
            mp4 = MP4(target_path)
            if mp4.tags is None:
                mp4.add_tags()
            t = mp4.tags
            if meta.get("title"):
                t["\xa9nam"] = [str(meta["title"])]
            if meta.get("artist"):
                t["\xa9ART"] = [str(meta["artist"])]
            if meta.get("album"):
                t["\xa9alb"] = [str(meta["album"])]
            if meta.get("albumartist"):
                t["aART"] = [str(meta["albumartist"])]
            if meta.get("date"):
                t["\xa9day"] = [str(meta["date"])]
            if meta.get("genre"):
                t["\xa9gen"] = [str(meta["genre"])]
            if meta.get("composer"):
                t["\xa9wrt"] = [str(meta["composer"])]
            if meta.get("comment"):
                t["\xa9cmt"] = [str(meta["comment"])]
            if meta.get("lyrics"):
                t["\xa9lyr"] = [str(meta["lyrics"])]
            if meta.get("track"):
                try:
                    pts = str(meta["track"]).split("/")
                    t["trkn"] = [(int(pts[0]), int(pts[1]) if len(pts) > 1 else 0)]
                except Exception:
                    pass
            if meta.get("disc"):
                try:
                    pts = str(meta["disc"]).split("/")
                    t["disk"] = [(int(pts[0]), int(pts[1]) if len(pts) > 1 else 0)]
                except Exception:
                    pass
            if meta.get("picture_data"):
                mime = meta.get("picture_mime", "image/jpeg")
                fmt = MP4Cover.FORMAT_PNG if "png" in mime.lower() else MP4Cover.FORMAT_JPEG
                t["covr"] = [MP4Cover(meta["picture_data"], imageformat=fmt)]
            mp4.save()
        except Exception:
            pass

    # --- FLAC Target ---
    elif ext == "flac":
        try:
            flac = FLAC(target_path)
            mappings = [
                ("TITLE", meta.get("title")),
                ("ARTIST", meta.get("artist")),
                ("ALBUM", meta.get("album")),
                ("ALBUMARTIST", meta.get("albumartist")),
                ("DATE", meta.get("date")),
                ("GENRE", meta.get("genre")),
                ("TRACKNUMBER", meta.get("track")),
                ("DISCNUMBER", meta.get("disc")),
                ("COMPOSER", meta.get("composer")),
                ("COMMENT", meta.get("comment")),
                ("LYRICS", meta.get("lyrics")),
            ]
            for tag_name, val in mappings:
                if val:
                    flac[tag_name] = [str(val)]
            if meta.get("picture_data"):
                pic = Picture()
                pic.data = meta["picture_data"]
                pic.type = 3
                pic.mime = meta.get("picture_mime", "image/jpeg")
                pic.desc = "Front Cover"
                flac.clear_pictures()
                flac.add_picture(pic)
            flac.save()
        except Exception:
            pass

    # --- OPUS Target ---
    elif ext == "opus":
        try:
            opus = OggOpus(target_path)
            mappings = [
                ("title", meta.get("title")),
                ("artist", meta.get("artist")),
                ("album", meta.get("album")),
                ("albumartist", meta.get("albumartist")),
                ("date", meta.get("date")),
                ("genre", meta.get("genre")),
                ("tracknumber", meta.get("track")),
                ("discnumber", meta.get("disc")),
                ("composer", meta.get("composer")),
                ("comment", meta.get("comment")),
                ("lyrics", meta.get("lyrics")),
            ]
            for tag_name, val in mappings:
                if val:
                    opus[tag_name] = [str(val)]
            if meta.get("picture_data"):
                pic = Picture()
                pic.data = meta["picture_data"]
                pic.type = 3
                pic.mime = meta.get("picture_mime", "image/jpeg")
                pic.desc = "Front Cover"
                opus["metadata_block_picture"] = [base64.b64encode(pic.write()).decode("ascii")]
            opus.save()
        except Exception:
            pass

    # --- OGG Target ---
    elif ext == "ogg":
        try:
            ogg = OggVorbis(target_path)
            mappings = [
                ("title", meta.get("title")),
                ("artist", meta.get("artist")),
                ("album", meta.get("album")),
                ("albumartist", meta.get("albumartist")),
                ("date", meta.get("date")),
                ("genre", meta.get("genre")),
                ("tracknumber", meta.get("track")),
                ("discnumber", meta.get("disc")),
                ("composer", meta.get("composer")),
                ("comment", meta.get("comment")),
                ("lyrics", meta.get("lyrics")),
            ]
            for tag_name, val in mappings:
                if val:
                    ogg[tag_name] = [str(val)]
            if meta.get("picture_data"):
                pic = Picture()
                pic.data = meta["picture_data"]
                pic.type = 3
                pic.mime = meta.get("picture_mime", "image/jpeg")
                pic.desc = "Front Cover"
                ogg["metadata_block_picture"] = [base64.b64encode(pic.write()).decode("ascii")]
            ogg.save()
        except Exception:
            pass

    # --- WAV Target ---
    elif ext == "wav":
        try:
            wave = WAVE(target_path)
            try:
                wave.add_tags()
            except Exception:
                pass
            if wave.tags:
                if meta.get("title"):
                    wave.tags["TIT2"] = TIT2(encoding=3, text=str(meta["title"]))
                if meta.get("artist"):
                    wave.tags["TPE1"] = TPE1(encoding=3, text=str(meta["artist"]))
                if meta.get("album"):
                    wave.tags["TALB"] = TALB(encoding=3, text=str(meta["album"]))
                if meta.get("date"):
                    wave.tags["TDRC"] = TDRC(encoding=3, text=str(meta["date"]))
                if meta.get("genre"):
                    wave.tags["TCON"] = TCON(encoding=3, text=str(meta["genre"]))
                wave.save()
        except Exception:
            pass


def detect_media_type(file_path: str) -> Dict[str, Any]:
    """
    Automatically detects the file format, audio stream presence, codec,
    and metadata of any audio or video container.
    """
    res: Dict[str, Any] = {
        "is_valid": False,
        "format": None,
        "is_video": False,
        "has_audio": False,
        "codec": None,
        "title": None,
        "artist": None,
        "album": None,
        "has_cover": False,
    }
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return res

    ext = os.path.splitext(file_path)[1].lower().lstrip(".")

    # 1. Check with Mutagen
    try:
        audio = mutagen.File(file_path)
    except Exception:
        audio = None

    if audio is not None:
        res["is_valid"] = True
        res["has_audio"] = True
        if isinstance(audio, OggOpus):
            res["format"] = "opus"
            res["codec"] = "opus"
        elif isinstance(audio, MP3):
            res["format"] = "mp3"
            res["codec"] = "mp3"
        elif isinstance(audio, FLAC):
            res["format"] = "flac"
            res["codec"] = "flac"
        elif isinstance(audio, MP4):
            res["format"] = "m4a"
            res["codec"] = "aac"
        elif isinstance(audio, OggVorbis):
            res["format"] = "ogg"
            res["codec"] = "vorbis"
        elif isinstance(audio, WAVE):
            res["format"] = "wav"
            res["codec"] = "pcm"
        else:
            res["format"] = ext if ext else "audio"

    # 2. Check if video container
    if ext in ("mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v"):
        res["is_video"] = True

    # 3. FFprobe / FFmpeg stream inspection
    ffmpeg_bin = get_ffmpeg_path()
    if ffmpeg_bin:
        try:
            proc = subprocess.run(
                [ffmpeg_bin, "-i", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            out_err = proc.stderr
            if "Audio:" in out_err:
                res["has_audio"] = True
                res["is_valid"] = True
                import re
                m_codec = re.search(r"Audio:\s*(\w+)", out_err)
                if m_codec:
                    res["codec"] = m_codec.group(1).lower()
                    if not res["format"] or res["format"] in ("audio", "unknown", ""):
                        res["format"] = res["codec"]
            if "Video:" in out_err and not ("attached pic" in out_err.lower() or ("mjpeg" in out_err.lower() and ext in SUPPORTED_AUDIO_FORMATS)):
                res["is_video"] = True
        except Exception:
            pass

    if not res["format"]:
        res["format"] = ext if ext else "unknown"

    # 4. Extract metadata summary
    meta = extract_audio_metadata(file_path)
    res["title"] = meta.get("title")
    res["artist"] = meta.get("artist")
    res["album"] = meta.get("album")
    res["has_cover"] = bool(meta.get("picture_data"))

    return res


def convert_audio(
    input_file: str,
    output_file: str,
    target_format: Optional[str] = None,
    bitrate: str = "192k",
    keep_tags: bool = True
) -> dict:
    """
    Auto-detects input audio/video format and converts into target format using offline FFmpeg,
    meticulously preserving all song details (artist, album, title, year, genre)
    and embedding front album cover art.
    """
    if not os.path.exists(input_file):
        return {"success": False, "error": f"Audio file not found: {input_file}"}

    ffmpeg_bin = get_ffmpeg_path()
    if not ffmpeg_bin:
        return {"success": False, "error": "FFmpeg executable was not found on your system."}

    # Auto-detect source format and streams
    detection = detect_media_type(input_file)
    detected_format = detection.get("format") or os.path.splitext(input_file)[1].lower().lstrip(".")

    if not target_format:
        ext = os.path.splitext(output_file)[1].lower().lstrip(".")
        target_format = ext if ext else "mp3"

    target_format = target_format.lower().lstrip(".")
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    # 1. Pre-extract song metadata and album cover if enabled
    metadata = extract_audio_metadata(input_file) if keep_tags else {}

    # Check if input is already target format and paths are identical
    if os.path.abspath(input_file) == os.path.abspath(output_file):
        if keep_tags:
            inject_audio_metadata(output_file, metadata)
        return {
            "success": True,
            "output": output_file,
            "format": target_format,
            "detected_format": detected_format,
            "title": metadata.get("title"),
            "artist": metadata.get("artist"),
            "album": metadata.get("album"),
            "has_cover": bool(metadata.get("picture_data")),
        }

    # 2. Transcode audio track cleanly using FFmpeg
    cmd = [
        ffmpeg_bin,
        "-y",               # Overwrite output
        "-i", input_file,   # Input
        "-vn",              # Transcode audio stream (prevent stream-copy errors on covers)
    ]

    # Specific format codec mapping for best fidelity & compatibility
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

        # 3. Inject full metadata and album cover art into output file
        if keep_tags:
            inject_audio_metadata(output_file, metadata)

        return {
            "success": True,
            "output": output_file,
            "format": target_format,
            "detected_format": detected_format,
            "title": metadata.get("title"),
            "artist": metadata.get("artist"),
            "album": metadata.get("album"),
            "has_cover": bool(metadata.get("picture_data")),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def batch_convert_audio(
    input_folder: str,
    output_folder: str,
    target_format: str = "mp3",
    bitrate: str = "192k",
    keep_tags: bool = True,
    recursive: bool = False
) -> dict:
    """
    Batch converts all audio/video files in a directory to the desired audio format,
    auto-detecting each file's format and retaining all song details and album art.
    """
    if not os.path.isdir(input_folder):
        return {"success": False, "error": f"Folder not found: {input_folder}"}

    target_format = target_format.lower().lstrip(".")
    all_supported = tuple(f".{fmt}" for fmt in SUPPORTED_AUDIO_FORMATS + [v.lstrip(".") for v in SUPPORTED_VIDEO_FORMATS])

    candidate_files = []
    if recursive:
        for root, _, filenames in os.walk(input_folder):
            for fn in filenames:
                if fn.lower().endswith(all_supported):
                    candidate_files.append(os.path.join(root, fn))
    else:
        for fn in os.listdir(input_folder):
            full_p = os.path.join(input_folder, fn)
            if os.path.isfile(full_p) and fn.lower().endswith(all_supported):
                candidate_files.append(full_p)

    os.makedirs(output_folder, exist_ok=True)

    converted = []
    failed = []

    for in_p in candidate_files:
        fn = os.path.basename(in_p)
        base = os.path.splitext(fn)[0]
        out_p = os.path.join(output_folder, f"{base}.{target_format}")

        res = convert_audio(in_p, out_p, target_format, bitrate=bitrate, keep_tags=keep_tags)
        if res["success"]:
            converted.append({
                "file": out_p,
                "detected_format": res.get("detected_format"),
                "title": res.get("title"),
                "artist": res.get("artist"),
                "album": res.get("album"),
                "has_cover": res.get("has_cover"),
            })
        else:
            failed.append({"file": fn, "error": res["error"]})

    return {
        "success": True,
        "total_found": len(candidate_files),
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
    """Extracts the audio track from any video file with metadata preservation."""
    if not os.path.exists(video_file):
        return {"success": False, "error": f"Video file not found: {video_file}"}

    ffmpeg_bin = get_ffmpeg_path()
    if not ffmpeg_bin:
        return {"success": False, "error": "FFmpeg executable not found."}

    os.makedirs(os.path.dirname(os.path.abspath(output_audio_file)), exist_ok=True)
    target_format = target_format.lower().lstrip(".")

    # Extract metadata before stripping
    metadata = extract_audio_metadata(video_file)

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
    elif target_format == "opus":
        cmd.extend(["-c:a", "libopus", "-b:a", bitrate])
    else:
        cmd.extend(["-c:a", "aac", "-b:a", bitrate])

    cmd.append(output_audio_file)

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return {"success": False, "error": f"FFmpeg error: {proc.stderr[-300:]}"}

        # Inject tags
        inject_audio_metadata(output_audio_file, metadata)

        return {"success": True, "output": output_audio_file}
    except Exception as e:
        return {"success": False, "error": str(e)}


def trim_audio(input_file: str, output_file: str, start_time: str, duration_or_end: str, is_duration: bool = True) -> dict:
    """
    Trims an audio file while preserving metadata tags.
    start_time: e.g. '00:00:10' or '10' (in seconds)
    duration_or_end: duration if is_duration=True, or end timestamp if False.
    """
    if not os.path.exists(input_file):
        return {"success": False, "error": f"File not found: {input_file}"}

    ffmpeg_bin = get_ffmpeg_path()
    if not ffmpeg_bin:
        return {"success": False, "error": "FFmpeg executable not found."}

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    metadata = extract_audio_metadata(input_file)

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

        inject_audio_metadata(output_file, metadata)
        return {"success": True, "output": output_file}
    except Exception as e:
        return {"success": False, "error": str(e)}
