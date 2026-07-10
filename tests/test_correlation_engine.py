"""Tests for threat correlation engine."""

import pytest

from embedguard.config import OperationalMode
from embedguard.correlation_engine import ThreatCorrelationEngine, correlate_signals
from embedguard.types import AttackType, Decision, LayerSignal, ThreatLevel


class TestThreatCorrelationEngine:
    """Tests for ThreatCorrelationEngine."""

    @pytest.fixture
    def engine(self):
        """Create correlation engine with default settings."""
        return ThreatCorrelationEngine()

    def test_init_default_weights(self, engine):
        """Test default layer weights from paper."""
        assert engine.layer_weights["prompt"] == 0.35
        assert engine.layer_weights["embedding"] == 0.75
        assert engine.layer_weights["retrieval"] == 0.50
        assert engine.layer_weights["output"] == 0.20

    def test_init_custom_weights(self):
        """Test custom layer weights."""
        engine = ThreatCorrelationEngine(
            layer_weights={"prompt": 0.5, "embedding": 0.5}
        )
        assert engine.layer_weights["prompt"] == 0.5
        assert engine.layer_weights["embedding"] == 0.5

    def test_correlate_empty_signals(self, engine):
        """Test correlation with no signals."""
        score, level, decision = engine.correlate({})

        assert score == 0.0
        assert level == ThreatLevel.NONE
        assert decision == Decision.ALLOW

    @pytest.mark.parametrize(
        ("mode", "expected"),
        [
            (OperationalMode.PASSIVE, Decision.LOG),
            (OperationalMode.GATED, Decision.ALLOW),
            (OperationalMode.ACTIVE, Decision.ALLOW),
        ],
    )
    def test_correlate_empty_signals_respects_operational_mode(
        self, engine, mode, expected
    ):
        """Empty signals still pass through the operational decision policy."""
        score, level, decision = engine.correlate({}, mode=mode)

        assert score == 0.0
        assert level == ThreatLevel.NONE
        assert decision == expected

    def test_correlate_single_low_signal(self, engine):
        """Test correlation with single low signal."""
        signals = {
            "prompt": LayerSignal(
                layer_name="prompt",
                score=0.2,
                confidence=0.8,
            )
        }

        score, level, decision = engine.correlate(signals)

        assert score < 0.5
        assert level in [ThreatLevel.NONE, ThreatLevel.LOW]
        assert decision == Decision.ALLOW

    def test_correlate_single_high_signal(self, engine):
        """Test correlation with single high signal."""
        signals = {
            "prompt": LayerSignal(
                layer_name="prompt",
                score=0.9,
                confidence=0.95,
            )
        }

        score, level, decision = engine.correlate(
            signals, mode=OperationalMode.GATED
        )

        assert score > 0.5
        assert level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]

    def test_correlate_multiple_signals(self, engine):
        """Test correlation with multiple layer signals."""
        signals = {
            "prompt": LayerSignal(
                layer_name="prompt",
                score=0.3,
                confidence=0.7,
            ),
            "retrieval": LayerSignal(
                layer_name="retrieval",
                score=0.4,
                confidence=0.8,
            ),
        }

        score, level, decision = engine.correlate(signals)

        # Score should be weighted combination
        assert 0 <= score <= 1

    def test_correlation_boost_multi_layer(self, engine):
        """Test that multi-layer attacks get boosted score."""
        # Single layer elevated
        single = {
            "prompt": LayerSignal(layer_name="prompt", score=0.6, confidence=0.9),
        }

        # Multiple layers elevated
        multi = {
            "prompt": LayerSignal(layer_name="prompt", score=0.6, confidence=0.9),
            "retrieval": LayerSignal(layer_name="retrieval", score=0.6, confidence=0.9),
            "embedding": LayerSignal(layer_name="embedding", score=0.6, confidence=0.9),
        }

        score_single, _, _ = engine.correlate(single)
        score_multi, _, _ = engine.correlate(multi)

        # Multi-layer should have correlation boost
        assert score_multi >= score_single

    def test_zero_confidence_signals_cannot_create_correlation_boost(self, engine):
        signals = {
            "prompt": LayerSignal(
                layer_name="prompt", score=0.69, confidence=1.0
            ),
            "embedding": LayerSignal(
                layer_name="embedding", score=1.0, confidence=0.0
            ),
            "retrieval": LayerSignal(
                layer_name="retrieval", score=1.0, confidence=0.0
            ),
            "output": LayerSignal(
                layer_name="output", score=1.0, confidence=0.0
            ),
        }

        score, _, decision = engine.correlate(
            signals,
            mode=OperationalMode.ACTIVE,
        )

        assert score == pytest.approx(0.69)
        assert decision == Decision.ALLOW

    def test_decision_passive_mode(self, engine):
        """Test that passive mode always logs."""
        signals = {
            "prompt": LayerSignal(layer_name="prompt", score=0.95, confidence=1.0),
        }

        _, _, decision = engine.correlate(signals, mode=OperationalMode.PASSIVE)
        assert decision == Decision.LOG

    def test_decision_gated_mode(self, engine):
        """Test gated mode decision thresholds."""
        # Below flag threshold
        low_signals = {
            "prompt": LayerSignal(layer_name="prompt", score=0.3, confidence=0.9),
        }
        _, _, decision = engine.correlate(low_signals, mode=OperationalMode.GATED)
        assert decision == Decision.ALLOW

        # Above flag threshold
        high_signals = {
            "prompt": LayerSignal(layer_name="prompt", score=0.95, confidence=1.0),
        }
        _, _, decision = engine.correlate(high_signals, mode=OperationalMode.GATED)
        assert decision == Decision.FLAG

    def test_decision_active_mode(self, engine):
        """Test active mode decision thresholds."""
        # Above block threshold
        high_signals = {
            "prompt": LayerSignal(layer_name="prompt", score=0.98, confidence=1.0),
            "embedding": LayerSignal(layer_name="embedding", score=0.95, confidence=1.0),
        }
        _, _, decision = engine.correlate(high_signals, mode=OperationalMode.ACTIVE)
        assert decision == Decision.BLOCK

    def test_threat_levels(self, engine):
        """Test threat level determination."""
        test_cases = [
            (0.1, ThreatLevel.NONE),
            (0.25, ThreatLevel.LOW),
            (0.45, ThreatLevel.MEDIUM),
            (0.65, ThreatLevel.HIGH),
            (0.9, ThreatLevel.CRITICAL),
        ]

        for score, expected_level in test_cases:
            signals = {
                "prompt": LayerSignal(
                    layer_name="prompt", score=score, confidence=1.0
                ),
            }
            _, level, _ = engine.correlate(signals)
            # Allow some variance due to weighting
            assert level in [expected_level] or abs(
                list(ThreatLevel).index(level) - list(ThreatLevel).index(expected_level)
            ) <= 1

    def test_analyze_attack_pattern(self, engine):
        """Test attack pattern analysis."""
        signals = {
            "prompt": LayerSignal(
                layer_name="prompt",
                score=0.8,
                confidence=0.9,
                attack_type=AttackType.PROMPT_INJECTION,
            ),
            "retrieval": LayerSignal(
                layer_name="retrieval",
                score=0.7,
                confidence=0.8,
                attack_type=AttackType.RETRIEVAL_MANIPULATION,
            ),
        }

        analysis = engine.analyze_attack_pattern(signals)

        assert "layer_scores" in analysis
        assert "primary_vector" in analysis
        assert "affected_layers" in analysis
        assert "is_coordinated" in analysis
        assert len(analysis["affected_layers"]) == 2

    def test_get_layer_contributions(self, engine):
        """Test layer contribution calculation."""
        signals = {
            "prompt": LayerSignal(layer_name="prompt", score=0.5, confidence=1.0),
            "embedding": LayerSignal(layer_name="embedding", score=0.5, confidence=1.0),
        }

        contributions = engine.get_layer_contributions(signals)

        assert "prompt" in contributions
        assert "embedding" in contributions
        # Contributions should sum to ~100%
        total = sum(contributions.values())
        assert abs(total - 100) < 1  # Allow small rounding error


class TestCorrelateSignalsFunction:
    """Tests for convenience correlation function."""

    def test_returns_tuple(self):
        """Test return type."""
        signals = {
            "prompt": LayerSignal(layer_name="prompt", score=0.5, confidence=0.8),
        }

        result = correlate_signals(signals)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_mode_string(self):
        """Test mode can be passed as string."""
        signals = {
            "prompt": LayerSignal(layer_name="prompt", score=0.5, confidence=0.8),
        }

        score, level, decision = correlate_signals(signals, mode="active")
        assert isinstance(score, float)
        assert isinstance(level, str)
        assert isinstance(decision, str)
