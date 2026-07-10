"""EmbedGuard reference components for adversarial RAG experiments.

The released package coordinates pattern detection, an HMAC provenance simulator,
experimental retrieval analysis, output-consistency proxies, and deterministic fusion.
It does not provide hardware-backed attestation.

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

__version__ = "1.2.0"
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
