"""Watch face (dial) binary compiler and RGB565 image converter."""
import struct
from typing import Any, Dict, Optional, Tuple

DIAL_MAGIC = b"DIAL"
COLOR_FORMAT_RGB565 = 0x0001


def rgb_to_rgb565_bytes(r: int, g: int, b: int) -> bytes:
    """Convert 8-bit RGB components to 16-bit little-endian RGB565 bytes."""
    val = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    return struct.pack("<H", val)


def generate_solid_rgb565(width: int, height: int, r: int, g: int, b: int) -> bytes:
    """Generate raw uncompressed RGB565 pixel buffer of solid color."""
    pixel = rgb_to_rgb565_bytes(r, g, b)
    return pixel * (width * height)


def generate_gradient_rgb565(width: int, height: int) -> bytes:
    """Generate raw RGB565 test pattern with horizontal and vertical gradients."""
    buf = bytearray(width * height * 2)
    idx = 0
    for y in range(height):
        r = int((y / max(1, height - 1)) * 255)
        for x in range(width):
            b = int((x / max(1, width - 1)) * 255)
            g = (r + b) // 2
            val = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            buf[idx] = val & 0xFF
            buf[idx + 1] = (val >> 8) & 0xFF
            idx += 2
    return bytes(buf)


def image_to_rgb565(image_path: str, target_width: int, target_height: int) -> bytes:
    """Convert an image file (PNG/JPEG) to RGB565 using Pillow."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for image file conversion (pip install pillow)") from exc

    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        buf = bytearray(target_width * target_height * 2)
        idx = 0
        for y in range(target_height):
            for x in range(target_width):
                r, g, b = img.getpixel((x, y))
                val = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
                buf[idx] = val & 0xFF
                buf[idx + 1] = (val >> 8) & 0xFF
                idx += 2
        return bytes(buf)


def compile_dial_package(
    width: int = 240,
    height: int = 286,
    thumb_width: int = 64,
    thumb_height: int = 64,
    background_rgb565: Optional[bytes] = None,
    thumbnail_rgb565: Optional[bytes] = None,
) -> bytes:
    """Compile a 32-byte header + thumbnail + background dial package."""
    expected_bg_len = width * height * 2
    expected_th_len = thumb_width * thumb_height * 2

    if background_rgb565 is None:
        background_rgb565 = generate_gradient_rgb565(width, height)
    elif len(background_rgb565) != expected_bg_len:
        raise ValueError(f"Background buffer size {len(background_rgb565)} != expected {expected_bg_len}")

    if thumbnail_rgb565 is None:
        thumbnail_rgb565 = generate_solid_rgb565(thumb_width, thumb_height, 0, 100, 200)
    elif len(thumbnail_rgb565) != expected_th_len:
        raise ValueError(f"Thumbnail buffer size {len(thumbnail_rgb565)} != expected {expected_th_len}")

    thumb_offset = 32
    thumb_size = len(thumbnail_rgb565)
    bg_offset = thumb_offset + thumb_size
    bg_size = len(background_rgb565)

    header = struct.pack(
        "<4sHHHHHHIIII",
        DIAL_MAGIC,
        0x0001,  # version
        width,
        height,
        COLOR_FORMAT_RGB565,
        0x0001,  # flags: has_preview
        0x0000,  # reserved
        thumb_offset,
        thumb_size,
        bg_offset,
        bg_size,
    )

    return header + thumbnail_rgb565 + background_rgb565


def parse_dial_package(data: bytes) -> Dict[str, Any]:
    """Parse and validate dial package binary."""
    if len(data) < 32:
        raise ValueError("Dial package shorter than 32-byte header")

    magic, ver, w, h, fmt, flags, res, th_off, th_sz, bg_off, bg_sz = struct.unpack("<4sHHHHHHIIII", data[:32])
    if magic != DIAL_MAGIC:
        raise ValueError(f"Invalid dial magic: {magic}")
    if fmt != COLOR_FORMAT_RGB565:
        raise ValueError(f"Unsupported color format: {fmt}")

    if len(data) < bg_off + bg_sz:
        raise ValueError("Truncated dial package data")

    thumb_data = data[th_off:th_off + th_sz]
    bg_data = data[bg_off:bg_off + bg_sz]

    return {
        "version": ver,
        "width": w,
        "height": h,
        "flags": flags,
        "thumbnail_offset": th_off,
        "thumbnail_size": th_sz,
        "background_offset": bg_off,
        "background_size": bg_sz,
        "thumbnail_bytes": thumb_data,
        "background_bytes": bg_data,
    }
