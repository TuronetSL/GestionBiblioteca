from __future__ import annotations

import struct
from pathlib import Path


def build_ico(path: Path, size: int = 32) -> None:
    w = h = size
    pixels = bytearray()
    for y in range(h):
        for x in range(w):
            r = int(35 + (x / (w - 1)) * 40)
            g = int(90 + (y / (h - 1)) * 85)
            b = 200
            a = 255
            if int(w * 0.24) < x < int(w * 0.36) or int(w * 0.62) < x < int(w * 0.74):
                r, g, b = 255, 255, 255
            pixels += bytes((b, g, r, a))

    row = w * 4
    pixels = b"".join(pixels[(h - 1 - i) * row : (h - i) * row] for i in range(h))

    mask_row_bytes = ((w + 31) // 32) * 4
    and_mask = b"\x00" * (mask_row_bytes * h)

    header = struct.pack(
        "<IIIHHIIIIII",
        40,
        w,
        h * 2,
        1,
        32,
        0,
        len(pixels),
        0,
        0,
        0,
        0,
    )
    img = header + pixels + and_mask

    icondir = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(img), 22)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(icondir + entry + img)


if __name__ == "__main__":
    build_ico(Path("assets/app_icon.ico"))
    print("Icon generated at assets/app_icon.ico")
