"""Type definitions for EmbedGuard framework."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Decision(str, Enum):
    """Decision made by EmbedGuard after analysis."""

    ALLOW = "allow"      # Safe to proceed
    FLAG = "flag"        # Flag for human review (gated mode)
    BLOCK = "block"      # Block the request (active mode)
    LOG = "log"          # Log only (passive mode)


class ThreatLevel(str, Enum):
    """Threat severity levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackType(str, Enum):
    """Types of detected attacks."""

    PROMPT_INJECTION = "prompt_injection"
    EMBEDDING_POISONING = "embedding_poisoning"
    RETRIEVAL_MANIPULATION = "retrieval_manipulation"
    OUTPUT_INSTABILITY = "output_instability"
    COORDINATED_ATTACK = "coordinated_attack"
    UNKNOWN = "unknown"


@dataclass
class LayerSignal:
    """Signal from a single detection layer."""

    layer_name: str
    score: float  # 0.0 to 1.0, higher = more suspicious
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    attack_type: Optional[AttackType] = None

    @property
    def weighted_score(self) -> float:
        """Return confidence-weighted score."""
        return self.score * self.confidence


@dataclass
class AttestationResult:
    """Result of TEE attestation verification."""

    is_valid: bool
    document_hash: Optional[str] = None
    model_hash: Optional[str] = None
    timestamp: Optional[str] = None
    signature: Optional[str] = None
    error: Optional[str] = None


@dataclass
class RetrievalAnalysis:
    """Results from retrieval distributional analysis."""

    pca_anomaly_score: float
    kl_divergence: float
    rank_correlation: float
    is_anomalous: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputStability:
    """Results from output consistency verification."""

    stability_score: float  # 0.0 to 1.0, higher = more stable
    perturbation_count: int
    variance: float
    is_stable: bool
    outputs_compared: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete analysis result from EmbedGuard."""

    # Core results
    threat_score: float  # 0.0 to 1.0
    threat_level: ThreatLevel
    decision: Decision

    # Layer signals
    layer_signals: Dict[str, LayerSignal] = field(default_factory=dict)

    # Attack information
    detected_attacks: List[AttackType] = field(default_factory=list)
    attack_confidence: float = 0.0

    # Timing
    total_latency_ms: float = 0.0

    # Detailed results (optional)
    attestation: Optional[AttestationResult] = None
    retrieval_analysis: Optional[RetrievalAnalysis] = None
    output_stability: Optional[OutputStability] = None

    # Context
    query: str = ""
    num_documents: int = 0

    # Audit trail
    session_id: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "threat_score": self.threat_score,
            "threat_level": self.threat_level.value,
            "decision": self.decision.value,
            "layer_signals": {
                name: {
                    "score": sig.score,
                    "confidence": sig.confidence,
                    "latency_ms": sig.latency_ms,
                }
                for name, sig in self.layer_signals.items()
            },
            "detected_attacks": [a.value for a in self.detected_attacks],
            "attack_confidence": self.attack_confidence,
            "total_latency_ms": self.total_latency_ms,
            "query_preview": self.query[:100] if self.query else "",
            "num_documents": self.num_documents,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }


@dataclass
class Document:
    """A document with optional attestation."""

    content: str
    embedding: Optional[List[float]] = None
    document_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    attestation: Optional[AttestationResult] = None

    def __post_init__(self):
        """Generate document ID if not provided."""
        if self.document_id is None:
            import hashlib
            self.document_id = hashlib.sha256(self.content.encode()).hexdigest()[:16]
