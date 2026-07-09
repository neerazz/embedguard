#!/usr/bin/env python3
"""EmbedGuard paper figures.

Figures 1-2 are drawn diagrams (matplotlib primitives, vector output).
Figures 3-4 are plotted from data: Figure 3 from the committed benchmark
results JSON (results/benchmark_results_20260125_005427.json), Figure 4
from the Tier-1 ablation table in the published article (Section 4.1).

Usage:  python3 paper/scripts/generate_figures.py
Output: paper/images/figure_{1,2,3,4}.{png,pdf}
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "images"
RESULTS = ROOT / "results" / "benchmark_results_20260125_005427.json"

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
LAYERS = [  # name, weight, latency label, fill
    ("Layer 1 · Prompt Injection Detection\n81-pattern classifier", 0.35, "0.04 ms", "#dbe7f4"),
    ("Layer 2 · Embedding Attestation\nTEE (AMD SEV-SNP) certificate check", 0.75, "0.3 ms/doc", "#dcefdd"),
    ("Layer 3 · Retrieval Analysis\nincremental PCA + KL divergence", 0.50, "15.2 ms", "#fdeeda"),
    ("Layer 4 · Output Verification\nperturbation stability (flagged only)", 0.20, "6.3 ms", "#ece2f4"),
]


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
    """Cross-layer pipeline with signal taps into the correlation engine."""
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.1); ax.axis("off")

    # untrusted inputs
    _box(ax, 0.25, 6.25, 2.5, 0.65, "User query", "#f6f7f9")
    _box(ax, 3.05, 6.25, 2.5, 0.65, "Document corpus\n(untrusted)", "#f6f7f9", fontsize=8)
    ax.text(2.9, 7.05, "Untrusted input", fontsize=8, color=GRAY, ha="center", style="italic")

    # detection layers
    ys = [4.85, 3.65, 2.45, 1.25]
    for (label, w, lat, fc), y in zip(LAYERS, ys):
        _box(ax, 0.25, y, 5.3, 0.95, label, fc, fontsize=8.3)
        ax.text(5.72, y + 0.62, f"β = {w:.2f}", fontsize=8, color=INK, ha="left")
        ax.text(5.72, y + 0.28, lat, fontsize=7.5, color=GRAY, ha="left")
        _arrow(ax, 6.6, y + 0.475, 7.35, y + 0.475, color=GRAY, lw=1.0)

    _arrow(ax, 1.5, 6.25, 1.5, 5.8)
    _arrow(ax, 4.3, 6.25, 4.3, 5.8)
    for y0, y1 in zip(ys[:-1], ys[1:]):
        _arrow(ax, 2.9, y0, 2.9, y1 + 0.95)

    # correlation engine
    _box(ax, 7.35, 1.25, 2.4, 4.55, "", "#f1f3f6")
    ax.text(8.55, 5.25, "Threat Correlation\nEngine", ha="center", fontsize=9,
            fontweight="bold", color=INK, linespacing=1.3)
    ax.text(8.55, 4.15, r"ThreatScore = $\Sigma_i\,\beta_i s_i$", ha="center", fontsize=8.5, color=INK)
    ax.text(8.55, 3.45, "flag ≥ 0.70\nblock ≥ 0.85", ha="center", fontsize=8, color=GRAY, linespacing=1.4)

    # decisions
    _arrow(ax, 8.55, 1.25, 8.55, 0.82)
    for x, lbl, fc in [(6.0, "ALLOW", "#dcefdd"), (7.7, "FLAG", "#fdeeda"), (9.4, "BLOCK", "#f6dbdb")]:
        _box(ax, x - 0.72, 0.1, 1.44, 0.55, lbl, fc, fontsize=8, weight="bold")
    _arrow(ax, 8.55, 0.82, 6.0, 0.65, color=GRAY, lw=0.9)
    _arrow(ax, 8.55, 0.82, 7.7, 0.65, color=GRAY, lw=0.9)
    _arrow(ax, 8.55, 0.82, 9.4, 0.65, color=GRAY, lw=0.9)
    ax.text(4.4, 0.38, "passive / gated / active mode", fontsize=7.5, color=GRAY, ha="right", style="italic")

    fig.savefig(OUT / "figure_1.png"); fig.savefig(OUT / "figure_1.pdf")
    plt.close(fig)


def figure_2_tee_protocol():
    """TEE attestation as a sequence diagram: ingestion vs retrieval time."""
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.8); ax.axis("off")

    actors = [(1.3, "Document\nsource"), (4.0, "TEE enclave\n(SEV-SNP)"),
              (6.7, "Vector store"), (9.0, "Retrieval\nverifier")]
    for x, name in actors:
        _box(ax, x - 0.85, 6.0, 1.7, 0.7, name, "#f1f3f6", fontsize=8)
        ax.plot([x, x], [0.55, 6.0], color=GRAY, lw=0.8, ls=(0, (4, 3)), zorder=0)

    def msg(y, x0, x1, text, above=True):
        _arrow(ax, x0, y, x1, y, lw=1.0)
        ax.text((x0 + x1) / 2, y + (0.13 if above else -0.3), text,
                ha="center", fontsize=7.6, color=INK)

    ax.text(0.12, 5.55, "Ingestion", fontsize=8, color=GRAY, rotation=90, va="top")
    msg(5.35, 1.3, 4.0, "document D")
    # enclave internal note
    _box(ax, 2.95, 4.35, 2.1, 0.75,
         "embed inside enclave\ncert = sign(H(D), H(model),\nE, T, PCRs)", "#dcefdd", fontsize=6.8)
    msg(3.95, 4.0, 6.7, "E + attestation cert")

    ax.plot([0.1, 9.9], [3.45, 3.45], color=GRAY, lw=0.6)
    ax.text(0.12, 3.1, "Retrieval", fontsize=8, color=GRAY, rotation=90, va="top")
    msg(2.85, 9.0, 6.7, "query top-k", above=True)
    msg(2.35, 6.7, 9.0, "candidates + certs")
    _box(ax, 7.9, 1.15, 2.0, 0.85,
         "verify: signature,\nmodel hash, validity\nwindow, platform PCRs", "#dbe7f4", fontsize=6.8)
    msg(0.85, 9.0, 6.7, "reject unverified embeddings", above=False)

    ax.text(5.0, 6.75, "", fontsize=1)
    fig.savefig(OUT / "figure_2.png"); fig.savefig(OUT / "figure_2.pdf")
    plt.close(fig)


def figure_3_latency():
    """Per-dataset latency stats plotted from the committed benchmark JSON."""
    data = json.loads(RESULTS.read_text())
    order = [("injection", "Injection\nattacks"), ("nq", "Natural\nQuestions"),
             ("hotpotqa", "HotpotQA"), ("msmarco", "MS-MARCO")]
    stats = [data["benchmarks"][k]["latency_stats"] for k, _ in order]
    labels = [lbl for _, lbl in order]

    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    x = range(len(stats))
    means = [s["mean_ms"] for s in stats]
    p95 = [s["p95_ms"] for s in stats]
    p99 = [s["p99_ms"] for s in stats]
    mins = [s["min_ms"] for s in stats]
    maxs = [s["max_ms"] for s in stats]

    for i, s in enumerate(stats):
        ax.plot([i, i], [mins[i], maxs[i]], color=GRAY, lw=1.0, zorder=1)
        ax.plot([i - 0.1, i + 0.1], [mins[i]] * 2, color=GRAY, lw=1.0)
        ax.plot([i - 0.1, i + 0.1], [maxs[i]] * 2, color=GRAY, lw=1.0)
    ax.scatter(x, means, s=46, color="#2f6db3", zorder=3, label="mean")
    ax.scatter(x, p95, s=34, marker="D", color="#c9803a", zorder=3, label="p95")
    ax.scatter(x, p99, s=40, marker="^", color="#a54242", zorder=3, label="p99")

    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_ylabel("Detection latency (ms)")
    ax.set_ylim(0, 0.185)
    ax.legend(frameon=False, loc="upper right", ncols=3)
    ax.grid(axis="y", alpha=0.25, lw=0.5)
    n = data["aggregate"]["total_samples_processed"]
    ax.set_title(f"Prompt-layer detection latency by dataset (N={n}, single run)",
                 fontsize=9, fontweight="normal", color=INK)
    fig.savefig(OUT / "figure_3.png"); fig.savefig(OUT / "figure_3.pdf")
    plt.close(fig)


def figure_4_ablation():
    """Tier-1 cross-layer ablation (values from the published article, Sec. 4.1)."""
    rows = [
        ("Full system (4 layers)", 94.7),
        ("w/o output layer", 91.2),
        ("w/o prompt layer", 89.8),
        ("w/o retrieval layer", 87.4),
        ("w/o embedding TEE", 84.6),
        ("Embedding only\n(best single layer)", 76.3),
    ]
    labels = [r[0] for r in rows][::-1]
    vals = [r[1] for r in rows][::-1]

    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    colors = ["#b8c4cf"] * len(vals)
    colors[-1] = "#2f6db3"          # full system
    colors[0] = "#c9803a"           # best single layer
    bars = ax.barh(labels, vals, color=colors, height=0.62, edgecolor="white")
    for b, v in zip(bars, vals):
        ax.text(v - 0.6, b.get_y() + b.get_height() / 2, f"{v:.1f}",
                va="center", ha="right", fontsize=8, color="white", fontweight="bold")

    ax.set_xlim(70, 100)
    ax.set_xlabel("Detection rate (%) — production-scale evaluation")
    ax.axvline(76.3, color="#c9803a", lw=0.8, ls=(0, (3, 3)), alpha=0.7)
    ax.axvline(94.7, color="#2f6db3", lw=0.8, ls=(0, (3, 3)), alpha=0.7)
    ax.annotate("", xy=(94.7, 5.42), xytext=(76.3, 5.42),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    ax.text((94.7 + 76.3) / 2, 5.58, "+18.4 pp from cross-layer correlation",
            ha="center", fontsize=8, color=INK)
    ax.set_ylim(-0.55, 6.1)
    ax.grid(axis="x", alpha=0.25, lw=0.5)
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
