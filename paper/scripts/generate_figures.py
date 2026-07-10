#!/usr/bin/env python3
"""EmbedGuard paper figures.

Figures 1-2 are drawn diagrams (matplotlib primitives, vector output).
Figures 3-4 are plotted from committed data: Figure 3 from the Tier-2
benchmark JSON and Figure 4 from a machine-readable transcription of the
Tier-1 ablation table in the published article (Section 4.1).

Usage:  python3 paper/scripts/generate_figures.py
Output: paper/images/figure_{1,2,3,4}.{png,pdf}
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "images"
RESULTS = ROOT / "results" / "benchmark_results_20260710_025640.json"
TIER1_ABLATION = ROOT / "paper" / "data" / "tier1_ablation_vor.json"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "figure.dpi": 200,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

INK = "#1a1a2e"
GRAY = "#8a8f98"
def _box(ax, x, y, w, h, text, fc, fontsize=8.5, ec=INK, lw=1.0, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.015",
                                fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=INK, fontweight=weight, linespacing=1.35)


def _arrow(ax, x0, y0, x1, y1, color=INK, lw=1.1, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, ls=ls,
                                 mutation_scale=11, color=color, lw=lw,
                                 shrinkA=1, shrinkB=1))


def figure_1_architecture():
    """Delegates to figure1_architecture.py (attack-vs-defense narrative figure)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import figure1_architecture
    figure1_architecture.main()


def figure_2_tee_protocol():
    """Target TEE protocol as a sequence diagram: design, not package behavior."""
    fig, ax = plt.subplots(figsize=(6.8, 4.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.35); ax.axis("off")
    ax.text(
        5.0,
        7.15,
        "Target AMD SEV-SNP protocol — design only; not implemented in the released package",
        ha="center",
        fontsize=8.2,
        color=INK,
        fontweight="bold",
    )

    actors = [(1.3, "Document\nsource"), (4.0, "Confidential VM\n(SEV-SNP)"),
              (6.7, "Vector store"), (9.0, "Retrieval\nverifier")]
    for x, name in actors:
        _box(ax, x - 0.85, 6.0, 1.7, 0.7, name, "#f1f3f6", fontsize=8)
        ax.plot([x, x], [0.55, 6.0], color=GRAY, lw=0.8, ls=(0, (4, 3)), zorder=0)

    def msg(y, x0, x1, text, above=True):
        _arrow(ax, x0, y, x1, y, lw=1.0)
        ax.text((x0 + x1) / 2, y + (0.13 if above else -0.3), text,
                ha="center", fontsize=7.6, color=INK)

    ax.text(0.12, 5.55, "Ingestion", fontsize=8, color=GRAY, rotation=90, va="top")
    msg(5.65, 9.0, 4.0, "fresh challenge nonce N (recorded)")
    msg(5.25, 1.3, 4.0, "document D")
    # enclave internal note
    _box(ax, 2.65, 4.15, 2.7, 1.10,
         "E = f_model(D)\nB = H(H(D)||H(model)||H(E)||T||N)\n"
         "request SNP report\nREPORT_DATA = B",
         "#dcefdd", fontsize=5.35)
    msg(3.75, 4.0, 6.7, "E + bound metadata + SNP report + N")

    ax.plot([0.1, 9.9], [3.45, 3.45], color=GRAY, lw=0.6)
    ax.text(0.12, 3.1, "Retrieval", fontsize=8, color=GRAY, rotation=90, va="top")
    msg(2.85, 9.0, 6.7, "query top-k", above=True)
    msg(2.35, 6.7, 9.0, "candidates + bound SNP reports")
    _box(ax, 7.50, 0.95, 2.20, 1.30,
         "validate ARK/ASK/VCEK chain\nverify report signature with VCEK\n"
         "recompute REPORT_DATA binding\ncheck replay cache + max age\n"
         "enforce measurement/policy/TCB", "#dbe7f4", fontsize=5.15)
    msg(0.85, 9.0, 6.7, "verification result: reject", above=False)

    ax.text(
        5.0,
        0.18,
        "Released code uses software HMAC binding only; it obtains no SNP report or AMD endorsement chain.",
        ha="center",
        fontsize=6.5,
        color=GRAY,
        style="italic",
    )
    fig.savefig(OUT / "figure_2.png"); fig.savefig(OUT / "figure_2.pdf")
    plt.close(fig)


def figure_3_latency():
    """Per-dataset latency stats plotted from the committed benchmark JSON."""
    data = json.loads(RESULTS.read_text())
    order = [("injection", "Injection set\n30 attacks + 5 benign"), ("nq", "NQ-style"),
             ("hotpotqa", "HotpotQA-style"), ("msmarco", "MS-MARCO-style")]
    stats = [data["benchmarks"][k]["latency_stats"] for k, _ in order]
    labels = [lbl for _, lbl in order]

    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    x = range(len(stats))
    means = [s["mean_ms"] for s in stats]
    p95 = [s["p95_ms"] for s in stats]
    p99 = [s["p99_ms"] for s in stats]
    mins = [s["min_ms"] for s in stats]
    maxs = [s["max_ms"] for s in stats]

    for i in range(len(stats)):
        ax.plot([i, i], [mins[i], maxs[i]], color=GRAY, lw=1.0, zorder=1)
        ax.plot([i - 0.1, i + 0.1], [mins[i]] * 2, color=GRAY, lw=1.0)
        ax.plot([i - 0.1, i + 0.1], [maxs[i]] * 2, color=GRAY, lw=1.0)
    ax.scatter(x, means, s=46, color="#2f6db3", zorder=3, label="mean")
    ax.scatter(x, p95, s=34, marker="D", color="#c9803a", zorder=3, label="p95")
    ax.scatter(x, p99, s=40, marker="^", color="#a54242", zorder=3, label="p99")
    ax.plot([], [], color=GRAY, lw=1.0, label="min–max")

    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_ylabel("Detection latency (ms)")
    ax.set_ylim(0, max(maxs) * 1.12)
    ax.legend(frameon=False, loc="upper right", ncols=4)
    ax.grid(axis="y", alpha=0.25, lw=0.5)
    n = data["aggregate"]["total_samples_processed"]
    run_date = data["timestamp"].split("T", maxsplit=1)[0]
    ax.set_title(f"Tier-2 prompt-layer latency — {run_date} (N={n}, single run)",
                 fontsize=9, fontweight="normal", color=INK)
    ax.text(
        0.5,
        -0.26,
        f"Source: {RESULTS.relative_to(ROOT)} · host-dependent timing",
        transform=ax.transAxes,
        ha="center",
        fontsize=6.2,
        color=GRAY,
    )
    fig.savefig(OUT / "figure_3.png"); fig.savefig(OUT / "figure_3.pdf")
    plt.close(fig)


def figure_4_ablation():
    """Plot the archived Tier-1 ablation transcription without causal overclaiming."""
    with TIER1_ABLATION.open(encoding="utf-8") as handle:
        evidence = json.load(handle)
    rows = [(row["label"], row["detection_rate_percent"]) for row in evidence["rows"]]
    labels = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]

    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    ax.set_title(
        "Tier-1 version-of-record ablation (not reproduced by the open benchmark)",
        fontsize=8.5,
        pad=10,
    )
    colors = ["#b8c4cf"] * len(vals)
    colors[-1] = "#2f6db3"          # full system
    colors[0] = "#c9803a"           # best single layer
    bars = ax.barh(labels, vals, color=colors, height=0.62, edgecolor="white")
    for b, v in zip(bars, vals):
        ax.text(v - 0.6, b.get_y() + b.get_height() / 2, f"{v:.1f}",
                va="center", ha="right", fontsize=8, color="white", fontweight="bold")

    ax.set_xlim(0, 100)
    ax.set_xlabel("Detection rate (%) — production-scale evaluation")
    ax.axvline(76.3, color="#c9803a", lw=0.8, ls=(0, (3, 3)), alpha=0.7)
    ax.axvline(94.7, color="#2f6db3", lw=0.8, ls=(0, (3, 3)), alpha=0.7)
    ax.annotate("", xy=(94.7, 5.42), xytext=(76.3, 5.42),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    ax.text(
        (94.7 + 76.3) / 2,
        5.58,
        "+18.4 pp: full system vs best single layer",
        ha="center",
        fontsize=7.8,
        color=INK,
    )
    ax.set_ylim(-0.55, 6.1)
    ax.grid(axis="x", alpha=0.25, lw=0.5)
    ax.text(
        0.5,
        -0.31,
        "Archived comparison; not causal isolation · source DOI 10.22399/ijcesen.4869 · sample counts/CIs unavailable",
        transform=ax.transAxes,
        ha="center",
        fontsize=6.2,
        color=GRAY,
    )
    fig.savefig(OUT / "figure_4.png"); fig.savefig(OUT / "figure_4.pdf")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    figure_1_architecture()
    figure_2_tee_protocol()
    figure_3_latency()
    figure_4_ablation()
    for f in sorted(OUT.glob("figure_*.p*")):
        print(f.relative_to(ROOT), f.stat().st_size)
