from pathlib import Path

from ai.pi_forensics.core import (
    a1z26,
    ascii_decimal,
    build_identity_cases,
    expected_wait,
    probability_by_position,
    search_digits,
)


def test_a1z26():
    assert a1z26("RICHARD") == "189381184"
    assert a1z26("RS") == "1819"


def test_a1z26_padded():
    assert a1z26("RS", padded=True) == "1819"
    assert a1z26("A", padded=True) == "01"


def test_ascii_decimal():
    assert ascii_decimal("RS") == "8283"


def test_expected_wait():
    assert expected_wait("1234") == 10000


def test_probability_monotonic():
    assert probability_by_position("12345678", 1) < probability_by_position("12345678", 100000000)


def test_identity_matrix():
    cases = build_identity_cases("01211981")
    names = {c.name for c in cases}
    assert "birthday_8" in names
    assert "full_name_a1z26" in names
    assert "birthday_then_name" in names


def test_search_across_chunk_boundary(tmp_path: Path):
    (tmp_path / "pi_digits_1_5.txt").write_text("12345", encoding="ascii")
    (tmp_path / "pi_digits_6_10.txt").write_text("67890", encoding="ascii")
    hit = search_digits("4567", tmp_path)
    assert hit.found
    assert hit.position == 4
