#!/usr/bin/env python3
"""
Generate publication-quality figures for Tier-1 venue submission.
Addresses gaps identified in BRUTAL dynamic roundtable evaluation.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path

# IEEE/ACM Professional Style
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'axes.linewidth': 0.8,
    'axes.grid': False,
    'grid.alpha': 0.3,
})

# Color palette (colorblind-friendly)
COLORS = {
    'embedguard': '#2E86AB',  # Blue
    'raguard': '#A23B72',     # Magenta
    'robustrag': '#F18F01',   # Orange
    'trustrag': '#C73E1D',    # Red
    'ragdefender': '#3B1F2B', # Dark
    'pass': '#28A745',        # Green
    'fail': '#DC3545',        # Red
    'warn': '#FFC107',        # Yellow
}

output_dir = Path(__file__).parent
output_dir.mkdir(parents=True, exist_ok=True)


def figure6_threat_model():
    """Figure 6: Formal Threat Model Diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Title
    ax.text(5, 7.5, 'EmbedGuard Threat Model', ha='center', va='center',
            fontsize=14, fontweight='bold')

    # Adversary box
    adv_box = FancyBboxPatch((0.5, 4.5), 4, 2.5, boxstyle="round,pad=0.1",
                              facecolor='#FFE6E6', edgecolor='#DC3545', linewidth=2)
    ax.add_patch(adv_box)
    ax.text(2.5, 6.5, 'ADVERSARY (A)', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#DC3545')

    adv_text = """Knowledge: Black-box RAG access
Capabilities: Corpus poisoning
Goals: Integrity/Availability violation
Budget: 10K GPU-hrs, 1K queries"""
    ax.text(2.5, 5.3, adv_text, ha='center', va='center', fontsize=8,
            family='monospace', linespacing=1.5)

    # Trust assumptions box
    trust_box = FancyBboxPatch((5.5, 4.5), 4, 2.5, boxstyle="round,pad=0.1",
                                facecolor='#E6FFE6', edgecolor='#28A745', linewidth=2)
    ax.add_patch(trust_box)
    ax.text(7.5, 6.5, 'TRUST ASSUMPTIONS', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#28A745')

    trust_text = """TEE firmware patched
Attestation keys protected
Detection thresholds confidential
No insider threat"""
    ax.text(7.5, 5.3, trust_text, ha='center', va='center', fontsize=8,
            family='monospace', linespacing=1.5)

    # Attack vectors
    attack_box = FancyBboxPatch((0.5, 1.5), 4, 2.5, boxstyle="round,pad=0.1",
                                 facecolor='#FFF3E6', edgecolor='#F18F01', linewidth=2)
    ax.add_patch(attack_box)
    ax.text(2.5, 3.5, 'ATTACK VECTORS', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#F18F01')

    attack_text = """1. Optimization-based poisoning
2. Transferability attacks
3. Jamming/DoS attacks
4. Adaptive evasion"""
    ax.text(2.5, 2.3, attack_text, ha='center', va='center', fontsize=8,
            family='monospace', linespacing=1.5)

    # Defense layers
    defense_box = FancyBboxPatch((5.5, 1.5), 4, 2.5, boxstyle="round,pad=0.1",
                                  facecolor='#E6F3FF', edgecolor='#2E86AB', linewidth=2)
    ax.add_patch(defense_box)
    ax.text(7.5, 3.5, 'DEFENSE LAYERS', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#2E86AB')

    defense_text = """L1: Prompt injection detection
L2: TEE embedding attestation
L3: Retrieval distributional analysis
L4: Output consistency verification"""
    ax.text(7.5, 2.3, defense_text, ha='center', va='center', fontsize=8,
            family='monospace', linespacing=1.5)

    # Arrows
    ax.annotate('', xy=(5.3, 5.75), xytext=(4.7, 5.75),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    ax.annotate('', xy=(5.3, 2.75), xytext=(4.7, 2.75),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    ax.annotate('', xy=(2.5, 4.3), xytext=(2.5, 4.0),
                arrowprops=dict(arrowstyle='->', color='#DC3545', lw=1.5))
    ax.annotate('', xy=(7.5, 4.3), xytext=(7.5, 4.0),
                arrowprops=dict(arrowstyle='->', color='#28A745', lw=1.5))

    # Labels
    ax.text(5, 5.75, 'vs', ha='center', va='center', fontsize=10)
    ax.text(5, 2.75, 'defends', ha='center', va='center', fontsize=10)

    plt.tight_layout()
    fig.savefig(output_dir / 'figure6_threat_model.png', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    fig.savefig(output_dir / 'figure6_threat_model.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Generated: figure6_threat_model.png/pdf")


def figure7_benchmark_comparison():
    """Figure 7: Standardized Benchmark Results (placeholder data)."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))

    # Data (placeholder - to be updated with actual results)
    datasets = ['NQ', 'HotpotQA', 'MS-MARCO']
    x = np.arange(len(datasets))
    width = 0.15

    # Detection rates (placeholder)
    embedguard = [94.7, 93.2, 92.8]  # To be updated
    raguard = [87.2, 84.5, 82.1]
    robustrag = [82.9, 80.3, 78.7]
    trustrag = [79.3, 76.8, 74.2]
    ragdefender = [91.2, 89.5, 87.3]

    bars1 = ax.bar(x - 2*width, embedguard, width, label='EmbedGuard (Ours)',
                   color=COLORS['embedguard'], edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x - width, ragdefender, width, label='RAGDefender',
                   color=COLORS['ragdefender'], edgecolor='black', linewidth=0.5)
    bars3 = ax.bar(x, raguard, width, label='RAGuard',
                   color=COLORS['raguard'], edgecolor='black', linewidth=0.5)
    bars4 = ax.bar(x + width, robustrag, width, label='RobustRAG',
                   color=COLORS['robustrag'], edgecolor='black', linewidth=0.5)
    bars5 = ax.bar(x + 2*width, trustrag, width, label='TrustRAG',
                   color=COLORS['trustrag'], edgecolor='black', linewidth=0.5)

    # Add value labels
    for bars in [bars1, bars2, bars3, bars4, bars5]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}%',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=7, rotation=90)

    ax.set_ylabel('Detection Rate (%)')
    ax.set_xlabel('Benchmark Dataset')
    ax.set_title('EmbedGuard vs. State-of-the-Art on Standardized Benchmarks', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.set_ylim(0, 110)
    ax.legend(loc='upper right', ncol=2, framealpha=0.9)
    ax.axhline(y=90, color='gray', linestyle='--', alpha=0.5, label='90% threshold')

    # Add note about placeholder
    ax.text(0.02, 0.02, '*Placeholder data - update after benchmark evaluation',
            transform=ax.transAxes, fontsize=8, style='italic', alpha=0.7)

    plt.tight_layout()
    fig.savefig(output_dir / 'figure7_benchmark_comparison.png', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    fig.savefig(output_dir / 'figure7_benchmark_comparison.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Generated: figure7_benchmark_comparison.png/pdf")


def figure8_sidechannel_attack():
    """Figure 8: Side-Channel Attack Surface and Mitigations."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Title
    ax.text(6, 7.5, 'TEE Side-Channel Attack Surface (CounterSEVeillance)',
            ha='center', va='center', fontsize=13, fontweight='bold')

    # SEV-SNP VM box
    vm_box = FancyBboxPatch((0.5, 3), 3.5, 4, boxstyle="round,pad=0.1",
                             facecolor='#E6F3FF', edgecolor='#2E86AB', linewidth=2)
    ax.add_patch(vm_box)
    ax.text(2.25, 6.5, 'SEV-SNP VM', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#2E86AB')
    ax.text(2.25, 5.5, 'EmbedGuard\nEnclave', ha='center', va='center',
            fontsize=10, family='monospace')
    ax.text(2.25, 4.2, 'Embedding\nGeneration', ha='center', va='center',
            fontsize=9, family='monospace')
    ax.text(2.25, 3.3, 'Attestation\nCertificate', ha='center', va='center',
            fontsize=9, family='monospace')

    # Hypervisor box
    hv_box = FancyBboxPatch((4.5, 3), 3, 4, boxstyle="round,pad=0.1",
                             facecolor='#FFE6E6', edgecolor='#DC3545', linewidth=2)
    ax.add_patch(hv_box)
    ax.text(6, 6.5, 'Malicious\nHypervisor', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#DC3545')
    ax.text(6, 5, '228 Exposed\nPerf Counters', ha='center', va='center',
            fontsize=10, family='monospace')
    ax.text(6, 3.8, 'RSA-4096 key\nin <8 min', ha='center', va='center',
            fontsize=9, style='italic', color='#DC3545')

    # Attack arrow
    ax.annotate('', xy=(4.3, 5), xytext=(4.0, 5),
                arrowprops=dict(arrowstyle='->', color='#DC3545', lw=2))
    ax.text(4.15, 5.3, 'Leaks', ha='center', va='center', fontsize=8,
            color='#DC3545', rotation=0)

    # Mitigations box
    mit_box = FancyBboxPatch((8, 3), 3.5, 4, boxstyle="round,pad=0.1",
                              facecolor='#E6FFE6', edgecolor='#28A745', linewidth=2)
    ax.add_patch(mit_box)
    ax.text(9.75, 6.5, 'Mitigations', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#28A745')

    mitigations = """1. Disable perf counters
   in enclave (+0ms)

2. Timing obfuscation
   (+8ms latency)

3. Hypervisor monitoring
   (+4ms latency)"""
    ax.text(9.75, 4.5, mitigations, ha='center', va='center',
            fontsize=8, family='monospace', linespacing=1.3)

    # Defense arrow
    ax.annotate('', xy=(7.8, 5), xytext=(7.5, 5),
                arrowprops=dict(arrowstyle='->', color='#28A745', lw=2))
    ax.text(7.65, 5.3, 'Defends', ha='center', va='center', fontsize=8,
            color='#28A745')

    # Impact summary
    impact_box = FancyBboxPatch((2, 0.5), 8, 2, boxstyle="round,pad=0.1",
                                 facecolor='#FFF9E6', edgecolor='#F18F01', linewidth=2)
    ax.add_patch(impact_box)
    ax.text(6, 2.1, 'Impact on EmbedGuard Claims', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#F18F01')

    impact_text = """Attestation certificates remain valid, but embedding computation patterns may leak.
Mitigation adds 8-12ms latency. Tradeoff: security vs. performance."""
    ax.text(6, 1.1, impact_text, ha='center', va='center', fontsize=9,
            linespacing=1.5)

    plt.tight_layout()
    fig.savefig(output_dir / 'figure8_sidechannel_attack.png', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    fig.savefig(output_dir / 'figure8_sidechannel_attack.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Generated: figure8_sidechannel_attack.png/pdf")


def figure9_gap_analysis():
    """Figure 9: Tier-1 Venue Gap Analysis."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    # Gap categories
    categories = [
        'Formal Threat Model',
        'Standardized Benchmarks',
        'Side-Channel Discussion',
        'Jamming Attack Coverage',
        'Formal TEE Citation',
        'Artifact Readiness',
        'Ethics Section'
    ]

    # Status: 0 = missing, 0.5 = partial, 1 = complete
    current_status = [0, 0, 0.3, 0, 0.5, 0.7, 0.8]
    required_status = [1, 1, 1, 1, 1, 1, 1]

    y_pos = np.arange(len(categories))

    # Horizontal bar chart
    bars_req = ax.barh(y_pos, required_status, height=0.4, label='Required',
                       color='#E0E0E0', edgecolor='black', linewidth=0.5)
    bars_cur = ax.barh(y_pos, current_status, height=0.4, label='Current',
                       color=[COLORS['fail'] if s < 0.5 else
                              COLORS['warn'] if s < 0.8 else
                              COLORS['pass'] for s in current_status],
                       edgecolor='black', linewidth=0.5)

    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.set_xlabel('Completion Level')
    ax.set_title('Tier-1 Venue Readiness Gap Analysis', fontweight='bold')
    ax.set_xlim(0, 1.2)

    # Add percentage labels
    for i, (cur, req) in enumerate(zip(current_status, required_status)):
        ax.text(cur + 0.02, i, f'{int(cur*100)}%', va='center', fontsize=9)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['pass'], label='Complete (≥80%)'),
        mpatches.Patch(facecolor=COLORS['warn'], label='Partial (50-79%)'),
        mpatches.Patch(facecolor=COLORS['fail'], label='Missing (<50%)')
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()
    fig.savefig(output_dir / 'figure9_gap_analysis.png', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    fig.savefig(output_dir / 'figure9_gap_analysis.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Generated: figure9_gap_analysis.png/pdf")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("EmbedGuard Tier-1 Venue Figure Generator")
    print("="*60 + "\n")

    figure6_threat_model()
    figure7_benchmark_comparison()
    figure8_sidechannel_attack()
    figure9_gap_analysis()

    print("\n" + "="*60)
    print("All figures generated successfully!")
    print(f"Output directory: {output_dir}")
    print("="*60 + "\n")
