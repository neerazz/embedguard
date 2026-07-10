#!/usr/bin/env python3
"""
EmbedGuard Command Line Interface.

Usage:
    embedguard analyze "query" --documents doc1.txt doc2.txt
    embedguard analyze "query" --document-dir ./docs/
    embedguard check "query"  # Quick prompt injection check
    embedguard benchmark --dataset path/to/test.json
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import List, Optional

from embedguard import EmbedGuard, EmbedGuardConfig, __version__
from embedguard.config import OperationalMode, get_preset_config
from embedguard.prompt_detector import detect_injection
from embedguard.types import Document


def load_documents(paths: List[str]) -> List[Document]:
    """Load documents from file paths."""
    documents = []
    for path in paths:
        p = Path(path)
        if p.is_file():
            try:
                content = p.read_text()
                documents.append(Document(
                    content=content,
                    document_id=p.name,
                    metadata={"source": str(p)}
                ))
            except Exception as e:
                print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
        elif p.is_dir():
            for file_path in p.glob("**/*.txt"):
                try:
                    content = file_path.read_text()
                    documents.append(Document(
                        content=content,
                        document_id=file_path.name,
                        metadata={"source": str(file_path)}
                    ))
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
    return documents


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run full EmbedGuard analysis."""
    # Load configuration
    if args.preset:
        config = get_preset_config(args.preset)
    else:
        config = EmbedGuardConfig(
            mode=OperationalMode(args.mode),
            device=args.device,
        )

    # Initialize EmbedGuard
    guard = EmbedGuard(config)

    # Load documents
    documents = []
    if args.documents:
        documents = load_documents(args.documents)
    elif args.document_dir:
        documents = load_documents([args.document_dir])
    elif args.document_text:
        documents = [Document(content=args.document_text)]
    else:
        # Use stdin for documents
        stdin_content = sys.stdin.read().strip()
        if stdin_content:
            documents = [Document(content=stdin_content)]

    if not documents:
        print("Warning: No documents provided. Analysis will be limited.", file=sys.stderr)
        documents = [Document(content="No documents provided.")]

    # Run analysis
    result = guard.analyze(args.query, documents)

    # Output results
    output = {
        "query": args.query,
        "threat_score": result.threat_score,
        "threat_level": result.threat_level.value,
        "decision": result.decision.value,
        "detected_attacks": [a.value for a in result.detected_attacks],
        "attack_confidence": result.attack_confidence,
        "latency_ms": result.total_latency_ms,
        "num_documents": result.num_documents,
        "session_id": result.session_id,
    }

    if args.verbose:
        output["layer_signals"] = {
            name: {
                "score": sig.score,
                "confidence": sig.confidence,
                "latency_ms": sig.latency_ms,
                "details": sig.details,
            }
            for name, sig in result.layer_signals.items()
        }

    if args.output == "json":
        print(json.dumps(output, indent=2))
    else:
        print(f"\nEmbedGuard Analysis Results")
        print("=" * 40)
        print(f"Query: {args.query[:60]}{'...' if len(args.query) > 60 else ''}")
        print(f"Documents: {result.num_documents}")
        print(f"Threat Score: {result.threat_score:.3f}")
        print(f"Threat Level: {result.threat_level.value.upper()}")
        print(f"Decision: {result.decision.value.upper()}")
        if result.detected_attacks:
            print(f"Detected Attacks: {', '.join(a.value for a in result.detected_attacks)}")
        print(f"Latency: {result.total_latency_ms:.2f}ms")

        if args.verbose:
            print("\nLayer Signals:")
            for name, sig in result.layer_signals.items():
                print(f"  {name}: score={sig.score:.3f}, conf={sig.confidence:.3f}")

    return 0 if result.decision.value in {"allow", "log"} else 1


def cmd_check(args: argparse.Namespace) -> int:
    """Quick prompt injection check."""
    is_injection = detect_injection(args.query, threshold=args.threshold)

    if args.output == "json":
        print(json.dumps({
            "query": args.query,
            "is_injection": is_injection,
            "threshold": args.threshold,
        }))
    else:
        status = "⚠️  INJECTION DETECTED" if is_injection else "✓ Safe"
        print(f"{status}: {args.query[:60]}...")

    return 1 if is_injection else 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Run benchmark on a test dataset."""
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Error: Dataset not found: {args.dataset}", file=sys.stderr)
        return 1

    # Load dataset
    with open(dataset_path) as f:
        dataset = json.load(f)

    if not isinstance(dataset, list) or not dataset:
        print("Error: Dataset must be a non-empty JSON array", file=sys.stderr)
        return 1

    # Initialize EmbedGuard
    config = EmbedGuardConfig(mode=OperationalMode(args.mode))
    guard = EmbedGuard(config)

    # Run benchmark
    results = {
        "total": 0,
        "correct": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "attack_samples": 0,
        "benign_samples": 0,
        "latencies": [],
    }

    print(f"Running benchmark on {len(dataset)} samples...")

    classification_threshold = config.get_threshold("threat_score_flag")
    for index, item in enumerate(dataset):
        if not isinstance(item, dict) or not isinstance(item.get("is_attack"), bool):
            print(
                f"Error: Sample {index} must be an object with boolean is_attack",
                file=sys.stderr,
            )
            return 1
        query = item.get("query", "")
        documents = [Document(content=d) for d in item.get("documents", [])]
        expected_attack = item.get("is_attack", False)

        start = time.perf_counter()
        result = guard.analyze(query, documents)
        latency = (time.perf_counter() - start) * 1000

        # Measure classification at the configured flag threshold. Operational
        # mode changes enforcement/logging, not whether the score is suspicious.
        detected_attack = result.threat_score >= classification_threshold

        results["total"] += 1
        results["latencies"].append(latency)
        if expected_attack:
            results["attack_samples"] += 1
        else:
            results["benign_samples"] += 1

        if detected_attack == expected_attack:
            results["correct"] += 1
        elif detected_attack and not expected_attack:
            results["false_positives"] += 1
        else:
            results["false_negatives"] += 1

    # Calculate metrics
    accuracy = results["correct"] / results["total"] * 100
    avg_latency = sum(results["latencies"]) / len(results["latencies"])
    p95_index = math.ceil(len(results["latencies"]) * 0.95) - 1
    p95_latency = sorted(results["latencies"])[p95_index]
    false_positive_rate = (
        results["false_positives"] / results["benign_samples"] * 100
        if results["benign_samples"]
        else 0.0
    )
    false_negative_rate = (
        results["false_negatives"] / results["attack_samples"] * 100
        if results["attack_samples"]
        else 0.0
    )

    output = {
        "total_samples": results["total"],
        "attack_samples": results["attack_samples"],
        "benign_samples": results["benign_samples"],
        "classification_threshold": classification_threshold,
        "accuracy": accuracy,
        "false_positive_rate": false_positive_rate,
        "false_negative_rate": false_negative_rate,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
    }

    if args.output == "json":
        print(json.dumps(output, indent=2))
    else:
        print(f"\nBenchmark Results")
        print("=" * 40)
        print(f"Samples: {results['total']}")
        print(f"Accuracy: {accuracy:.1f}%")
        print(f"False Positive Rate: {output['false_positive_rate']:.1f}%")
        print(f"False Negative Rate: {output['false_negative_rate']:.1f}%")
        print(f"Avg Latency: {avg_latency:.2f}ms")
        print(f"P95 Latency: {p95_latency:.2f}ms")

    return 0


def cmd_version(args: argparse.Namespace) -> int:
    """Print version information."""
    print(f"EmbedGuard {__version__}")
    return 0


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="embedguard",
        description="EmbedGuard: Cross-layer RAG security framework",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"EmbedGuard {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run full security analysis on a query"
    )
    analyze_parser.add_argument("query", help="The query to analyze")
    analyze_parser.add_argument(
        "--documents", "-d",
        nargs="+",
        help="Document file paths"
    )
    analyze_parser.add_argument(
        "--document-dir",
        help="Directory containing documents"
    )
    analyze_parser.add_argument(
        "--document-text",
        help="Document text directly"
    )
    analyze_parser.add_argument(
        "--mode", "-m",
        choices=["passive", "gated", "active"],
        default="gated",
        help="Operational mode (default: gated)"
    )
    analyze_parser.add_argument(
        "--preset",
        choices=["high_security", "balanced", "low_latency"],
        help="Use preset configuration"
    )
    analyze_parser.add_argument(
        "--device",
        default="cpu",
        help="Device for inference (default: cpu)"
    )
    analyze_parser.add_argument(
        "--output", "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    analyze_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output with layer details"
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    # Check command (quick injection check)
    check_parser = subparsers.add_parser(
        "check",
        help="Quick prompt injection check"
    )
    check_parser.add_argument("query", help="The query to check")
    check_parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.7,
        help="Detection threshold (default: 0.7)"
    )
    check_parser.add_argument(
        "--output", "-o",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    check_parser.set_defaults(func=cmd_check)

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Run benchmark on test dataset"
    )
    benchmark_parser.add_argument(
        "--dataset",
        required=True,
        help="Path to benchmark dataset (JSON)"
    )
    benchmark_parser.add_argument(
        "--mode", "-m",
        choices=["passive", "gated", "active"],
        default="gated",
        help="Operational mode"
    )
    benchmark_parser.add_argument(
        "--output", "-o",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    benchmark_parser.set_defaults(func=cmd_benchmark)

    # Parse arguments
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
