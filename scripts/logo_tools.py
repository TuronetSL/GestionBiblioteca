from __future__ import annotations

import argparse
from pathlib import Path


def build_icon_from_png(source_png: Path, target_ico: Path, white_threshold: int = 245) -> None:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Pillow no está instalado. Ejecuta: python -m pip install pillow"
        ) from exc

    img = Image.open(source_png).convert("RGBA")
    pixels = img.getdata()
    cleaned = []
    for r, g, b, a in pixels:
        if r >= white_threshold and g >= white_threshold and b >= white_threshold:
            cleaned.append((r, g, b, 0))
        else:
            cleaned.append((r, g, b, a))

    img.putdata(cleaned)
    target_ico.parent.mkdir(parents=True, exist_ok=True)
    img.save(target_ico, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera icono .ico transparente desde PNG")
    parser.add_argument("--source", required=True, help="Ruta al PNG original")
    parser.add_argument("--out", required=True, help="Ruta de salida .ico")
    parser.add_argument("--white-threshold", type=int, default=245, help="Umbral para eliminar blanco")
    args = parser.parse_args()

    build_icon_from_png(Path(args.source), Path(args.out), args.white_threshold)
    print(f"Icon generated at {args.out}")


if __name__ == "__main__":
    main()
