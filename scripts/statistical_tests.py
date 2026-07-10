#!/usr/bin/env python3
"""Compute count-based uncertainty for the open EmbedGuard benchmark.

The analysis deliberately uses only observed confusion-matrix counts from a
benchmark result JSON. It does not synthesize per-sample scores, invent a null
distribution, or substitute paper-reported values when evidence is missing.
"""

import argparse
import json
import math
from pathlib import Path
from typing import Any

DEFAULT_RESULTS = Path("results/latest_results.json")
DEFAULT_OUTPUT = Path("results/statistical_analysis.json")
Z_95 = 1.959963984540054
EXPECTED_SAMPLE_COUNTS = {
    "injection": 35,
    "nq": 50,
    "hotpotqa": 25,
    "msmarco": 25,
}


def load_results(path: Path = DEFAULT_RESULTS) -> dict[str, Any]:
    """Load benchmark results, failing closed when the file is absent."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def wilson_score_interval(
    successes: int,
    trials: int,
    z: float = Z_95,
) -> tuple[float, float]:
    """Return a two-sided Wilson score interval for a binomial proportion."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must be between zero and trials")

    proportion = successes / trials
    denominator = 1 + z**2 / trials
    center = (proportion + z**2 / (2 * trials)) / denominator
    margin = z * math.sqrt(
        proportion * (1 - proportion) / trials + z**2 / (4 * trials**2)
    ) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def analyze_results(results: dict[str, Any]) -> dict[str, Any]:
    """Compute observed rates and Wilson intervals from benchmark counts."""
    benchmarks = results["benchmarks"]
    if set(benchmarks) != set(EXPECTED_SAMPLE_COUNTS):
        missing = sorted(set(EXPECTED_SAMPLE_COUNTS) - set(benchmarks))
        unexpected = sorted(set(benchmarks) - set(EXPECTED_SAMPLE_COUNTS))
        raise ValueError(
            "Incomplete benchmark evidence: "
            f"missing={missing}, unexpected={unexpected}"
        )

    benchmark_errors = {
        name: benchmark["error"]
        for name, benchmark in benchmarks.items()
        if "error" in benchmark
    }
    if benchmark_errors:
        failures = ", ".join(
            f"{name}: {error}" for name, error in sorted(benchmark_errors.items())
        )
        raise ValueError(f"Incomplete benchmark evidence: {failures}")

    for name, expected in EXPECTED_SAMPLE_COUNTS.items():
        benchmark = benchmarks[name]
        if name == "injection":
            observed = sum(
                int(benchmark[key])
                for key in (
                    "true_positives",
                    "false_negatives",
                    "true_negatives",
                    "false_positives",
                )
            )
        else:
            observed = int(benchmark["true_negatives"]) + int(
                benchmark["false_positives"]
            )
        if observed != expected:
            raise ValueError(
                f"Incomplete {name} benchmark: expected {expected} samples, "
                f"observed {observed}"
            )

    injection = benchmarks["injection"]

    true_positives = int(injection["true_positives"])
    false_negatives = int(injection["false_negatives"])
    true_negatives = int(injection["true_negatives"])
    false_positives = int(injection["false_positives"])

    for name, benchmark in benchmarks.items():
        if name == "injection":
            continue
        true_negatives += int(benchmark.get("true_negatives", 0))
        false_positives += int(benchmark.get("false_positives", 0))

    attack_samples = true_positives + false_negatives
    benign_samples = true_negatives + false_positives
    detection_rate = true_positives / attack_samples
    specificity = true_negatives / benign_samples

    return {
        "attack_samples": attack_samples,
        "benign_samples": benign_samples,
        "detection_rate": detection_rate,
        "specificity": specificity,
        "detection_rate_ci_95": list(
            wilson_score_interval(true_positives, attack_samples)
        ),
        "specificity_ci_95": list(
            wilson_score_interval(true_negatives, benign_samples)
        ),
        "method": "Two-sided 95% Wilson score intervals over observed counts",
    }


def run_analysis(
    results_path: Path = DEFAULT_RESULTS,
    output_path: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    """Analyze a benchmark result JSON and write the derived artifact."""
    analysis = analyze_results(load_results(results_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis


def main() -> int:
    """Parse CLI arguments, run the analysis, and print the written artifact."""
    parser = argparse.ArgumentParser(
        description="Compute count-based uncertainty for EmbedGuard benchmark results."
    )
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    analysis = run_analysis(args.results, args.output)
    print(json.dumps(analysis, indent=2))
    print(f"Analysis saved to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
