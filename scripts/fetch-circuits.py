#!/usr/bin/env python3
"""Download real 2026 F1 circuit maps from Wikimedia Commons (and F1DB fallback)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "circuits"
UA = "F1TrackMaster/1.0 (https://github.com; circuit quiz; educational)"

# Wikimedia Commons filenames for the current 2026 layouts.
WIKI = {
    "melbourne": "Albert Park Circuit 2021.svg",
    "shanghai": "Shanghai International Racing Circuit track map.svg",
    "suzuka": "Suzuka circuit map--2005.svg",
    "miami": "Hard Rock Stadium Circuit 2022.svg",
    "montreal": "Île Notre-Dame (Circuit Gilles Villeneuve).svg",
    "monaco": "Monte Carlo Formula 1 track map.svg",
    "catalunya": "Circuit de Catalunya moto 2021.svg",
    "spielberg": "Spielberg bare map numbers contextless 2021 corner names.svg",
    "silverstone": "Silverstone Circuit 2020.png",
    "spa": "Spa-Francorchamps of Belgium.svg",
    "hungaroring": "Hungaroring2026.svg",
    "zandvoort": "Zandvoort Circuit.png",
    "monza": "Monza track map.svg",
    "madring": "Madring (2026).svg",
    "baku": "Baku Formula One circuit map.svg",
    "sepang": "Sepang.svg",
    "marina-bay": "Marina Bay circuit 2023.svg",
    "austin": "Austin circuit.svg",
    "mexico-city": "Autódromo Hermanos Rodríguez 2015.svg",
    "interlagos": "Autódromo José Carlos Pace (AKA Interlagos) track map.svg",
    "las-vegas": "2023 Las Vegas street circuit.svg",
    "lusail": "Lusail International Circuit 2023.svg",
    "yas-marina": "Yas Marina Circuit.png",
}

F1DB_FALLBACK = {
    "melbourne": "melbourne-2",
    "shanghai": "shanghai-1",
    "suzuka": "suzuka-2",
    "miami": "miami-1",
    "montreal": "montreal-6",
    "monaco": "monaco-6",
    "catalunya": "catalunya-6",
    "spielberg": "spielberg-3",
    "silverstone": "silverstone-8",
    "spa": "spa-francorchamps-4",
    "hungaroring": "hungaroring-3",
    "zandvoort": "zandvoort-5",
    "monza": "monza-7",
    "madring": "madring-1",
    "baku": "baku-1",
    "sepang": "sepang-1",
    "marina-bay": "marina-bay-4",
    "austin": "austin-1",
    "mexico-city": "mexico-city-3",
    "interlagos": "interlagos-2",
    "las-vegas": "las-vegas-1",
    "lusail": "lusail-1",
    "yas-marina": "yas-marina-2",
}

def fetch(url: str) -> bytes:
    result = subprocess.run(
        ["curl", "-fsSL", "-A", UA, "--max-time", "90", url],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(err or f"curl exit {result.returncode}")
    if not result.stdout:
        raise RuntimeError("empty response")
    return result.stdout


def wiki_url(filename: str, width: int | None = None) -> str:
    from urllib.parse import quote
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(filename)
    if width:
        url += f"?width={width}"
    return url


def f1db_url(layout_id: str) -> str:
    return f"https://cdn.jsdelivr.net/gh/f1db/f1db@main/src/assets/circuits/black/{layout_id}.svg"


def strip_svg_labels(svg: str) -> str:
    svg = re.sub(r"<title\b[^>]*>.*?</title>", "", svg, flags=re.I | re.S)
    svg = re.sub(r"<desc\b[^>]*>.*?</desc>", "", svg, flags=re.I | re.S)
    svg = re.sub(r"<text\b[^>]*>.*?</text>", "", svg, flags=re.I | re.S)
    svg = re.sub(r"<tspan\b[^>]*>.*?</tspan>", "", svg, flags=re.I | re.S)
    return svg


def wrap_f1db(svg: str) -> str:
    """Place the white/black F1DB outline on a map-like background."""
    inner = re.sub(r"^<\?xml[^>]*>", "", svg).strip()
    inner = re.sub(r"<svg\b[^>]*>", "", inner, count=1)
    inner = re.sub(r"</svg>\s*$", "", inner)
    return f"""<svg viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
  <rect width="500" height="500" fill="#1a3324"/>
  <g transform="translate(40 40) scale(0.84)" stroke-linecap="round">
    {inner}
  </g>
</svg>
"""


def save(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    print(f"  saved {path.name} ({len(data):,} bytes)")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for slug, filename in WIKI.items():
        ext = Path(filename).suffix.lower()
        width = 1600 if ext in {".png", ".jpg", ".jpeg"} else None
        dest_ext = ".png" if width else ".svg"
        dest = OUT / f"{slug}{dest_ext}"
        print(f"{slug}: fetching {filename}")
        try:
            data = fetch(wiki_url(filename, width))
            if dest_ext == ".svg":
                text = data.decode("utf-8", errors="replace")
                if "<svg" not in text.lower():
                    raise RuntimeError("not an svg")
                text = strip_svg_labels(text)
                save(dest, text.encode("utf-8"))
            else:
                if not data.startswith(b"\x89PNG") and b"JFIF" not in data[:32]:
                    raise RuntimeError("not a raster image")
                save(dest, data)
        except Exception as exc:
            print(f"  wiki failed ({exc}); trying F1DB")
            try:
                svg = fetch(f1db_url(F1DB_FALLBACK[slug])).decode("utf-8")
                save(OUT / f"{slug}.svg", wrap_f1db(svg).encode("utf-8"))
                if dest.exists() and dest.suffix != ".svg":
                    dest.unlink()
            except Exception as exc2:
                print(f"  F1DB failed too: {exc2}")
                failed.append(slug)
    if failed:
        print("FAILED:", ", ".join(failed), file=sys.stderr)
        return 1
    print("All 23 circuit images downloaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
