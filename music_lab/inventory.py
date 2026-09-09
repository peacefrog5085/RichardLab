#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".opus"}


def ffprobe(path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-show_entries",
        "format=duration,size,bit_rate:format_tags",
        "-of", "json",
        str(path),
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout or "{}")
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}


def scan_music(root: Path) -> list[dict]:
    records = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue

        info = ffprobe(path)
        fmt = info.get("format", {})
        tags = fmt.get("tags", {})

        records.append(
            {
                "path": str(path),
                "filename": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "duration_seconds": float(fmt["duration"])
                if fmt.get("duration")
                else None,
                "bit_rate": int(fmt["bit_rate"])
                if fmt.get("bit_rate")
                else None,
                "artist": tags.get("artist"),
                "album": tags.get("album"),
                "title": tags.get("title"),
                "album_artist": tags.get("album_artist"),
                "genre": tags.get("genre"),
                "date": tags.get("date"),
                "track": tags.get("track"),
                "disc": tags.get("disc"),
                "encoder": tags.get("encoder"),
            }
        )

    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only RichardLab music inventory scanner."
    )
    parser.add_argument(
        "music_root",
        type=Path,
        help="Music directory to scan",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("music_lab/music_inventory.json"),
        help="Output JSON path",
    )

    args = parser.parse_args()

    root = args.music_root.expanduser().resolve()

    if not root.exists():
        raise SystemExit(f"Music directory does not exist: {root}")

    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    records = scan_music(root)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    tagged = sum(
        1
        for r in records
        if any(
            r.get(field)
            for field in ("artist", "album", "title", "genre", "date")
        )
    )

    total_bytes = sum(r["size_bytes"] for r in records)

    print("RichardLab Music Inventory")
    print("=" * 50)
    print(f"Root:              {root}")
    print(f"Files scanned:     {len(records)}")
    print(f"Tagged files:      {tagged}")
    print(f"Mostly untagged:   {len(records) - tagged}")
    print(f"Total bytes:       {total_bytes:,}")
    print(f"Inventory:         {args.output}")


if __name__ == "__main__":
    main()
