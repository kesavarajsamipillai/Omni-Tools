"""
Image Conversion & Processing Module (Completely Offline)
Features:
- Convert single image between ANY combination (PNG, JPG/JPEG, WEBP, BMP, GIF, TIFF, ICO)
- Handle transparency and RGBA -> RGB correctly with clean background
- Batch folder image converter
- Image resizer (percentage or dimensions with aspect ratio lock)
- Image compressor (quality adjustment and format optimization)
"""

import os
from typing import List, Tuple, Optional
from PIL import Image

SUPPORTED_IMAGE_FORMATS = [
    "png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"
]


def convert_image(
    input_path: str,
    output_path: str,
    target_format: Optional[str] = None,
    quality: int = 95,
    bg_color: Tuple[int, int, int] = (255, 255, 255)
) -> dict:
    """
    Converts any image file into target format.
    Handles color modes and transparency (RGBA -> RGB) cleanly.
    """
    if not os.path.exists(input_path):
        return {"success": False, "error": f"Image file not found: {input_path}"}

    if not target_format:
        ext = os.path.splitext(output_path)[1].lower().lstrip(".")
        target_format = ext if ext else "png"

    target_format = target_format.lower().lstrip(".")
    if target_format == "jpg":
        target_format = "jpeg"

    try:
        with Image.open(input_path) as img:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            # Special format requirements
            if target_format in ["jpeg"]:
                if img.mode in ("RGBA", "LA", "P"):
                    # Create white background canvas
                    rgba_img = img.convert("RGBA")
                    canvas = Image.new("RGB", rgba_img.size, bg_color)
                    canvas.paste(rgba_img, mask=rgba_img.split()[3])
                    canvas.save(output_path, format="JPEG", quality=quality, optimize=True)
                else:
                    rgb_img = img.convert("RGB")
                    rgb_img.save(output_path, format="JPEG", quality=quality, optimize=True)

            elif target_format == "ico":
                # Windows ICO supports sizes like 16, 32, 48, 64, 128, 256
                ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                rgba_img = img.convert("RGBA")
                rgba_img.save(output_path, format="ICO", sizes=ico_sizes)

            elif target_format == "bmp":
                rgb_img = img.convert("RGB")
                rgb_img.save(output_path, format="BMP")

            elif target_format == "webp":
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                img.save(output_path, format="WEBP", quality=quality)

            elif target_format == "png":
                img.save(output_path, format="PNG", optimize=True)

            elif target_format == "tiff":
                img.save(output_path, format="TIFF")

            elif target_format == "gif":
                img.save(output_path, format="GIF")

            else:
                img.save(output_path, format=target_format.upper())

        return {
            "success": True,
            "output": output_path,
            "format": target_format,
            "orig_size": os.path.getsize(input_path),
            "new_size": os.path.getsize(output_path)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def batch_convert_images(
    input_folder: str,
    output_folder: str,
    target_format: str,
    quality: int = 95,
    recursive: bool = False
) -> dict:
    """Batch converts all supported images in a folder to target format."""
    if not os.path.isdir(input_folder):
        return {"success": False, "error": f"Folder not found: {input_folder}"}

    target_format = target_format.lower().lstrip(".")
    ext_out = "jpg" if target_format == "jpeg" else target_format

    valid_exts = tuple(f".{fmt}" for fmt in SUPPORTED_IMAGE_FORMATS)
    converted = []
    failed = []

    files_to_process = []
    if recursive:
        for root, _, files in os.walk(input_folder):
            for f in files:
                if f.lower().endswith(valid_exts):
                    files_to_process.append(os.path.join(root, f))
    else:
        for f in os.listdir(input_folder):
            full_p = os.path.join(input_folder, f)
            if os.path.isfile(full_p) and f.lower().endswith(valid_exts):
                files_to_process.append(full_p)

    os.makedirs(output_folder, exist_ok=True)

    for in_file in files_to_process:
        base_name = os.path.splitext(os.path.basename(in_file))[0]
        out_file = os.path.join(output_folder, f"{base_name}.{ext_out}")
        
        # Avoid file collision if target has same name
        counter = 1
        while os.path.exists(out_file) and os.path.abspath(out_file) == os.path.abspath(in_file):
            out_file = os.path.join(output_folder, f"{base_name}_{counter}.{ext_out}")
            counter += 1

        res = convert_image(in_file, out_file, target_format, quality=quality)
        if res["success"]:
            converted.append(out_file)
        else:
            failed.append({"file": in_file, "error": res["error"]})

    return {
        "success": True,
        "total_found": len(files_to_process),
        "converted_count": len(converted),
        "failed_count": len(failed),
        "converted": converted,
        "failed": failed
    }


def resize_image(
    input_path: str,
    output_path: str,
    scale_pct: Optional[float] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    maintain_aspect: bool = True
) -> dict:
    """Resizes an image by percentage or explicit width/height."""
    if not os.path.exists(input_path):
        return {"success": False, "error": f"Image file not found: {input_path}"}

    try:
        with Image.open(input_path) as img:
            orig_w, orig_h = img.size

            if scale_pct is not None:
                new_w = max(1, int(orig_w * (scale_pct / 100.0)))
                new_h = max(1, int(orig_h * (scale_pct / 100.0)))
            elif width is not None and height is not None:
                if maintain_aspect:
                    ratio = min(width / orig_w, height / orig_h)
                    new_w = max(1, int(orig_w * ratio))
                    new_h = max(1, int(orig_h * ratio))
                else:
                    new_w, new_h = width, height
            elif width is not None:
                new_w = width
                new_h = max(1, int(orig_h * (width / orig_w)))
            elif height is not None:
                new_h = height
                new_w = max(1, int(orig_w * (height / orig_h)))
            else:
                return {"success": False, "error": "Specify scale_pct or width/height"}

            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            resized.save(output_path)

        return {
            "success": True,
            "output": output_path,
            "orig_size": (orig_w, orig_h),
            "new_size": (new_w, new_h)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def compress_image(input_path: str, output_path: str, quality: int = 75) -> dict:
    """Compresses an image to reduce file size."""
    if not os.path.exists(input_path):
        return {"success": False, "error": f"File not found: {input_path}"}

    try:
        with Image.open(input_path) as img:
            orig_size = os.path.getsize(input_path)
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            fmt = img.format if img.format else "JPEG"
            if fmt in ("JPEG", "JPG"):
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=quality, optimize=True)
            elif fmt == "PNG":
                # Convert to palette mode for huge size drop or optimize PNG
                img.save(output_path, "PNG", optimize=True)
            elif fmt == "WEBP":
                img.save(output_path, "WEBP", quality=quality, method=6)
            else:
                img.save(output_path, quality=quality)

            new_size = os.path.getsize(output_path)
            savings_pct = round(((orig_size - new_size) / orig_size) * 100, 1) if orig_size > 0 else 0

        return {
            "success": True,
            "output": output_path,
            "orig_bytes": orig_size,
            "new_bytes": new_size,
            "saved_pct": savings_pct
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
