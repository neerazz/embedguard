"""Configuration management for EmbedGuard."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class OperationalMode(str, Enum):
    """EmbedGuard operational modes."""

    PASSIVE = "passive"  # Log only, no intervention
    GATED = "gated"      # Flag for human review
    ACTIVE = "active"    # Automatic blocking


class EmbedGuardConfig(BaseModel):
    """Configuration for EmbedGuard framework.

    Attributes:
        mode: Operational mode (passive, gated, active)
        enable_tee: Enable TEE-based attestation (requires hardware support)
        enable_prompt_detection: Enable prompt injection detection layer
        enable_retrieval_analysis: Enable retrieval distributional analysis
        enable_output_verification: Enable output consistency verification
        thresholds: Detection thresholds for each component
        layer_weights: Weights for combining layer signals
        model_name: Embedding model name for semantic similarity
        device: Device for model inference (cuda, cpu, mps)
        random_seed: Random seed for reproducibility
    """

    # Core settings
    mode: OperationalMode = Field(
        default=OperationalMode.GATED,
        description="Operational mode for EmbedGuard"
    )

    # Layer toggles
    enable_tee: bool = Field(
        default=False,
        description="Enable TEE attestation (requires AMD SEV-SNP or Intel SGX)"
    )
    enable_prompt_detection: bool = Field(
        default=True,
        description="Enable prompt injection detection layer"
    )
    enable_retrieval_analysis: bool = Field(
        default=True,
        description="Enable retrieval distributional analysis layer"
    )
    enable_output_verification: bool = Field(
        default=True,
        description="Enable output consistency verification layer"
    )

    # Thresholds
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "prompt_injection": 0.70,
            "kl_divergence": 0.15,
            "pca_anomaly": 0.85,
            "rank_correlation_min": 0.30,
            "output_stability_min": 0.65,
            "threat_score_flag": 0.70,
            "threat_score_block": 0.85,
        },
        description="Detection thresholds"
    )

    # Layer weights (from paper: prompt=0.35, embedding=0.75, retrieval=0.50, output=0.20)
    layer_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "prompt": 0.35,
            "embedding": 0.75,
            "retrieval": 0.50,
            "output": 0.20,
        },
        description="Weights for combining layer signals"
    )

    # Model settings
    model_name: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        description="Embedding model for semantic similarity"
    )
    prompt_classifier_model: str = Field(
        default="distilbert-base-uncased",
        description="Model for prompt injection classification"
    )

    # Hardware settings
    device: str = Field(
        default="cpu",
        description="Device for inference (cuda, cpu, mps)"
    )

    # Reproducibility
    random_seed: int = Field(
        default=42,
        description="Random seed for reproducibility"
    )

    # Performance settings
    batch_size: int = Field(
        default=32,
        description="Batch size for embedding operations"
    )
    max_documents: int = Field(
        default=100,
        description="Maximum documents to analyze per query"
    )

    # Output verification settings
    perturbation_count: int = Field(
        default=5,
        description="Number of perturbations for output verification (K=5 in paper)"
    )

    # Retrieval analysis settings
    pca_components: int = Field(
        default=50,
        description="Number of PCA components (k=50 in paper)"
    )
    pca_update_frequency: int = Field(
        default=1000,
        description="Update PCA every N queries"
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    enable_audit_log: bool = Field(
        default=True,
        description="Enable detailed audit logging"
    )
    audit_log_path: Optional[str] = Field(
        default=None,
        description="Path for audit logs"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        extra = "allow"

    def get_threshold(self, name: str) -> float:
        """Get threshold by name with default fallback."""
        return self.thresholds.get(name, 0.5)

    def get_layer_weight(self, layer: str) -> float:
        """Get layer weight by name with default fallback."""
        return self.layer_weights.get(layer, 0.25)


# Preset configurations
PRESET_CONFIGS = {
    "high_security": EmbedGuardConfig(
        mode=OperationalMode.ACTIVE,
        enable_tee=True,
        thresholds={
            "prompt_injection": 0.60,
            "kl_divergence": 0.10,
            "pca_anomaly": 0.80,
            "rank_correlation_min": 0.40,
            "output_stability_min": 0.70,
            "threat_score_flag": 0.60,
            "threat_score_block": 0.75,
        }
    ),
    "balanced": EmbedGuardConfig(
        mode=OperationalMode.GATED,
        enable_tee=False,
        thresholds={
            "prompt_injection": 0.70,
            "kl_divergence": 0.15,
            "pca_anomaly": 0.85,
            "rank_correlation_min": 0.30,
            "output_stability_min": 0.65,
            "threat_score_flag": 0.70,
            "threat_score_block": 0.85,
        }
    ),
    "low_latency": EmbedGuardConfig(
        mode=OperationalMode.PASSIVE,
        enable_tee=False,
        enable_output_verification=False,  # Skip slowest layer
        thresholds={
            "prompt_injection": 0.80,
            "kl_divergence": 0.20,
            "pca_anomaly": 0.90,
            "rank_correlation_min": 0.25,
            "output_stability_min": 0.60,
            "threat_score_flag": 0.80,
            "threat_score_block": 0.90,
        }
    ),
}


def get_preset_config(name: str) -> EmbedGuardConfig:
    """Get a preset configuration by name.

    Args:
        name: Preset name (high_security, balanced, low_latency)

    Returns:
        EmbedGuardConfig instance

    Raises:
        ValueError: If preset name is not found
    """
    if name not in PRESET_CONFIGS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESET_CONFIGS.keys())}")
    return PRESET_CONFIGS[name].model_copy()
