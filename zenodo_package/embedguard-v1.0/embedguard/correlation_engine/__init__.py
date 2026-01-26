"""
Threat Correlation Engine.

This module implements weighted signal fusion from all detection layers
to compute unified threat scores and make final decisions.

The correlation engine uses configurable weights (from paper):
    - Prompt injection (Layer 1): 0.35
    - Embedding attestation (Layer 2): 0.75
    - Retrieval analysis (Layer 3): 0.50
    - Output verification (Layer 4): 0.20
"""

from typing import Any, Dict, Optional, Tuple

import numpy as np
from loguru import logger

from embedguard.config import OperationalMode
from embedguard.types import Decision, LayerSignal, ThreatLevel


class ThreatCorrelationEngine:
    """Correlates signals from multiple detection layers.

    This engine fuses signals from all EmbedGuard layers using weighted
    combination and cross-layer correlation to produce unified threat
    assessments and operational decisions.

    Attributes:
        layer_weights: Weight for each layer signal
        flag_threshold: Threat score threshold for flagging
        block_threshold: Threat score threshold for blocking
        correlation_boost: Additional weight for correlated attacks

    Example:
        >>> engine = ThreatCorrelationEngine()
        >>> threat_score, threat_level, decision = engine.correlate(signals)
        >>> if decision == Decision.BLOCK:
        ...     print(f"Blocking request with threat score {threat_score}")
    """

    # Default layer weights from paper
    DEFAULT_WEIGHTS = {
        "prompt": 0.35,      # Prompt injection detection
        "embedding": 0.75,   # TEE attestation (highest weight)
        "retrieval": 0.50,   # Distributional analysis
        "output": 0.20,      # Output verification
    }

    # Threat level thresholds
    THREAT_LEVELS = {
        "none": (0.0, 0.2),
        "low": (0.2, 0.4),
        "medium": (0.4, 0.6),
        "high": (0.6, 0.8),
        "critical": (0.8, 1.0),
    }

    def __init__(
        self,
        layer_weights: Optional[Dict[str, float]] = None,
        flag_threshold: float = 0.70,
        block_threshold: float = 0.85,
        correlation_boost: float = 0.15,
    ):
        """Initialize the correlation engine.

        Args:
            layer_weights: Custom layer weights (uses paper defaults if None)
            flag_threshold: Threshold for FLAG decision
            block_threshold: Threshold for BLOCK decision
            correlation_boost: Additional weight when multiple layers trigger
        """
        self.layer_weights = layer_weights or self.DEFAULT_WEIGHTS.copy()
        self.flag_threshold = flag_threshold
        self.block_threshold = block_threshold
        self.correlation_boost = correlation_boost

        logger.debug(
            f"ThreatCorrelationEngine initialized "
            f"(flag={flag_threshold}, block={block_threshold})"
        )

    def correlate(
        self,
        layer_signals: Dict[str, LayerSignal],
        mode: OperationalMode = OperationalMode.GATED,
    ) -> Tuple[float, ThreatLevel, Decision]:
        """Correlate layer signals and make a decision.

        Args:
            layer_signals: Dictionary of layer name to LayerSignal
            mode: Operational mode (passive, gated, active)

        Returns:
            Tuple of (threat_score, threat_level, decision)
        """
        if not layer_signals:
            return 0.0, ThreatLevel.NONE, Decision.ALLOW

        # Compute base threat score
        threat_score = self._compute_threat_score(layer_signals)

        # Apply correlation boost for multi-layer attacks
        correlation_factor = self._compute_correlation_factor(layer_signals)
        threat_score = min(threat_score + correlation_factor, 1.0)

        # Determine threat level
        threat_level = self._determine_threat_level(threat_score)

        # Make decision based on mode and score
        decision = self._make_decision(threat_score, mode)

        logger.debug(
            f"Correlation result: score={threat_score:.3f}, "
            f"level={threat_level.value}, decision={decision.value}"
        )

        return threat_score, threat_level, decision

    def _compute_threat_score(
        self, layer_signals: Dict[str, LayerSignal]
    ) -> float:
        """Compute threat score using Bayesian update across layers.

        Instead of simple weighted average, each layer updates a prior
        probability of attack. This captures the intuition that evidence
        from multiple independent layers compounds.
        
        Bayesian Update:
            P(attack | evidence) = P(evidence | attack) * P(attack) / P(evidence)
            
        We use log-odds for numerical stability:
            log_odds_posterior = log_odds_prior + log_likelihood_ratio
        """
        # Base prior: assume 10% of queries are attacks (from production data)
        prior_attack = 0.10
        log_odds = np.log(prior_attack / (1 - prior_attack))
        
        # Layer processing order: prompt -> embedding -> retrieval -> output
        layer_order = ["prompt", "embedding", "retrieval", "output"]
        
        for layer_name in layer_order:
            if layer_name not in layer_signals:
                continue
                
            signal = layer_signals[layer_name]
            weight = self.layer_weights.get(layer_name, 0.25)
            
            # Compute likelihood ratio for this layer
            # P(score | attack) / P(score | benign)
            # We model this as: high score = high likelihood of attack
            # Using logistic transformation to map score to likelihood ratio
            score = signal.score
            confidence = signal.confidence
            
            # Likelihood ratio: how much this evidence shifts our belief
            # Score of 0.5 = neutral (LR=1), higher = more attack-like
            # Scaled by layer weight and confidence
            if score > 0:
                # Log-likelihood ratio, bounded for stability
                log_lr = weight * confidence * np.log(
                    max(score, 0.01) / max(1 - score, 0.01)
                )
                log_lr = np.clip(log_lr, -5, 5)  # Prevent extreme updates
                log_odds += log_lr
        
        # Convert log-odds back to probability
        posterior = 1 / (1 + np.exp(-log_odds))
        
        return float(np.clip(posterior, 0.0, 1.0))

    def _compute_correlation_factor(
        self, layer_signals: Dict[str, LayerSignal]
    ) -> float:
        """Compute additional boost for correlated multi-layer attacks.

        The paper notes that coordinated attacks across multiple layers
        are stronger indicators than single-layer anomalies.
        """
        # Count layers with elevated scores
        elevated_count = sum(
            1 for signal in layer_signals.values()
            if signal.score > 0.5
        )

        # No boost for single layer
        if elevated_count <= 1:
            return 0.0

        # Progressive boost for multi-layer attacks
        # 2 layers: 0.5 × boost, 3 layers: 1.0 × boost, 4 layers: 1.5 × boost
        return self.correlation_boost * (elevated_count - 1) * 0.5

    def _determine_threat_level(self, threat_score: float) -> ThreatLevel:
        """Map threat score to threat level."""
        for level_name, (low, high) in self.THREAT_LEVELS.items():
            if low <= threat_score < high:
                return ThreatLevel(level_name)

        # Handle edge case of score = 1.0
        if threat_score >= 0.8:
            return ThreatLevel.CRITICAL

        return ThreatLevel.NONE

    def _make_decision(
        self,
        threat_score: float,
        mode: OperationalMode,
    ) -> Decision:
        """Make operational decision based on score and mode.

        Decision matrix:
        - PASSIVE mode: Always LOG (monitoring only)
        - GATED mode: FLAG if score >= flag_threshold, else ALLOW
        - ACTIVE mode: BLOCK if score >= block_threshold,
                       FLAG if score >= flag_threshold, else ALLOW
        """
        if mode == OperationalMode.PASSIVE:
            # Passive mode: log everything, never intervene
            return Decision.LOG

        if mode == OperationalMode.GATED:
            # Gated mode: flag for human review above threshold
            if threat_score >= self.flag_threshold:
                return Decision.FLAG
            return Decision.ALLOW

        if mode == OperationalMode.ACTIVE:
            # Active mode: automatic blocking
            if threat_score >= self.block_threshold:
                return Decision.BLOCK
            if threat_score >= self.flag_threshold:
                return Decision.FLAG
            return Decision.ALLOW

        # Default to safe behavior
        return Decision.ALLOW

    def analyze_attack_pattern(
        self, layer_signals: Dict[str, LayerSignal]
    ) -> Dict[str, Any]:
        """Analyze the pattern of signals for attack characterization.

        Returns detailed analysis useful for security teams.
        """
        analysis = {
            "layer_scores": {},
            "primary_vector": None,
            "is_coordinated": False,
            "affected_layers": [],
            "recommended_action": None,
        }

        if not layer_signals:
            return analysis

        # Record per-layer scores
        for name, signal in layer_signals.items():
            analysis["layer_scores"][name] = {
                "score": signal.score,
                "confidence": signal.confidence,
                "weighted_score": signal.weighted_score,
            }
            if signal.score > 0.5:
                analysis["affected_layers"].append(name)

        # Identify primary attack vector (highest weighted score)
        if analysis["layer_scores"]:
            primary = max(
                analysis["layer_scores"].items(),
                key=lambda x: x[1]["weighted_score"]
            )
            analysis["primary_vector"] = primary[0]

        # Check for coordinated attack
        if len(analysis["affected_layers"]) >= 3:
            analysis["is_coordinated"] = True

        # Generate recommendation
        threat_score = self._compute_threat_score(layer_signals)
        if threat_score >= self.block_threshold:
            analysis["recommended_action"] = "block_and_investigate"
        elif threat_score >= self.flag_threshold:
            analysis["recommended_action"] = "flag_for_review"
        elif threat_score >= 0.3:
            analysis["recommended_action"] = "monitor_closely"
        else:
            analysis["recommended_action"] = "allow"

        return analysis

    def get_layer_contributions(
        self, layer_signals: Dict[str, LayerSignal]
    ) -> Dict[str, float]:
        """Get each layer's contribution to the final score.

        Useful for explainability and debugging.
        """
        contributions = {}
        total_score = 0.0
        total_weight = 0.0

        for layer_name, signal in layer_signals.items():
            weight = self.layer_weights.get(layer_name, 0.25)
            effective_weight = weight * signal.confidence
            contribution = signal.score * effective_weight
            contributions[layer_name] = contribution
            total_score += contribution
            total_weight += effective_weight

        # Normalize to percentages
        if total_score > 0:
            contributions = {
                k: (v / total_score) * 100
                for k, v in contributions.items()
            }

        return contributions


# Convenience function for quick correlation
def correlate_signals(
    layer_signals: Dict[str, LayerSignal],
    mode: str = "gated",
) -> Tuple[float, str, str]:
    """Quick correlation of layer signals.

    Args:
        layer_signals: Dictionary of signals
        mode: Operational mode string

    Returns:
        Tuple of (threat_score, threat_level, decision) as strings
    """
    engine = ThreatCorrelationEngine()
    op_mode = OperationalMode(mode)
    score, level, decision = engine.correlate(layer_signals, op_mode)
    return score, level.value, decision.value
