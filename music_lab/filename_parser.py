#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".aac",
    ".ogg", ".wav", ".opus"
}


NOISE_PATTERNS = [
    r"\[official music video\]",
    r"\[official video\]",
    r"\[official lyric video\]",
    r"\[official audio\]",
    r"\[4k remaster\]",
    r"\[hd upgrade\]",
    r"\(official music video\)",
    r"\(official video\)",
    r"\(official lyric video\)",
    r"\(official audio\)",
    r"\bofficial music video\b",
    r"\bofficial video\b",
    r"\bofficial lyric video\b",
    r"\blyric video\b",
    r"\bofficial audio\b",
    r"\blyrics\b",
]


VERSION_PATTERNS = [
    r"\(([^()]*(?:live|acoustic|remix|remaster|radio edit|cover|version|session)[^()]*)\)",
    r"\[([^][]*(?:live|acoustic|remix|remaster|radio edit|cover|version|session)[^][]*)\]",
]


def clean_text(text: str) -> str:
    text = text.replace("⧸", "/")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -–—|:：/「」『』＂\"'")


def extract_version(text: str) -> list[str]:
    versions = []

    for pattern in VERSION_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = clean_text(match.group(1))

            if value and value.lower() not in {
                v.lower() for v in versions
            }:
                versions.append(value)

    return versions


def remove_noise(text: str) -> str:
    result = text

    for pattern in NOISE_PATTERNS:
        result = re.sub(pattern, " ", result, flags=re.IGNORECASE)

    return clean_text(result)


def build_record(
    artist: str | None,
    title: str | None,
    version: list[str],
    method: str,
    confidence: str,
    original: str,
) -> dict:
    return {
        "artist": clean_text(artist) if artist else None,
        "title": clean_text(title) if title else None,
        "version": version,
        "parse_method": method,
        "confidence": confidence,
        "original_stem": original,
    }


def parse_filename(filename: str) -> dict:
    stem = Path(filename).stem
    original = stem

    versions = extract_version(stem)
    cleaned = remove_noise(stem)

    # ---------------------------------------------------------
    # Explicit "Title" by Artist
    # ---------------------------------------------------------
    match = re.match(
        r'^[\"＂「『](.+?)[\"＂」』]\s+by\s+(.+)$',
        cleaned,
        flags=re.IGNORECASE,
    )

    if match:
        return build_record(
            match.group(2),
            match.group(1),
            versions,
            "quoted title by artist",
            "high",
            original,
        )

    # ---------------------------------------------------------
    # Explicit "Title by Artist"
    # ---------------------------------------------------------
    match = re.match(
        r'^(.+?)\s+by\s+(.+)$',
        cleaned,
        flags=re.IGNORECASE,
    )

    if match:
        return build_record(
            match.group(2),
            match.group(1),
            versions,
            "title by artist",
            "high",
            original,
        )

    # ---------------------------------------------------------
    # "Artist performs ... 'Title'"
    # ---------------------------------------------------------
    match = re.match(
        r"^(.+?)\s+performs.*?['\"＂](.+?)['\"＂]",
        cleaned,
        flags=re.IGNORECASE,
    )

    if match:
        return build_record(
            match.group(1),
            match.group(2),
            versions,
            "artist performs title",
            "high",
            original,
        )

    # ---------------------------------------------------------
    # Japanese corner quotes:
    # Artist「Title」
    #
    # This is checked against the ORIGINAL stem because the
    # cleanup step can strip the closing Japanese quote.
    # ---------------------------------------------------------
    match = re.match(
        r"^(.+?)「(.+?)」",
        stem,
    )

    if match:
        return build_record(
            match.group(1),
            match.group(2),
            versions,
            "artist Japanese-quoted title",
            "high",
            original,
        )

    # ---------------------------------------------------------
    # Artist "Title"
    # ---------------------------------------------------------
    match = re.match(
        r'^(.*?)\s+[\"＂](.+?)[\"＂]',
        cleaned,
    )

    if match:
        artist = clean_text(match.group(1))
        title = clean_text(match.group(2))

        if artist and title:
            return build_record(
                artist,
                title,
                versions,
                "artist quoted title",
                "high",
                original,
            )

    # ---------------------------------------------------------
    # Artist - Title
    # ---------------------------------------------------------
    match = re.match(
        r"^\s*(.+?)\s+-\s+(.+?)\s*$",
        cleaned,
    )

    if match:
        return build_record(
            match.group(1),
            match.group(2),
            versions,
            "artist - title",
            "high",
            original,
        )

    # ---------------------------------------------------------
    # Artist-Title
    #
    # Only accept this form when the left side looks like an
    # artist name rather than a normal sentence.
    # ---------------------------------------------------------
    match = re.match(
        r"^\s*(.+?)-\s*(.+?)\s*$",
        cleaned,
    )

    if match:
        left = clean_text(match.group(1))
        right = clean_text(match.group(2))

        if left and right and len(left) >= 2:
            return build_record(
                left,
                right,
                versions,
                "artist-title",
                "medium",
                original,
            )

    # ---------------------------------------------------------
    # Alternate separators
    # ---------------------------------------------------------
    for separator in [
        " – ",
        " — ",
        " ｜ ",
        " | ",
        "：",
        ":",
        "//",
    ]:
        if separator in cleaned:
            parts = cleaned.split(separator, 1)

            if len(parts) == 2:
                artist = clean_text(parts[0])
                title = clean_text(parts[1])

                if artist and title:
                    return build_record(
                        artist,
                        title,
                        versions,
                        f"alternate separator {separator!r}",
                        "high",
                        original,
                    )

    # ---------------------------------------------------------
    # Known artist patterns observed in this collection
    # ---------------------------------------------------------
    known_artists = [
        "KALEO",
        "Kathryn Cloward",
        "M83",
        "Limp Bizkit",
        "Metallica",
        "JISOO",
        "Passenger",
        "The Milk",
        "The XX",
        "Hueston",
        "Gert Taberner",
        "LERA LYNN",
        "LEVI ROBIN",
        "Mrs. GREEN APPLE",
        "Chet Faker",
        "Ben l'Oncle Soul",
    ]

    for artist in sorted(known_artists, key=len, reverse=True):
        pattern = rf"^{re.escape(artist)}\s+(.+)$"

        match = re.match(
            pattern,
            cleaned,
            flags=re.IGNORECASE,
        )

        if match:
            title = clean_text(match.group(1))

            if title:
                return build_record(
                    artist,
                    title,
                    versions,
                    "known artist pattern",
                    "high",
                    original,
                )

    # ---------------------------------------------------------
    # Explicit known collection formats
    # ---------------------------------------------------------
    match = re.match(
        r"^Senny Motion X Enoplat & Chino kid-\s*(.+)$",
        cleaned,
        flags=re.IGNORECASE,
    )

    if match:
        return build_record(
            "Senny Motion X Enoplat & Chino kid",
            match.group(1),
            versions,
            "known artist pattern",
            "high",
            original,
        )

    # ---------------------------------------------------------
    # Fallback: title only, artist unknown
    # ---------------------------------------------------------
    return build_record(
        None,
        cleaned or None,
        versions,
        "title only / unresolved artist",
        "low",
        original,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only RichardLab music filename parser v3."
    )

    parser.add_argument(
        "music_root",
        type=Path,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("music_lab/music_parsed.json"),
    )

    args = parser.parse_args()

    root = args.music_root.expanduser().resolve()

    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    records = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue

        parsed = parse_filename(path.name)

        records.append(
            {
                "path": str(path),
                "filename": path.name,
                **parsed,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)

    args.output.write_text(
        json.dumps(
            records,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    high = sum(r["confidence"] == "high" for r in records)
    medium = sum(r["confidence"] == "medium" for r in records)
    low = sum(r["confidence"] == "low" for r in records)

    print("RichardLab Music Filename Parser v3")
    print("=" * 50)
    print(f"Files parsed:      {len(records)}")
    print(f"High confidence:   {high}")
    print(f"Medium confidence: {medium}")
    print(f"Low confidence:    {low}")
    print(f"Output:            {args.output}")


if __name__ == "__main__":
    main()
