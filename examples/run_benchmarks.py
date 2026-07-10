#!/usr/bin/env python3
"""
EmbedGuard Benchmark Runner

This script executes the EmbedGuard detection pipeline on real benchmark datasets
and attack samples, producing reproducible experimental results for the paper.

Usage:
    python examples/run_benchmarks.py --all           # Run all benchmarks
    python examples/run_benchmarks.py --injection     # Run injection detection only
    python examples/run_benchmarks.py --benchmark nq  # Run specific benchmark

Output:
    Results are saved to results/ directory in JSON and CSV formats.
"""

import argparse
import hashlib
import importlib.metadata
import json
import platform

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from embedguard.prompt_detector import INJECTION_PATTERNS, PromptInjectionDetector

PROJECT_ROOT = Path(__file__).parent.parent


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of a benchmark input or source file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _installed_versions(distributions: List[str]) -> Dict[str, str]:
    """Record installed versions without requiring a dependency lock file."""
    versions = {}
    for distribution in distributions:
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = "not-installed"
    return versions


def _git_head(repo_root: Path) -> str | None:
    """Read the checked-out commit without requiring the Git executable."""
    git_dir = repo_root / ".git"
    if git_dir.is_file():
        marker = git_dir.read_text(encoding="utf-8").strip()
        if not marker.startswith("gitdir:"):
            return None
        git_dir = (repo_root / marker.split(":", maxsplit=1)[1].strip()).resolve()
    head_path = git_dir / "HEAD"
    if not head_path.is_file():
        return None
    head = head_path.read_text(encoding="utf-8").strip()
    if not head.startswith("ref:"):
        return head or None
    ref = head.split(":", maxsplit=1)[1].strip()
    loose_ref = git_dir / ref
    if loose_ref.is_file():
        return loose_ref.read_text(encoding="utf-8").strip() or None
    packed_refs = git_dir / "packed-refs"
    if packed_refs.is_file():
        for line in packed_refs.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith(("#", "^")):
                commit, name = line.split(" ", maxsplit=1)
                if name == ref:
                    return commit
    return None


class BenchmarkRunner:
    """Runs EmbedGuard benchmarks and collects real performance metrics."""

    def __init__(
        self,
        data_dir: Path,
        results_dir: Path,
    ):
        """Initialize benchmark runner.

        Args:
            data_dir: Path to data directory
            results_dir: Path to results directory
        """
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.input_files = set()

        # Create results directory
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Initialize detectors
        self.prompt_detector = PromptInjectionDetector(
            threshold=0.70,
            use_neural=False,
        )

        # Track execution time
        self.start_time = None

    def load_jsonl(self, filepath: Path) -> List[Dict]:
        """Load data from JSONL file."""
        self.input_files.add(filepath.resolve())
        data = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))
        return data

    def run_injection_benchmark(self) -> Dict[str, Any]:
        """Run prompt injection detection benchmark.

        Returns:
            Dictionary with benchmark results including:
            - detection_rate: True positive rate for attacks
            - false_positive_rate: False positive rate for benign queries
            - precision, recall, f1: Standard metrics
            - latency_stats: Timing statistics
            - per_attack_type: Breakdown by attack type
        """
        print("\n" + "=" * 60)
        print("PROMPT INJECTION DETECTION BENCHMARK")
        print("=" * 60)

        # Load attack dataset
        attack_file = self.data_dir / "attacks" / "injection" / "prompt_injection.jsonl"
        if not attack_file.exists():
            raise FileNotFoundError(f"Attack dataset not found: {attack_file}")

        attacks = self.load_jsonl(attack_file)
        print(f"Loaded {len(attacks)} injection samples")

        # Track results
        results = {
            "total_samples": len(attacks),
            "attack_samples": 0,
            "benign_samples": 0,
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0,
            "latencies_ms": [],
            "per_attack_type": {},
            "detailed_results": [],
        }

        # Process each sample
        for sample in attacks:
            sample_id = sample["id"]
            attack_type = sample["attack_type"]
            payload = sample["payload"]
            expected_detection = sample["expected_detection"]

            # Track attack types
            if attack_type not in results["per_attack_type"]:
                results["per_attack_type"][attack_type] = {
                    "total": 0,
                    "detected": 0,
                    "scores": [],
                }

            # Run detection with timing
            start_time = time.perf_counter()
            score, confidence, details = self.prompt_detector.detect(payload)
            latency_ms = (time.perf_counter() - start_time) * 1000
            results["latencies_ms"].append(latency_ms)

            # Determine if detected (score > threshold)
            detected = score > self.prompt_detector.threshold

            # Update per-attack-type stats
            results["per_attack_type"][attack_type]["total"] += 1
            results["per_attack_type"][attack_type]["scores"].append(score)
            if detected:
                results["per_attack_type"][attack_type]["detected"] += 1

            # Update confusion matrix
            if expected_detection:  # This is an attack
                results["attack_samples"] += 1
                if detected:
                    results["true_positives"] += 1
                else:
                    results["false_negatives"] += 1
            else:  # This is benign
                results["benign_samples"] += 1
                if detected:
                    results["false_positives"] += 1
                else:
                    results["true_negatives"] += 1

            # Store detailed result
            results["detailed_results"].append({
                "id": sample_id,
                "attack_type": attack_type,
                "expected_detection": expected_detection,
                "actual_detection": detected,
                "score": score,
                "confidence": confidence,
                "latency_ms": latency_ms,
                "patterns_matched": details.get("patterns_matched", []),
                "correct": detected == expected_detection,
            })

            # Print progress
            status = "✓" if detected == expected_detection else "✗"
            print(f"  {status} {sample_id}: score={score:.3f}, detected={detected}, expected={expected_detection}")

        # Calculate metrics
        tp = results["true_positives"]
        fp = results["false_positives"]
        tn = results["true_negatives"]
        fn = results["false_negatives"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / len(attacks) if attacks else 0.0
        detection_rate = recall
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        results["metrics"] = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "detection_rate": detection_rate,
            "false_positive_rate": fpr,
        }

        # Calculate latency statistics
        latencies = results["latencies_ms"]
        results["latency_stats"] = {
            "mean_ms": float(np.mean(latencies)),
            "median_ms": float(np.median(latencies)),
            "p95_ms": float(np.percentile(latencies, 95)),
            "p99_ms": float(np.percentile(latencies, 99)),
            "min_ms": float(np.min(latencies)),
            "max_ms": float(np.max(latencies)),
            "std_ms": float(np.std(latencies)),
        }

        # Calculate per-attack-type detection rates
        for stats in results["per_attack_type"].values():
            stats["detection_rate"] = stats["detected"] / stats["total"] if stats["total"] > 0 else 0.0
            stats["mean_score"] = float(np.mean(stats["scores"])) if stats["scores"] else 0.0
            del stats["scores"]  # Remove raw scores to save space

        # Print summary
        print("\n" + "-" * 40)
        print("INJECTION BENCHMARK SUMMARY")
        print("-" * 40)
        print(f"Total samples:      {results['total_samples']}")
        print(f"Attack samples:     {results['attack_samples']}")
        print(f"Benign samples:     {results['benign_samples']}")
        print(f"True positives:     {tp}")
        print(f"False positives:    {fp}")
        print(f"True negatives:     {tn}")
        print(f"False negatives:    {fn}")
        print(f"Accuracy:           {accuracy:.1%}")
        print(f"Precision:          {precision:.1%}")
        print(f"Recall/Detection:   {recall:.1%}")
        print(f"F1 Score:           {f1:.3f}")
        print(f"False Positive Rate: {fpr:.1%}")
        print(f"Mean latency:       {results['latency_stats']['mean_ms']:.2f}ms")
        print(f"P95 latency:        {results['latency_stats']['p95_ms']:.2f}ms")

        # Print per-attack-type breakdown
        print("\nPer-Attack-Type Detection Rates:")
        for attack_type, stats in sorted(results["per_attack_type"].items()):
            rate = stats["detection_rate"]
            print(f"  {attack_type:25s}: {rate:.1%} ({stats['detected']}/{stats['total']})")

        return results

    def run_benign_benchmark(self, dataset_name: str = "nq") -> Dict[str, Any]:
        """Run benchmark on benign queries to measure false positive rate.

        Args:
            dataset_name: Name of benchmark dataset (nq, hotpotqa, msmarco)

        Returns:
            Dictionary with benchmark results
        """
        print("\n" + "=" * 60)
        print(f"BENIGN QUERY BENCHMARK: {dataset_name.upper()}")
        print("=" * 60)

        # Load dataset
        dataset_dir = self.data_dir / "benchmarks" / dataset_name
        questions_file = dataset_dir / "questions.jsonl"

        if not questions_file.exists():
            raise FileNotFoundError(f"Dataset not found: {questions_file}")

        questions = self.load_jsonl(questions_file)
        print(f"Loaded {len(questions)} questions from {dataset_name}")

        # Track results
        results = {
            "dataset": dataset_name,
            "total_samples": len(questions),
            "false_positives": 0,
            "true_negatives": 0,
            "latencies_ms": [],
            "detailed_results": [],
        }

        # Process each question
        for q in questions:
            qid = q["id"]
            # Get query text (different datasets have different field names)
            query = q.get("question") or q.get("query", "")

            # Run detection with timing
            start_time = time.perf_counter()
            score, confidence, details = self.prompt_detector.detect(query)
            latency_ms = (time.perf_counter() - start_time) * 1000
            results["latencies_ms"].append(latency_ms)

            # These are benign queries, so detection is a false positive
            detected = score > self.prompt_detector.threshold
            if detected:
                results["false_positives"] += 1
            else:
                results["true_negatives"] += 1

            # Store result
            results["detailed_results"].append({
                "id": qid,
                "query": query[:100],  # Truncate for readability
                "score": score,
                "confidence": confidence,
                "detected": detected,
                "latency_ms": latency_ms,
            })

            status = "✓" if not detected else "FP"
            if detected:
                print(f"  {status} {qid}: score={score:.3f} - FALSE POSITIVE!")

        # Calculate metrics
        fp = results["false_positives"]
        tn = results["true_negatives"]
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        results["metrics"] = {
            "false_positive_rate": fpr,
            "specificity": 1 - fpr,
        }

        # Latency stats
        latencies = results["latencies_ms"]
        results["latency_stats"] = {
            "mean_ms": float(np.mean(latencies)),
            "median_ms": float(np.median(latencies)),
            "p95_ms": float(np.percentile(latencies, 95)),
            "p99_ms": float(np.percentile(latencies, 99)),
            "min_ms": float(np.min(latencies)),
            "max_ms": float(np.max(latencies)),
        }

        # Print summary
        print("\n" + "-" * 40)
        print(f"{dataset_name.upper()} BENCHMARK SUMMARY")
        print("-" * 40)
        print(f"Total samples:        {results['total_samples']}")
        print(f"False positives:      {fp}")
        print(f"True negatives:       {tn}")
        print(f"False positive rate:  {fpr:.2%}")
        print(f"Mean latency:         {results['latency_stats']['mean_ms']:.2f}ms")

        return results

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and aggregate results.

        Returns:
            Comprehensive results dictionary
        """
        self.start_time = datetime.now()

        all_results = {
            "timestamp": self.start_time.isoformat(),
            "configuration": {
                "detector": "PromptInjectionDetector (pattern-only)",
                "threshold": 0.70,
                "num_patterns": len(INJECTION_PATTERNS),
            },
            "benchmarks": {},
        }

        # A release benchmark is atomic: missing or malformed inputs must fail the
        # run rather than produce a plausible-looking partial artifact.
        all_results["benchmarks"]["injection"] = self.run_injection_benchmark()

        for dataset in ["nq", "hotpotqa", "msmarco"]:
            all_results["benchmarks"][dataset] = self.run_benign_benchmark(dataset)

        expected_samples = {
            "injection": 35,
            "nq": 50,
            "hotpotqa": 25,
            "msmarco": 25,
        }
        for dataset, expected in expected_samples.items():
            actual = all_results["benchmarks"][dataset].get("total_samples")
            if actual != expected:
                raise ValueError(
                    f"Incomplete {dataset} benchmark: expected {expected} samples, "
                    f"observed {actual}"
                )

        # Calculate aggregate statistics
        all_results["aggregate"] = self._calculate_aggregate_stats(all_results)
        all_results["provenance"] = self._build_provenance()

        # Save results
        self._save_results(all_results)

        return all_results

    def _build_provenance(self) -> Dict[str, Any]:
        """Capture the exact inputs, source files, runtime, and timing scope."""
        source_files = [
            PROJECT_ROOT / "embedguard" / "prompt_detector" / "__init__.py",
            PROJECT_ROOT / "examples" / "run_benchmarks.py",
            PROJECT_ROOT / "scripts" / "statistical_tests.py",
            PROJECT_ROOT / "pyproject.toml",
        ]
        clock = time.get_clock_info("perf_counter")
        return {
            "source_commit": _git_head(PROJECT_ROOT),
            "source_binding": "source_file_sha256 binds the exact benchmark implementation",
            "source_file_sha256": {
                str(path.relative_to(PROJECT_ROOT)): _sha256(path)
                for path in source_files
            },
            "input_file_sha256": {
                str(path.relative_to(PROJECT_ROOT)): _sha256(path)
                for path in sorted(self.input_files)
            },
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "unreported",
            "dependencies": _installed_versions([
                "embedguard", "numpy", "scipy", "scikit-learn", "pydantic", "loguru"
            ]),
            "timing": {
                "clock": "time.perf_counter",
                "implementation": clock.implementation,
                "resolution_seconds": clock.resolution,
                "monotonic": clock.monotonic,
                "adjustable": clock.adjustable,
                "repetitions_per_sample": 1,
                "scope": "single-threaded detector calls; host- and load-dependent",
            },
        }

    def _calculate_aggregate_stats(self, results: Dict) -> Dict:
        """Calculate aggregate statistics across all benchmarks."""
        aggregate = {
            "total_samples_processed": 0,
            "total_latency_samples": 0,
            "all_latencies_ms": [],
        }

        for benchmark in results["benchmarks"].values():
            if "error" in benchmark:
                continue

            aggregate["total_samples_processed"] += benchmark.get("total_samples", 0)

            if "latencies_ms" in benchmark:
                aggregate["all_latencies_ms"].extend(benchmark["latencies_ms"])
                aggregate["total_latency_samples"] += len(benchmark["latencies_ms"])

        if aggregate["all_latencies_ms"]:
            latencies = aggregate["all_latencies_ms"]
            aggregate["overall_latency_stats"] = {
                "mean_ms": float(np.mean(latencies)),
                "median_ms": float(np.median(latencies)),
                "p95_ms": float(np.percentile(latencies, 95)),
                "p99_ms": float(np.percentile(latencies, 99)),
            }

        # Remove raw latencies to save space
        del aggregate["all_latencies_ms"]

        return aggregate

    def _save_results(self, results: Dict) -> None:
        """Save benchmark results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save full JSON results
        json_file = self.results_dir / f"benchmark_results_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            # Remove detailed_results for summary file (too large)
            summary = json.loads(json.dumps(results, default=str))
            for name in summary.get("benchmarks", {}):
                if "detailed_results" in summary["benchmarks"][name]:
                    del summary["benchmarks"][name]["detailed_results"]
                if "latencies_ms" in summary["benchmarks"][name]:
                    del summary["benchmarks"][name]["latencies_ms"]
            json.dump(summary, f, indent=2)
        print(f"\nResults saved to: {json_file}")

        # Save latest results symlink/copy
        latest_file = self.results_dir / "latest_results.json"
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"Latest results: {latest_file}")

        # Generate markdown report
        self._generate_markdown_report(results, timestamp)

    def _generate_markdown_report(self, results: Dict, timestamp: str) -> None:
        """Generate human-readable markdown report."""
        report_file = self.results_dir / f"benchmark_report_{timestamp}.md"

        lines = [
            "# EmbedGuard Benchmark Results",
            "",
            f"**Generated:** {results['timestamp']}",
            (
                "**Detector:** PromptInjectionDetector, pattern-only "
                f"({len(INJECTION_PATTERNS)} patterns)"
            ),
            "**Threshold:** 0.70",
            f"**Source commit:** {results['provenance']['source_commit'] or 'unavailable'}",
            f"**Python:** {results['provenance']['python']}",
            "**Timing scope:** single run; host- and load-dependent",
            "",
            "---",
            "",
        ]

        # Injection benchmark results
        if (
            "injection" in results["benchmarks"]
            and "error" not in results["benchmarks"]["injection"]
        ):
            inj = results["benchmarks"]["injection"]
            metrics = inj["metrics"]
            latency = inj["latency_stats"]

            lines.extend([
                "## Prompt Injection Detection",
                "",
                "### Performance Metrics",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Detection Rate (Recall) | {metrics['recall']:.1%} |",
                f"| Precision | {metrics['precision']:.1%} |",
                f"| F1 Score | {metrics['f1_score']:.3f} |",
                f"| False Positive Rate | {metrics['false_positive_rate']:.1%} |",
                f"| Accuracy | {metrics['accuracy']:.1%} |",
                "",
                "### Confusion Matrix",
                "",
                f"- True Positives: {inj['true_positives']}",
                f"- False Positives: {inj['false_positives']}",
                f"- True Negatives: {inj['true_negatives']}",
                f"- False Negatives: {inj['false_negatives']}",
                "",
                "### Latency",
                "",
                f"- Mean: {latency['mean_ms']:.2f}ms",
                f"- Median: {latency['median_ms']:.2f}ms",
                f"- P95: {latency['p95_ms']:.2f}ms",
                f"- P99: {latency['p99_ms']:.2f}ms",
                "",
                "### Detection by Attack Type",
                "",
                "| Attack Type | Detection Rate | Count |",
                "|-------------|----------------|-------|",
            ])

            for attack_type, stats in sorted(inj["per_attack_type"].items()):
                lines.append(
                    f"| {attack_type} | {stats['detection_rate']:.1%} | "
                    f"{stats['detected']}/{stats['total']} |"
                )

            lines.extend(["", "---", ""])

        # Benign benchmark results
        for dataset in ["nq", "hotpotqa", "msmarco"]:
            if dataset in results["benchmarks"] and "error" not in results["benchmarks"][dataset]:
                bench = results["benchmarks"][dataset]
                lines.extend([
                    f"## Benign Benchmark: {dataset.upper()}",
                    "",
                    f"- Total samples: {bench['total_samples']}",
                    f"- False positives: {bench['false_positives']}",
                    f"- False positive rate: {bench['metrics']['false_positive_rate']:.2%}",
                    f"- Mean latency: {bench['latency_stats']['mean_ms']:.2f}ms",
                    "",
                ])

        # Aggregate stats
        if "aggregate" in results:
            agg = results["aggregate"]
            lines.extend([
                "---",
                "",
                "## Aggregate Statistics",
                "",
                f"- Total samples processed: {agg['total_samples_processed']}",
            ])
            if "overall_latency_stats" in agg:
                lat = agg["overall_latency_stats"]
                lines.extend([
                    f"- Overall mean latency: {lat['mean_ms']:.2f}ms",
                    f"- Overall P95 latency: {lat['p95_ms']:.2f}ms",
                ])

        # Write report
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Report saved to: {report_file}")


def main():
    """Main entry point for benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Run EmbedGuard benchmarks on real datasets"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all benchmarks"
    )
    parser.add_argument(
        "--injection", action="store_true",
        help="Run injection detection benchmark only"
    )
    parser.add_argument(
        "--benchmark", type=str,
        choices=["nq", "hotpotqa", "msmarco"],
        help="Run specific benign benchmark"
    )
    parser.add_argument(
        "--data-dir", type=str,
        default=str(PROJECT_ROOT / "data"),
        help="Path to data directory"
    )
    parser.add_argument(
        "--results-dir", type=str,
        default=str(PROJECT_ROOT / "results"),
        help="Path to results directory"
    )

    args = parser.parse_args()

    # Default to --all if no specific benchmark selected
    if not (args.all or args.injection or args.benchmark):
        args.all = True

    print("=" * 60)
    print("EMBEDGUARD BENCHMARK RUNNER")
    print("=" * 60)
    print(f"Data directory: {args.data_dir}")
    print(f"Results directory: {args.results_dir}")
    print(f"Pattern detector: {len(INJECTION_PATTERNS)} patterns")

    runner = BenchmarkRunner(
        data_dir=Path(args.data_dir),
        results_dir=Path(args.results_dir),
    )

    if args.all:
        runner.run_all_benchmarks()
    elif args.injection:
        runner.run_injection_benchmark()
    elif args.benchmark:
        runner.run_benign_benchmark(args.benchmark)

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
