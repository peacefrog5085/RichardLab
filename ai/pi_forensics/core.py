"""Deterministic π identity fingerprinting.

This module deliberately separates:
1. encoding,
2. candidate generation,
3. searching,
4. statistical interpretation.

No sensitive identifiers are required. Do not put SSNs or other credentials
into experiment manifests.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log10
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ExperimentCase:
    name: str
    encoding: str
    sequence: str


@dataclass(frozen=True)
class PiHit:
    case: ExperimentCase
    position: int | None
    found: bool
    context: str = ""


def a1z26(text: str, padded: bool = False) -> str:
    """Encode A-Z as 1-26, optionally zero-padded to two digits."""
    out = []
    for ch in text.upper():
        if "A" <= ch <= "Z":
            n = ord(ch) - ord("A") + 1
            out.append(f"{n:02d}" if padded else str(n))
    return "".join(out)


def ascii_decimal(text: str) -> str:
    """Encode text as concatenated decimal ASCII byte values."""
    return "".join(str(ord(ch)) for ch in text)


def expected_wait(sequence: str) -> float:
    """Expected first-occurrence scale under an iid uniform-digit model."""
    if not sequence or any(c not in "0123456789" for c in sequence):
        raise ValueError("sequence must contain decimal digits only")
    return 10.0 ** len(sequence)


def probability_by_position(sequence: str, position: int) -> float:
    """Approximate P(at least one hit by position) under iid uniform digits."""
    if position < 1:
        return 0.0
    n = len(sequence)
    # Poisson approximation: 1 - exp(-position / 10**n)
    x = position / (10.0 ** n)
    if x > 50:
        return 1.0
    # Avoid importing scipy.
    import math
    return 1.0 - math.exp(-x)


def search_digits(sequence: str, input_dir: str | Path) -> PiHit:
    """Search chunked pi_digits_*.txt files from the pi-200m layout."""
    if not sequence or any(c not in "0123456789" for c in sequence):
        raise ValueError("sequence must contain decimal digits only")

    base = Path(input_dir)
    chunks = sorted(base.glob("pi_digits_*.txt"))
    if not chunks:
        raise FileNotFoundError(f"No π digit chunks found in {base}")

    overlap = max(0, len(sequence) - 1)
    previous = ""
    previous_start = 1

    for chunk in chunks:
        digits = chunk.read_text(encoding="ascii").strip()
        # Parse start position from filename: pi_digits_<start>_<end>.txt
        parts = chunk.stem.split("_")
        start = int(parts[2])
        combined = previous + digits
        idx = combined.find(sequence)
        if idx >= 0:
            pos = (previous_start if previous else start) + idx
            # Correct for overlap when a previous tail was prepended.
            if previous:
                pos = start - len(previous) + idx
            left = max(0, idx - 20)
            right = min(len(combined), idx + len(sequence) + 20)
            context = combined[left:right]
            return PiHit(
                case=ExperimentCase("ad-hoc", "raw", sequence),
                position=pos,
                found=True,
                context=context,
            )

        if overlap:
            previous = digits[-overlap:]
            previous_start = start + len(digits) - len(previous)
        else:
            previous = ""
        # Keep memory bounded even if chunk files are unexpectedly large.

    return PiHit(
        case=ExperimentCase("ad-hoc", "raw", sequence),
        position=None,
        found=False,
    )


def build_identity_cases(
    birthdate_digits: str,
    first_name: str = "RICHARD",
    last_name: str = "SPRAGUE",
) -> list[ExperimentCase]:
    """Build a predetermined, auditable identity experiment matrix.

    The caller supplies only a date string such as 01211981. No SSN is accepted.
    """
    if not birthdate_digits.isdigit():
        raise ValueError("birthdate_digits must contain digits only")

    rich = a1z26(first_name)
    spr = a1z26(last_name)
    full = rich + spr

    rich_p = a1z26(first_name, padded=True)
    spr_p = a1z26(last_name, padded=True)
    full_p = rich_p + spr_p

    cases = [
        ExperimentCase("birthday_8", "decimal", birthdate_digits),
        ExperimentCase("birthday_year", "decimal", birthdate_digits[-4:]),
        ExperimentCase("birthday_month_day", "decimal", birthdate_digits[:4]),
        ExperimentCase("first_name_a1z26", "a1z26", rich),
        ExperimentCase("last_name_a1z26", "a1z26", spr),
        ExperimentCase("full_name_a1z26", "a1z26", full),
        ExperimentCase("first_name_a1z26_padded", "a1z26_padded", rich_p),
        ExperimentCase("last_name_a1z26_padded", "a1z26_padded", spr_p),
        ExperimentCase("full_name_a1z26_padded", "a1z26_padded", full_p),
        ExperimentCase("birthday_then_name", "decimal+a1z26", birthdate_digits + full),
        ExperimentCase("name_then_birthday", "a1z26+decimal", full + birthdate_digits),
        ExperimentCase("birthday_then_padded_name", "decimal+a1z26_padded", birthdate_digits + full_p),
        ExperimentCase("padded_name_then_birthday", "a1z26_padded+decimal", full_p + birthdate_digits),
        ExperimentCase("first_name_ascii", "ascii_decimal", ascii_decimal(first_name)),
        ExperimentCase("last_name_ascii", "ascii_decimal", ascii_decimal(last_name)),
    ]
    return cases
