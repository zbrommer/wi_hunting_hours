#!/usr/bin/env python3
"""Draw the app icon (rising blaze-orange sun over a dark horizon) as PNGs in src/icons/.
Pure standard library, no Pillow. Run once; the PNGs are committed."""
import struct, zlib
from pathlib import Path

BG, GROUND, SUN, LINE = (0x13, 0x20, 0x1B), (0x22, 0x34, 0x2D), (0xFF, 0x5F, 0x00), (0xFF, 0x8A, 0x3D)
HZ, R = 0.62, 0.25  # horizon height and sun radius, as fractions of the icon size (kept inside the maskable safe zone)

def color(x, y):
    if abs(y - HZ) < 0.014 and 0.14 < x < 0.86:
        return LINE
    if y < HZ and (x - 0.5) ** 2 + (y - HZ) ** 2 < R * R:
        return SUN
    return GROUND if y > HZ else BG

def png(size):
    rows = []
    for py in range(size):
        row = bytearray([0])
        for px in range(size):
            acc = [0, 0, 0]
            for sx in (0.25, 0.75):  # 2x2 supersampling for smooth edges
                for sy in (0.25, 0.75):
                    c = color((px + sx) / size, (py + sy) / size)
                    acc = [a + b for a, b in zip(acc, c)]
            row += bytes(round(a / 4) for a in acc)
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")

if __name__ == "__main__":  # also imported by app/ios_patch.py for the 1024px iOS icon
    out = Path(__file__).resolve().parent.parent / "src" / "icons"
    out.mkdir(parents=True, exist_ok=True)
    for s in (180, 192, 512):
        (out / f"icon-{s}.png").write_bytes(png(s))
        print("wrote", out / f"icon-{s}.png")
