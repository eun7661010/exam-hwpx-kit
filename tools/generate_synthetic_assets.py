"""Generate deterministic, metadata-free PNG fixtures using only the standard library."""

from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path


def _chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data))
    )


def make_chart(width: int = 320, height: int = 180) -> bytes:
    white = (255, 255, 255)
    ink = (55, 65, 81)
    blue = (37, 99, 235)
    amber = (245, 158, 11)
    pixels = [[white for _ in range(width)] for _ in range(height)]

    def rectangle(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
        for y in range(max(0, y0), min(height, y1)):
            for x in range(max(0, x0), min(width, x1)):
                pixels[y][x] = color

    rectangle(36, 24, 39, 150, ink)
    rectangle(36, 147, 294, 150, ink)
    rectangle(39, 76, 294, 79, amber)
    values = [52, 63, 68, 71]
    for index, value in enumerate(values):
        x0 = 64 + index * 55
        bar_height = value
        rectangle(x0, 147 - bar_height, x0 + 28, 147, blue)

    raw = b"".join(b"\x00" + bytes(channel for pixel in row for channel in pixel) for row in pixels)
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        signature
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / "examples" / "assets" / "sensor-chart.png"
    target.write_bytes(make_chart())
    print(f"generated {target.relative_to(root)} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
