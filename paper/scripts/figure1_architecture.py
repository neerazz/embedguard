#!/usr/bin/env python3
"""Figure 1 — EmbedGuard architecture as an attack-vs-defense story.

Design brief (modeled on PoisonedRAG Fig.1 / RevPRAG-class figures):
- Concrete running example woven through the figure, not abstract boxes.
- Two contrasting paths: benign query (blue) and poisoned document (red).
- Each detection layer shows its check AND the signal it emits for the
  worked example from Section 3.6 (0.1, 1.0, 0.8, 0.7 -> ThreatScore 1.225).
- Correlation engine shows the actual fusion arithmetic ending in BLOCK.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "images"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "figure.dpi": 200,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.06,
})

INK = "#16213e"
GRAY = "#7a828e"
RED = "#b03a3a"
RED_BG = "#fbe9e7"
BLUE = "#2f6db3"
BLUE_BG = "#e8f0fa"
GREEN = "#2e7d4f"
GREEN_BG = "#e6f2ea"
AMBER = "#b07f2e"
AMBER_BG = "#fdf3e0"


def box(ax, x, y, w, h, fc, ec=INK, lw=1.0, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.008,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw))


def txt(ax, x, y, s, size=8, color=INK, ha="center", va="center", weight="normal",
        style="normal", ls=1.3):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontweight=weight, style=style, linespacing=ls)


def arrow(ax, x0, y0, x1, y1, color=INK, lw=1.2, style="-|>", ls="-", ms=11):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, ls=ls,
                                 mutation_scale=ms, color=color, lw=lw,
                                 shrinkA=1.5, shrinkB=1.5))


def person(ax, x, y, s, color):
    ax.add_patch(Circle((x, y + s * 0.62), s * 0.30, fc=color, ec="none"))
    ax.add_patch(FancyBboxPatch((x - s * 0.42, y - s * 0.28), s * 0.84, s * 0.62,
                                boxstyle="round,pad=0.005,rounding_size=0.04",
                                fc=color, ec="none"))


def doc_card(ax, x, y, w, h, fc, ec, lines, lw=0.9, fold=0.14):
    """A little document glyph with text lines."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.008",
                                fc=fc, ec=ec, lw=lw))
    for i, (frac, c) in enumerate(lines):
        yy = y + h - (i + 1) * h / (len(lines) + 1)
        ax.plot([x + w * 0.10, x + w * (0.10 + frac)], [yy, yy], color=c, lw=1.4,
                solid_capstyle="round")


def main():
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    ax.set_xlim(0, 12.9)
    ax.set_ylim(0, 8.3)
    ax.axis("off")

    # ============ TOP BAND: the RAG pipeline with the attack ============
    band_y = 5.55

    # benign user (left)
    person(ax, 0.75, 7.0, 0.5, BLUE)
    txt(ax, 0.75, 6.45, "User", 7.5, GRAY)
    box(ax, 0.18, band_y, 2.5, 0.62, BLUE_BG, BLUE, 1.0)
    txt(ax, 1.43, band_y + 0.31, '"What is our refund policy?"', 7.2, BLUE, style="italic")
    arrow(ax, 0.75, 6.72, 0.75, band_y + 0.66, BLUE, 1.2)

    # attacker (right top) injecting poisoned doc into corpus
    person(ax, 11.85, 7.0, 0.5, RED)
    txt(ax, 11.85, 7.85, "Attacker", 7.5, RED)
    doc_card(ax, 10.1, 6.85, 0.8, 0.9, "white", RED,
             [(0.75, "#c9c9c9"), (0.6, "#c9c9c9"), (0.7, RED), (0.5, "#c9c9c9")])
    txt(ax, 10.5, 6.6, "fluent poisoned document", 6.6, RED)
    arrow(ax, 11.42, 7.15, 10.95, 7.25, RED, 1.1)

    # corpus + embedding + retrieval + LLM pipeline
    box(ax, 7.35, band_y, 2.0, 0.85, "#f4f5f7", INK, 1.0)
    doc_card(ax, 7.5, band_y + 0.12, 0.5, 0.6, "white", GRAY, [(0.7, "#c9c9c9"), (0.55, "#c9c9c9")])
    doc_card(ax, 8.08, band_y + 0.12, 0.5, 0.6, "white", GRAY, [(0.65, "#c9c9c9"), (0.6, "#c9c9c9")])
    doc_card(ax, 8.66, band_y + 0.12, 0.5, 0.6, RED_BG, RED, [(0.7, RED), (0.5, RED)])
    txt(ax, 8.35, band_y + 1.02, "Knowledge corpus", 7.5, INK)
    arrow(ax, 10.15, 6.82, 9.0, band_y + 0.92, RED, 1.3)     # poison lands in corpus

    box(ax, 10.0, band_y, 1.35, 0.85, "#f4f5f7", INK, 1.0)
    txt(ax, 10.68, band_y + 0.55, "Embed +", 7.5, INK)
    txt(ax, 10.68, band_y + 0.28, "index", 7.5, INK)
    arrow(ax, 9.4, band_y + 0.42, 9.98, band_y + 0.42, INK, 1.1)

    box(ax, 11.75, band_y, 1.05, 0.85, "#f4f5f7", INK, 1.0)
    txt(ax, 12.27, band_y + 0.55, "LLM", 8, INK, weight="bold")
    txt(ax, 12.27, band_y + 0.26, "generate", 6.8, GRAY)
    arrow(ax, 11.37, band_y + 0.42, 11.73, band_y + 0.42, INK, 1.1)

    # query joins pipeline
    box(ax, 3.1, band_y, 2.1, 0.85, "#f4f5f7", INK, 1.0)
    txt(ax, 4.15, band_y + 0.55, "Retrieve top-k", 7.5, INK)
    txt(ax, 4.15, band_y + 0.26, "similarity search", 6.8, GRAY)
    arrow(ax, 2.7, band_y + 0.31, 3.08, band_y + 0.31, BLUE, 1.2)
    # retrieval pulls from index (leftward)
    arrow(ax, 9.98, band_y + 0.62, 5.22, band_y + 0.62, GRAY, 1.0, ls=(0, (4, 3)))
    txt(ax, 6.2, band_y + 0.92, "poisoned embedding retrieved\nfor the benign query", 6.6, RED, style="italic", ls=1.15)
    # retrieved set forward to LLM
    arrow(ax, 5.22, band_y + 0.2, 11.73, band_y + 0.2, RED, 1.2, ls=(0, (5, 2)))

    # ============ DETECTION LAYERS (middle band) ============
    ly = 3.15
    lh = 1.55
    lw_ = 2.55
    xs = [0.35, 3.35, 6.35, 9.35]
    layers = [
        ("L1 · Prompt analysis", "81-pattern classifier\non the user query",
         '"refund policy" — clean', GREEN, GREEN_BG, "s\u2081 = 0.1", 0.35),
        ("L2 · Embedding attestation", "TEE certificate check\n(SEV-SNP signed)",
         "poisoned vector has\nNO valid certificate", RED, RED_BG, "s\u2082 = 1.0", 0.75),
        ("L3 · Retrieval analysis", "PCA subspace + KL vs\nhistorical distribution",
         "similarity distribution\nshifted ($D_{KL} > \\tau$)", RED, RED_BG, "s\u2083 = 0.8", 0.50),
        ("L4 · Output verification", "stability under K=5\nretrieval perturbations",
         "answer flips when the\npoisoned doc is ablated", AMBER, AMBER_BG, "s\u2084 = 0.7", 0.20),
    ]
    for (title, mech, finding, fc_c, fc_bg, sig, beta), x in zip(layers, xs):
        box(ax, x, ly, lw_, lh, "white", INK, 1.0)
        box(ax, x, ly + lh - 0.38, lw_, 0.38, "#eef0f3", INK, 0.8, r=0.01)
        txt(ax, x + lw_ / 2, ly + lh - 0.19, title, 7.6, INK, weight="bold")
        txt(ax, x + lw_ / 2, ly + lh - 0.66, mech, 6.6, GRAY, ls=1.25)
        box(ax, x + 0.10, ly + 0.10, lw_ - 0.20, 0.52, fc_bg, fc_c, 0.9, r=0.012)
        txt(ax, x + lw_ / 2, ly + 0.36, finding, 6.4, fc_c, ls=1.2)
        # signal chip
        box(ax, x + lw_ - 0.78, ly - 0.30, 0.72, 0.34, "white", fc_c, 1.1, r=0.012)
        txt(ax, x + lw_ - 0.42, ly - 0.13, sig, 7.2, fc_c, weight="bold")
        txt(ax, x + 0.06, ly - 0.16, f"\u03b2 = {beta:.2f}", 6.8, GRAY, ha="left")

    # taps from pipeline into layers
    arrow(ax, 1.43, band_y - 0.03, 1.63, ly + lh + 0.03, GRAY, 0.9)
    arrow(ax, 10.68, band_y - 0.03, 4.63, ly + lh + 0.03, GRAY, 0.9)
    arrow(ax, 4.15, band_y - 0.03, 7.63, ly + lh + 0.03, GRAY, 0.9)
    arrow(ax, 12.27, band_y - 0.03, 10.63, ly + lh + 0.03, GRAY, 0.9)

    # ============ CORRELATION ENGINE (bottom band) ============
    ey = 0.55
    box(ax, 2.6, ey, 7.7, 1.55, "#f7f8fa", INK, 1.2)
    txt(ax, 6.45, ey + 1.28, "Threat Correlation Engine — weighted signal fusion", 8.2, INK, weight="bold")
    txt(ax, 6.45, ey + 0.82,
        "ThreatScore = 0.35(0.1) + 0.75(1.0) + 0.50(0.8) + 0.20(0.7) = 1.225",
        8.2, INK)
    txt(ax, 6.45, ey + 0.38,
        "each signal is weak or moderate alone — only the correlation crosses the block threshold (0.85)",
        6.8, GRAY, style="italic")

    # signals converge
    for x in xs:
        arrow(ax, x + lw_ - 0.42, ly - 0.32, 6.45, ey + 1.58, GRAY, 0.9)

    # verdict
    box(ax, 10.75, ey + 0.35, 1.85, 0.85, RED_BG, RED, 1.6, r=0.02)
    txt(ax, 11.67, ey + 0.92, "BLOCK", 10.5, RED, weight="bold")
    txt(ax, 11.67, ey + 0.57, "1.225 \u2265 0.85", 7.2, RED)
    arrow(ax, 10.32, ey + 0.77, 10.72, ey + 0.77, RED, 1.6)
    txt(ax, 11.67, ey - 0.02, "safe fallback response to user", 6.6, GRAY)

    # legend
    ax.plot([0.35, 0.75], [0.28, 0.28], color=BLUE, lw=1.6)
    txt(ax, 0.83, 0.28, "benign query path", 6.8, GRAY, ha="left")
    ax.plot([0.35, 0.75], [0.02, 0.02], color=RED, lw=1.6, ls=(0, (5, 2)))
    txt(ax, 0.83, 0.02, "poisoned document path", 6.8, GRAY, ha="left")

    fig.savefig(OUT / "figure_1.png")
    fig.savefig(OUT / "figure_1.pdf")
    plt.close(fig)
    print("figure_1 written")


if __name__ == "__main__":
    main()
