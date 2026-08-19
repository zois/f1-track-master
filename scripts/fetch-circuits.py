#!/usr/bin/env python3
"""Download 2026 F1 circuit maps (detailed SVG layouts)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "circuits"
UA = "F1TrackMaster/1.0 (https://github.com/zois/f1-track-master; circuit quiz; educational)"

# Current 2026 layouts from https://github.com/julesr0y/f1-circuits-svg (CC BY 4.0)
LAYOUTS = {
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

BASE = "https://raw.githubusercontent.com/julesr0y/f1-circuits-svg/main/circuits/detailed/black-outline"


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


def wrap_detailed(svg: str) -> str:
    """Place the layout on the quiz map background with a little padding."""
    inner = re.sub(r"^<\?xml[^>]*>", "", svg).strip()
    inner = re.sub(r"<svg\b[^>]*>", "", inner, count=1)
    inner = re.sub(r"</svg>\s*$", "", inner)
    inner = re.sub(r"<desc\b[^>]*>.*?</desc>", "", inner, flags=re.I | re.S)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="500" height="500">
  <rect width="500" height="500" fill="#e8e4d4"/>
  <g transform="translate(28 28) scale(0.888)">
    {inner.strip()}
  </g>
</svg>
"""


def save(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    print(f"  saved {path.name} ({len(data):,} bytes)")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for slug, layout_id in LAYOUTS.items():
        dest = OUT / f"{slug}.svg"
        url = f"{BASE}/{layout_id}.svg"
        print(f"{slug}: fetching {layout_id}")
        try:
            text = fetch(url).decode("utf-8", errors="replace")
            if "<svg" not in text.lower() or "<path" not in text.lower():
                raise RuntimeError("not a circuit svg")
            save(dest, wrap_detailed(text).encode("utf-8"))
        except Exception as exc:
            print(f"  failed ({exc})")
            failed.append(slug)
        for leftover in OUT.glob(f"{slug}.png"):
            leftover.unlink()
            print(f"  removed {leftover.name}")
    if failed:
        print("FAILED:", ", ".join(failed), file=sys.stderr)
        return 1
    print("All 23 circuit images downloaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
