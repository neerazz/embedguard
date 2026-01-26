#!/usr/bin/env python3
"""
EmbedGuard Paper Figures Generator - Professional Academic Style
Generates all 5 figures for the PeerJ Computer Science submission.

Style: IEEE/ACM academic standard
- Grayscale-friendly colors
- Larger fonts (11-12pt minimum)
- Clean, minimal layout
- Sans-serif for clarity

Usage:
    python generate_all_figures.py

Output:
    - figure1_architecture.png/pdf
    - figure2_tee_protocol.png/pdf
    - figure3_comparative_detection.png/pdf
    - figure4_ablation_study.png/pdf
    - figure5_latency_breakdown.png/pdf
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

# Professional academic style defaults
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.15,
    'axes.linewidth': 1.0,
    'axes.edgecolor': '#333333',
    'axes.grid': False,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.5,
})

# Professional color palette (grayscale-friendly)
COLORS = {
    'primary': '#2C3E50',      # Dark blue-gray
    'secondary': '#7F8C8D',    # Medium gray
    'accent1': '#3498DB',      # Blue
    'accent2': '#E74C3C',      # Red (for emphasis)
    'light1': '#ECF0F1',       # Light gray
    'light2': '#BDC3C7',       # Medium light gray
    'light3': '#95A5A6',       # Darker light gray
    'success': '#27AE60',      # Green
    'warning': '#F39C12',      # Orange
}

# Grayscale-friendly layer colors
LAYER_COLORS = ['#D5E8D4', '#DAE8FC', '#FFE6CC', '#F8CECC']  # Green, Blue, Orange, Red (light)
LAYER_BORDERS = ['#82B366', '#6C8EBF', '#D79B00', '#B85450']


def figure1_architecture():
    """
    Figure 1: EmbedGuard cross-layer detection architecture.
    Professional academic style with clean boxes and arrows.
    """
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # Layer boxes (left side)
    layers = [
        ('Layer 1: Prompt\nInjection Detection', 'β₁=0.35', 5.3),
        ('Layer 2: TEE Embedding\nAttestation', 'β₂=0.75', 4.0),
        ('Layer 3: Retrieval\nDistributional Analysis', 'β₃=0.50', 2.7),
        ('Layer 4: Output\nConsistency Verification', 'β₄=0.20', 1.4)
    ]

    for i, (name, weight, y) in enumerate(layers):
        box = FancyBboxPatch((0.4, y), 3.0, 0.85, boxstyle="round,pad=0.03,rounding_size=0.1",
                            facecolor=LAYER_COLORS[i], edgecolor=LAYER_BORDERS[i], linewidth=1.5)
        ax.add_patch(box)
        ax.text(1.9, y + 0.42, name, ha='center', va='center', fontsize=10, fontweight='bold')
        ax.text(3.2, y + 0.42, weight, ha='left', va='center', fontsize=9,
                fontfamily='monospace', color='#555')

    # Correlation Engine (center)
    engine_box = FancyBboxPatch((4.3, 2.2), 2.4, 2.6, boxstyle="round,pad=0.05,rounding_size=0.15",
                                facecolor='#E8DAEF', edgecolor='#8E44AD', linewidth=2)
    ax.add_patch(engine_box)
    ax.text(5.5, 4.3, 'Threat Correlation', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(5.5, 3.85, 'Engine', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(5.5, 3.2, 'ThreatScore =', ha='center', va='center', fontsize=10)
    ax.text(5.5, 2.8, 'Σ βᵢ × signalᵢ', ha='center', va='center', fontsize=10, fontfamily='monospace')

    # Arrows from layers to engine
    for i, (_, _, y) in enumerate(layers):
        ax.annotate('', xy=(4.3, 3.5), xytext=(3.4, y + 0.42),
                   arrowprops=dict(arrowstyle='->', color='#555', lw=1.2,
                                  connectionstyle='arc3,rad=0.1'))

    # Deployment Modes (right side)
    mode_colors = ['#F5F5F5', '#FFF9C4', '#FFCCBC']
    mode_borders = ['#9E9E9E', '#FBC02D', '#E64A19']
    modes = [
        ('Passive Mode\n(Logging)', 5.0),
        ('Gated Mode\n(Human Review)', 3.5),
        ('Active Mode\n(Auto-Block)', 2.0)
    ]

    for i, (name, y) in enumerate(modes):
        box = FancyBboxPatch((7.6, y), 2.0, 0.85, boxstyle="round,pad=0.03,rounding_size=0.1",
                            facecolor=mode_colors[i], edgecolor=mode_borders[i], linewidth=1.2)
        ax.add_patch(box)
        ax.text(8.6, y + 0.42, name, ha='center', va='center', fontsize=9)

    # Arrow from engine to modes
    ax.annotate('', xy=(7.6, 3.5), xytext=(6.7, 3.5),
               arrowprops=dict(arrowstyle='->', color='#8E44AD', lw=2))

    # Section labels
    ax.text(1.9, 6.4, 'Detection Layers', ha='center', fontsize=11, fontweight='bold', color='#333')
    ax.text(8.6, 6.0, 'Deployment', ha='center', fontsize=11, fontweight='bold', color='#333')
    ax.text(8.6, 5.7, 'Modes', ha='center', fontsize=11, fontweight='bold', color='#333')

    # Title
    ax.text(5, 6.7, 'EmbedGuard Cross-Layer Detection Architecture',
            ha='center', va='center', fontsize=14, fontweight='bold')

    plt.savefig('figure1_architecture.png', dpi=300, facecolor='white', edgecolor='none')
    plt.savefig('figure1_architecture.pdf', facecolor='white', edgecolor='none')
    plt.close()
    print("✓ Generated figure1_architecture.png/pdf")


def figure2_tee_protocol():
    """
    Figure 2: TEE-based embedding attestation protocol.
    Clean flow diagram with numbered steps.
    """
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.5)
    ax.axis('off')

    # Document input
    doc_box = FancyBboxPatch((0.3, 1.5), 1.6, 1.4, boxstyle="round,pad=0.05",
                             facecolor='#DAE8FC', edgecolor='#6C8EBF', linewidth=1.5)
    ax.add_patch(doc_box)
    ax.text(1.1, 2.4, 'Document D', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(1.1, 2.0, 'Hash: H(D)', ha='center', va='center', fontsize=9, style='italic')

    # TEE Enclave
    tee_box = FancyBboxPatch((2.8, 0.8), 3.4, 2.8, boxstyle="round,pad=0.08",
                             facecolor='#D5E8D4', edgecolor='#82B366', linewidth=2)
    ax.add_patch(tee_box)
    ax.text(4.5, 3.3, 'TEE Enclave', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(4.5, 2.95, '(AMD SEV-SNP)', ha='center', va='center', fontsize=9, color='#555')

    # Steps inside TEE
    steps = [
        '1. Load embedding model',
        '2. Generate embedding E',
        '3. Sign: σ = Sign(H(D)||E||T)',
        '4. Output certificate'
    ]
    for i, step in enumerate(steps):
        ax.text(4.5, 2.5 - i*0.4, step, ha='center', fontsize=9)

    # Certificate
    cert_box = FancyBboxPatch((7.0, 1.5), 1.8, 1.4, boxstyle="round,pad=0.05",
                              facecolor='#FFE6CC', edgecolor='#D79B00', linewidth=1.5)
    ax.add_patch(cert_box)
    ax.text(7.9, 2.5, 'Attestation', ha='center', fontsize=10, fontweight='bold')
    ax.text(7.9, 2.15, 'Certificate', ha='center', fontsize=10, fontweight='bold')
    ax.text(7.9, 1.8, '{E, σ, PCR}', ha='center', fontsize=9, fontfamily='monospace')

    # Verification
    verify_box = FancyBboxPatch((9.4, 1.5), 1.3, 1.4, boxstyle="round,pad=0.05",
                                facecolor='#E8DAEF', edgecolor='#8E44AD', linewidth=1.5)
    ax.add_patch(verify_box)
    ax.text(10.05, 2.35, 'Verify', ha='center', fontsize=10, fontweight='bold')
    ax.text(10.05, 1.95, 'Valid?', ha='center', fontsize=10)

    # Arrows with labels
    arrows = [
        ((1.9, 2.2), (2.8, 2.2), 'Input'),
        ((6.2, 2.2), (7.0, 2.2), 'Sign'),
        ((8.8, 2.2), (9.4, 2.2), 'Check'),
    ]
    for (start, end, label) in arrows:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
        mid_x = (start[0] + end[0]) / 2
        ax.text(mid_x, 2.5, label, ha='center', fontsize=8, color='#666')

    # Title
    ax.text(5.5, 4.2, 'TEE-Based Embedding Attestation Protocol',
            ha='center', va='center', fontsize=13, fontweight='bold')

    # Caption
    ax.text(5.5, 0.3, 'Hardware-isolated computation provides cryptographic integrity guarantees',
            ha='center', fontsize=9, style='italic', color='#555')

    plt.savefig('figure2_tee_protocol.png', dpi=300, facecolor='white', edgecolor='none')
    plt.savefig('figure2_tee_protocol.pdf', facecolor='white', edgecolor='none')
    plt.close()
    print("✓ Generated figure2_tee_protocol.png/pdf")


def figure3_comparative_detection():
    """
    Figure 3: Comparative detection rates.
    Professional grouped bar chart with clear annotations.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Data
    systems = ['EmbedGuard\n(Ours)', 'RAGuard', 'RobustRAG', 'TrustRAG']
    baseline = [94.7, 87.2, 82.9, 79.3]
    adaptive = [89.3, 61.4, 58.7, 54.2]

    x = np.arange(len(systems))
    width = 0.35

    # Professional colors (grayscale-friendly)
    color_baseline = '#4A90D9'  # Blue
    color_adaptive = '#D97B4A'  # Orange

    # Bars with edge
    bars1 = ax.bar(x - width/2, baseline, width, label='Baseline Attacks',
                   color=color_baseline, edgecolor='#2C5282', linewidth=1)
    bars2 = ax.bar(x + width/2, adaptive, width, label='Adaptive Attacks',
                   color=color_adaptive, edgecolor='#9C4221', linewidth=1)

    # Value labels
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                   xytext=(0, 3), textcoords="offset points", ha='center', fontsize=9)

    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                   xytext=(0, 3), textcoords="offset points", ha='center', fontsize=9)

    # Improvement bracket
    ax.annotate('', xy=(0.175, 89.3), xytext=(1.175, 61.4),
               arrowprops=dict(arrowstyle='<->', color='#C0392B', lw=2))
    ax.text(0.7, 76, '+27.9pp', ha='center', fontsize=11, fontweight='bold',
            color='#C0392B', bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

    # Formatting
    ax.set_ylabel('Detection Rate (%)', fontweight='bold')
    ax.set_xlabel('Defense System', fontweight='bold')
    ax.set_title('Comparative Detection Performance', fontsize=13, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(systems)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', framealpha=0.95)
    ax.yaxis.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    # Note
    ax.text(0.02, -0.14, '*Baseline implementations based on published descriptions',
            transform=ax.transAxes, fontsize=8, style='italic', color='#666')

    plt.tight_layout()
    plt.savefig('figure3_comparative_detection.png', dpi=300, facecolor='white', edgecolor='none')
    plt.savefig('figure3_comparative_detection.pdf', facecolor='white', edgecolor='none')
    plt.close()
    print("✓ Generated figure3_comparative_detection.png/pdf")


def figure4_ablation_study():
    """
    Figure 4: Ablation study - layer contribution analysis.
    Clean horizontal bar chart with gradient coloring.
    """
    fig, ax = plt.subplots(figsize=(9, 4.5))

    # Data
    configs = [
        'Embedding Only\n(Best Single-Layer)',
        'w/o TEE Attestation',
        'w/o Retrieval Layer',
        'w/o Prompt Layer',
        'w/o Output Layer',
        'Full System\n(4 Layers)'
    ]
    detection_rates = [76.3, 84.6, 87.4, 89.8, 91.2, 94.7]
    deltas = ['-18.4pp', '-10.1pp', '-7.3pp', '-4.9pp', '-3.5pp', '—']

    # Color gradient from red to green
    colors = ['#E74C3C', '#E67E22', '#F1C40F', '#2ECC71', '#27AE60', '#1E8449']

    y_pos = np.arange(len(configs))

    bars = ax.barh(y_pos, detection_rates, color=colors, edgecolor='#333', linewidth=0.8, height=0.7)

    # Value labels
    for i, (bar, delta) in enumerate(zip(bars, deltas)):
        width = bar.get_width()
        label_color = '#333' if i < 3 else '#fff'
        ax.text(width - 2, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}%', va='center', ha='right', fontsize=10,
                fontweight='bold', color=label_color)
        ax.text(width + 1.5, bar.get_y() + bar.get_height()/2,
                f'({delta})', va='center', fontsize=9, color='#666')

    # Reference lines
    ax.axvline(x=76.3, color='#E74C3C', linestyle='--', alpha=0.5, linewidth=1)
    ax.axvline(x=94.7, color='#1E8449', linestyle='--', alpha=0.5, linewidth=1)

    # Improvement annotation
    ax.annotate('', xy=(94.7, 5.7), xytext=(76.3, 5.7),
               arrowprops=dict(arrowstyle='<->', color='#C0392B', lw=2))
    ax.text(85.5, 5.9, '+18.4pp from cross-layer correlation',
            ha='center', fontsize=10, fontweight='bold', color='#C0392B')

    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(configs)
    ax.set_xlabel('Detection Rate (%)', fontweight='bold')
    ax.set_title('Ablation Study: Layer Contribution Analysis', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlim(0, 108)
    ax.xaxis.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig('figure4_ablation_study.png', dpi=300, facecolor='white', edgecolor='none')
    plt.savefig('figure4_ablation_study.pdf', facecolor='white', edgecolor='none')
    plt.close()
    print("✓ Generated figure4_ablation_study.png/pdf")


def figure5_latency_breakdown():
    """
    Figure 5: Latency breakdown by detection layer.
    Professional dual-panel: pie chart + horizontal bar.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # Data
    layers = ['Prompt\nAnalysis', 'TEE\nAttestation', 'Retrieval\nAnalysis',
              'Output\nVerification', 'Correlation\nEngine']
    latencies = [4.2, 12.8, 23.5, 6.3, 4.2]

    # Professional colors
    colors = ['#DAE8FC', '#D5E8D4', '#FFE6CC', '#F8CECC', '#E8DAEF']
    edge_colors = ['#6C8EBF', '#82B366', '#D79B00', '#B85450', '#8E44AD']

    # Pie chart
    wedges, texts, autotexts = ax1.pie(
        latencies, labels=None, autopct='%1.1f%%',
        colors=colors,
        wedgeprops={'edgecolor': '#333', 'linewidth': 0.8},
        textprops={'fontsize': 9},
        pctdistance=0.75
    )

    # Custom legend for pie
    ax1.legend(wedges, [l.replace('\n', ' ') for l in layers],
              title="Layer", loc="center left", bbox_to_anchor=(0.9, 0, 0.5, 1),
              fontsize=8)
    ax1.set_title('Latency Distribution', fontsize=12, fontweight='bold', pad=10)

    # Bar chart
    y_pos = np.arange(len(layers))
    bars = ax2.barh(y_pos, latencies, color=colors, edgecolor=[edge_colors[i] for i in range(len(layers))],
                    linewidth=1.2, height=0.6)

    for bar in bars:
        width = bar.get_width()
        ax2.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}ms', va='center', fontsize=10)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([l.replace('\n', ' ') for l in layers])
    ax2.set_xlabel('Latency (ms)', fontweight='bold')
    ax2.set_title('Per-Layer Latency', fontsize=12, fontweight='bold', pad=10)
    ax2.set_xlim(0, 30)
    ax2.xaxis.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax2.set_axisbelow(True)

    # Total annotation
    fig.text(0.5, 0.02, 'Total Pipeline Latency: 51.0ms (P99: 171ms)',
             ha='center', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12, wspace=0.4)
    plt.savefig('figure5_latency_breakdown.png', dpi=300, facecolor='white', edgecolor='none')
    plt.savefig('figure5_latency_breakdown.pdf', facecolor='white', edgecolor='none')
    plt.close()
    print("✓ Generated figure5_latency_breakdown.png/pdf")


if __name__ == '__main__':
    print("\n" + "="*55)
    print("EmbedGuard Paper Figures - Professional Academic Style")
    print("="*55 + "\n")

    figure1_architecture()
    figure2_tee_protocol()
    figure3_comparative_detection()
    figure4_ablation_study()
    figure5_latency_breakdown()

    print("\n" + "="*55)
    print("All figures generated successfully!")
    print("Style: IEEE/ACM Professional Academic")
    print("Output: figure1-5_*.png and figure1-5_*.pdf")
    print("="*55 + "\n")
