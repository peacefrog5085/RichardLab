#!/usr/bin/env python3

from knowledge.knowledge import (
    _query_features,
    search_records,
    consult,
)


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(
            f"{label}\n"
            f"  expected: {expected!r}\n"
            f"  actual:   {actual!r}"
        )


def test_query_experiment_detection():
    features = _query_features(
        "What should I use to run experiment-011d.py?"
    )

    assert_equal(
        features["experiments"],
        {"experiment-011d.py"},
        "Exact experiment detection failed",
    )


def test_unrelated_experiment_detection():
    features = _query_features(
        "What should I use to run an unrelated experiment?"
    )

    assert_equal(
        features["experiments"],
        set(),
        "Unrelated experiment was incorrectly identified",
    )


def test_run_exact_experiment():
    result = consult(
        "What should I use to run experiment-011d.py?"
    )

    assert_equal(
        result["decision"],
        "REUSE",
        "Exact experiment run query should reuse known-good knowledge",
    )

    assert result["knowledge_id"], (
        "Exact experiment run query returned no knowledge ID"
    )

    matching = [
        record
        for _, record in search_records(
            "What should I use to run experiment-011d.py?"
        )
        if record.get("knowledge_id") == result["knowledge_id"]
    ]

    assert matching, (
        "Exact experiment run query returned a knowledge ID "
        "that is not present in search results"
    )

    record = matching[0]
    assert record.get("subject") == "experiment-011d.py", (
        f"Run query selected unrelated subject: {record.get('subject')!r}"
    )
    assert (
        record.get("kind") == "known_good"
        or record.get("status") == "passed"
    ), "Run query did not select successful knowledge"


def test_about_exact_experiment():
    result = consult(
        "Tell me about experiment-011d.py."
    )

    assert_equal(
        result["decision"],
        "REUSE",
        "Informational experiment query should reuse known-good knowledge",
    )

    assert result["knowledge_id"], (
        "Informational experiment query returned no knowledge ID"
    )

    matching = [
        record
        for _, record in search_records(
            "Tell me about experiment-011d.py."
        )
        if record.get("knowledge_id") == result["knowledge_id"]
    ]

    assert matching, (
        "Informational query returned a knowledge ID "
        "that is not present in search results"
    )

    record = matching[0]
    assert record.get("subject") == "experiment-011d.py", (
        f"Informational query selected unrelated subject: {record.get('subject')!r}"
    )
    assert (
        record.get("kind") == "known_good"
        or record.get("status") == "passed"
    ), "Informational query did not select successful knowledge"


def test_failure_exact_experiment():
    result = consult(
        "What does RichardLab know about experiment-011d.py failing?"
    )

    assert_equal(
        result["decision"],
        "BLOCK",
        "Explicit experiment failure query should block",
    )

    assert_equal(
        result["knowledge_id"],
        "K-8DB72A656CDC",
        "Failure query selected unexpected knowledge",
    )


def test_unrelated_experiment():
    result = consult(
        "What should I use to run an unrelated experiment?"
    )

    assert_equal(
        result["decision"],
        "NO_KNOWN_MEMORY",
        "Unrelated experiment should not retrieve unrelated knowledge",
    )


def test_failure_ranks_above_success():
    results = search_records(
        "What does RichardLab know about experiment-011d.py failing?"
    )

    assert results, "Failure query returned no results"

    first_score, first_record = results[0]

    assert_equal(
        first_record["knowledge_id"],
        "K-8DB72A656CDC",
        "Failure memory did not rank first for failure query",
    )

    assert first_score > 0.90, (
        f"Failure relevance unexpectedly low: {first_score}"
    )


def test_success_ranks_above_failure_for_run():
    results = search_records(
        "What should I use to run experiment-011d.py?"
    )

    assert results, "Run query returned no results"

    first_score, first_record = results[0]

    assert first_record.get("subject") == "experiment-011d.py", (
        "Run query did not rank the exact experiment first"
    )

    assert (
        first_record.get("kind") == "known_good"
        or first_record.get("status") == "passed"
    ), "Run query did not rank successful knowledge first"

    assert first_score > 0.90, (
        f"Known-good relevance unexpectedly low: {first_score}"
    )


def run_all():
    tests = [
        test_query_experiment_detection,
        test_unrelated_experiment_detection,
        test_run_exact_experiment,
        test_about_exact_experiment,
        test_failure_exact_experiment,
        test_unrelated_experiment,
        test_failure_ranks_above_success,
        test_success_ranks_above_failure_for_run,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS  {test.__name__}")
        passed += 1

    print()
    print(f"KNOWLEDGE TESTS: {passed}/{len(tests)} PASSED")


if __name__ == "__main__":
    run_all()
