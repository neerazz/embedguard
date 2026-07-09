"""
EmbedGuard: Cross-Layer Detection and Provenance Attestation for Adversarial Embedding Attacks in RAG Systems.

This module provides the main EmbedGuard framework for protecting RAG systems against
embedding space poisoning attacks through cross-layer detection and cryptographic attestation.

Example:
    >>> from embedguard import EmbedGuard, EmbedGuardConfig
    >>> config = EmbedGuardConfig(mode="active")
    >>> guard = EmbedGuard(config)
    >>> result = guard.analyze(query, documents)
    >>> print(result.threat_score)
"""

from embedguard.config import EmbedGuardConfig
from embedguard.core import EmbedGuard
from embedguard.types import (
    AnalysisResult,
    Decision,
    LayerSignal,
    ThreatLevel,
)

__version__ = "1.1.0"
__author__ = "Neeraj Kumar Singh Beshane"
__email__ = "b.neerajkumarsingh@gmail.com"

__all__ = [
    "EmbedGuard",
    "EmbedGuardConfig",
    "AnalysisResult",
    "Decision",
    "LayerSignal",
    "ThreatLevel",
    "__version__",
]
