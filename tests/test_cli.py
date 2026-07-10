"""Regression tests for CLI benchmark accounting."""

import argparse
import json
from types import SimpleNamespace

import pytest

from embedguard import cli


def test_cli_benchmark_uses_score_and_class_denominators(
    tmp_path, monkeypatch, capsys
):
    """Passive LOG decisions must not corrupt attack labels or FPR/FNR."""
    samples = [
        {"query": "attack-high", "documents": [], "is_attack": True},
        {"query": "attack-low", "documents": [], "is_attack": True},
        {"query": "benign-high", "documents": [], "is_attack": False},
        {"query": "benign-low", "documents": [], "is_attack": False},
    ]
    dataset = tmp_path / "benchmark.json"
    dataset.write_text(json.dumps(samples), encoding="utf-8")
    scores = {
        "attack-high": 0.9,
        "attack-low": 0.2,
        "benign-high": 0.8,
        "benign-low": 0.1,
    }

    class _FakeGuard:
        def __init__(self, config):
            self.config = config

        def analyze(self, query, documents):
            assert documents == []
            return SimpleNamespace(
                threat_score=scores[query],
                decision=SimpleNamespace(value="log"),
            )

    monkeypatch.setattr(cli, "EmbedGuard", _FakeGuard)
    args = argparse.Namespace(
        dataset=str(dataset),
        mode="passive",
        output="json",
    )

    assert cli.cmd_benchmark(args) == 0
    stdout = capsys.readouterr().out
    payload = json.loads(stdout[stdout.index("{"):])

    assert payload["total_samples"] == 4
    assert payload["attack_samples"] == 2
    assert payload["benign_samples"] == 2
    assert payload["classification_threshold"] == 0.7
    assert payload["accuracy"] == 50.0
    assert payload["false_positive_rate"] == 50.0
    assert payload["false_negative_rate"] == 50.0


def test_cli_benchmark_rejects_empty_or_non_array_dataset(tmp_path, capsys):
    for value in ([], {"query": "not-an-array"}):
        dataset = tmp_path / "invalid.json"
        dataset.write_text(json.dumps(value), encoding="utf-8")
        args = argparse.Namespace(
            dataset=str(dataset),
            mode="gated",
            output="json",
        )

        assert cli.cmd_benchmark(args) == 1
        assert "non-empty JSON array" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [("allow", 0), ("log", 0), ("flag", 1), ("block", 1)],
)
def test_cli_analyze_exit_status_matches_intervention(
    decision, expected_status, monkeypatch
):
    """Passive LOG is successful; only FLAG/BLOCK signal intervention."""

    class _FakeGuard:
        def __init__(self, config):
            self.config = config

        def analyze(self, query, documents):
            return SimpleNamespace(
                threat_score=0.0,
                threat_level=SimpleNamespace(value="none"),
                decision=SimpleNamespace(value=decision),
                detected_attacks=[],
                attack_confidence=0.0,
                total_latency_ms=1.0,
                num_documents=len(documents),
                session_id="test-session",
                layer_signals={},
            )

    monkeypatch.setattr(cli, "EmbedGuard", _FakeGuard)
    args = argparse.Namespace(
        preset=None,
        mode="passive",
        device="cpu",
        documents=None,
        document_dir=None,
        document_text="document",
        query="query",
        verbose=False,
        output="json",
    )

    assert cli.cmd_analyze(args) == expected_status
