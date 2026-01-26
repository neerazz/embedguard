"""Core EmbedGuard framework implementation."""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from embedguard.config import EmbedGuardConfig, OperationalMode
from embedguard.correlation_engine import ThreatCorrelationEngine
from embedguard.embedding_attestation import EmbeddingAttestationLayer
from embedguard.output_verifier import OutputConsistencyVerifier
from embedguard.prompt_detector import PromptInjectionDetector
from embedguard.retrieval_analyzer import RetrievalDistributionalAnalyzer
from embedguard.types import (
    AnalysisResult,
    AttackType,
    Decision,
    Document,
    LayerSignal,
    ThreatLevel,
)


class EmbedGuard:
    """Main EmbedGuard framework for RAG security.

    EmbedGuard implements cross-layer detection and cryptographic attestation
    for protecting RAG systems against embedding space poisoning attacks.

    Architecture:
        Layer 1: Prompt Injection Detection (DistilBERT classifier)
        Layer 2: Embedding Attestation (TEE-based, optional)
        Layer 3: Retrieval Distributional Analysis (PCA, KL divergence)
        Layer 4: Output Consistency Verification (perturbation testing)
        + Threat Correlation Engine (weighted signal fusion)

    Example:
        >>> from embedguard import EmbedGuard, EmbedGuardConfig
        >>> config = EmbedGuardConfig(mode="active")
        >>> guard = EmbedGuard(config)
        >>> result = guard.analyze("What is the capital of France?", documents)
        >>> if result.decision == Decision.BLOCK:
        ...     print(f"Blocked! Threat score: {result.threat_score}")
    """

    def __init__(self, config: Optional[EmbedGuardConfig] = None):
        """Initialize EmbedGuard with configuration.

        Args:
            config: Configuration object. If None, uses default balanced config.
        """
        self.config = config or EmbedGuardConfig()
        self._initialize_layers()
        self._query_count = 0
        logger.info(f"EmbedGuard initialized in {self.config.mode} mode")

    def _initialize_layers(self) -> None:
        """Initialize detection layers based on configuration."""
        # Layer 1: Prompt Injection Detection
        if self.config.enable_prompt_detection:
            self.prompt_detector = PromptInjectionDetector(
                model_name=self.config.prompt_classifier_model,
                device=self.config.device,
                threshold=self.config.get_threshold("prompt_injection"),
            )
            logger.debug("Prompt injection detector initialized")
        else:
            self.prompt_detector = None

        # Layer 2: Embedding Attestation
        if self.config.enable_tee:
            self.attestation_layer = EmbeddingAttestationLayer(
                model_name=self.config.model_name,
                device=self.config.device,
            )
            logger.debug("TEE attestation layer initialized")
        else:
            self.attestation_layer = None

        # Layer 3: Retrieval Distributional Analysis
        if self.config.enable_retrieval_analysis:
            self.retrieval_analyzer = RetrievalDistributionalAnalyzer(
                n_components=self.config.pca_components,
                kl_threshold=self.config.get_threshold("kl_divergence"),
                update_frequency=self.config.pca_update_frequency,
            )
            logger.debug("Retrieval analyzer initialized")
        else:
            self.retrieval_analyzer = None

        # Layer 4: Output Consistency Verification
        if self.config.enable_output_verification:
            self.output_verifier = OutputConsistencyVerifier(
                model_name=self.config.model_name,
                device=self.config.device,
                k_perturbations=self.config.perturbation_count,
                stability_threshold=self.config.get_threshold("output_stability_min"),
            )
            logger.debug("Output verifier initialized")
        else:
            self.output_verifier = None

        # Correlation Engine
        self.correlation_engine = ThreatCorrelationEngine(
            layer_weights=self.config.layer_weights,
            flag_threshold=self.config.get_threshold("threat_score_flag"),
            block_threshold=self.config.get_threshold("threat_score_block"),
        )
        logger.debug("Correlation engine initialized")

    def analyze(
        self,
        query: str,
        documents: Union[List[str], List[Document]],
        embeddings: Optional[List[List[float]]] = None,
        generated_output: Optional[str] = None,
    ) -> AnalysisResult:
        """Analyze a RAG query and documents for potential attacks.

        This is the main entry point for EmbedGuard protection. It runs all
        enabled detection layers and returns a comprehensive analysis result.

        Args:
            query: The user query being processed
            documents: Retrieved documents (strings or Document objects)
            embeddings: Optional pre-computed embeddings for documents
            generated_output: Optional generated output for consistency checking

        Returns:
            AnalysisResult containing threat score, decision, and layer signals
        """
        start_time = time.time()
        session_id = str(uuid.uuid4())[:8]
        self._query_count += 1

        logger.debug(f"[{session_id}] Analyzing query: {query[:50]}...")

        # Normalize documents to Document objects
        doc_objects = self._normalize_documents(documents, embeddings)

        # Collect layer signals
        layer_signals: Dict[str, LayerSignal] = {}
        detected_attacks: List[AttackType] = []

        # Layer 1: Prompt Injection Detection
        if self.prompt_detector is not None:
            signal = self._run_prompt_detection(query, session_id)
            layer_signals["prompt"] = signal
            if signal.score > self.config.get_threshold("prompt_injection"):
                detected_attacks.append(AttackType.PROMPT_INJECTION)

        # Layer 2: Embedding Attestation
        if self.attestation_layer is not None:
            signal = self._run_attestation(doc_objects, session_id)
            layer_signals["embedding"] = signal
            if signal.score > 0.5:  # Any attestation failure
                detected_attacks.append(AttackType.EMBEDDING_POISONING)

        # Layer 3: Retrieval Distributional Analysis
        if self.retrieval_analyzer is not None:
            signal = self._run_retrieval_analysis(query, doc_objects, session_id)
            layer_signals["retrieval"] = signal
            if signal.score > self.config.get_threshold("pca_anomaly"):
                detected_attacks.append(AttackType.RETRIEVAL_MANIPULATION)

        # Layer 4: Output Consistency (only if elevated threat or output provided)
        if self.output_verifier is not None:
            should_verify = (
                generated_output is not None
                or self._should_verify_output(layer_signals)
            )
            if should_verify:
                signal = self._run_output_verification(
                    query, doc_objects, generated_output, session_id
                )
                layer_signals["output"] = signal
                if signal.score > (1 - self.config.get_threshold("output_stability_min")):
                    detected_attacks.append(AttackType.OUTPUT_INSTABILITY)

        # Correlation Engine: Fuse signals and make decision
        threat_score, threat_level, decision = self.correlation_engine.correlate(
            layer_signals,
            mode=self.config.mode,
        )

        # Check for coordinated attack pattern
        if len(detected_attacks) >= 3:
            detected_attacks.append(AttackType.COORDINATED_ATTACK)

        # Build result
        total_latency = (time.time() - start_time) * 1000  # Convert to ms
        result = AnalysisResult(
            threat_score=threat_score,
            threat_level=threat_level,
            decision=decision,
            layer_signals=layer_signals,
            detected_attacks=detected_attacks,
            attack_confidence=max((s.confidence for s in layer_signals.values()), default=0.0),
            total_latency_ms=total_latency,
            query=query,
            num_documents=len(doc_objects),
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
        )

        logger.info(
            f"[{session_id}] Analysis complete: threat={threat_score:.2f}, "
            f"decision={decision.value}, latency={total_latency:.1f}ms"
        )

        return result

    def _normalize_documents(
        self,
        documents: Union[List[str], List[Document]],
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[Document]:
        """Normalize input documents to Document objects."""
        doc_objects = []
        for i, doc in enumerate(documents):
            if isinstance(doc, Document):
                doc_objects.append(doc)
            else:
                embedding = embeddings[i] if embeddings and i < len(embeddings) else None
                doc_objects.append(Document(content=doc, embedding=embedding))
        return doc_objects

    def _run_prompt_detection(self, query: str, session_id: str) -> LayerSignal:
        """Run prompt injection detection layer."""
        start = time.time()
        try:
            score, confidence, details = self.prompt_detector.detect(query)
            latency = (time.time() - start) * 1000
            return LayerSignal(
                layer_name="prompt",
                score=score,
                confidence=confidence,
                details=details,
                latency_ms=latency,
                attack_type=AttackType.PROMPT_INJECTION if score > 0.5 else None,
            )
        except Exception as e:
            logger.error(f"[{session_id}] Prompt detection error: {e}")
            return LayerSignal(
                layer_name="prompt",
                score=0.0,
                confidence=0.0,
                details={"error": str(e)},
                latency_ms=(time.time() - start) * 1000,
            )

    def _run_attestation(
        self, documents: List[Document], session_id: str
    ) -> LayerSignal:
        """Run embedding attestation layer."""
        start = time.time()
        try:
            score, confidence, details = self.attestation_layer.verify_batch(documents)
            latency = (time.time() - start) * 1000
            return LayerSignal(
                layer_name="embedding",
                score=score,
                confidence=confidence,
                details=details,
                latency_ms=latency,
                attack_type=AttackType.EMBEDDING_POISONING if score > 0.5 else None,
            )
        except Exception as e:
            logger.error(f"[{session_id}] Attestation error: {e}")
            return LayerSignal(
                layer_name="embedding",
                score=1.0,  # Fail safe: treat errors as suspicious
                confidence=0.5,
                details={"error": str(e)},
                latency_ms=(time.time() - start) * 1000,
            )

    def _run_retrieval_analysis(
        self, query: str, documents: List[Document], session_id: str
    ) -> LayerSignal:
        """Run retrieval distributional analysis layer."""
        start = time.time()
        try:
            score, confidence, details = self.retrieval_analyzer.analyze(
                query, documents, query_id=self._query_count
            )
            latency = (time.time() - start) * 1000
            return LayerSignal(
                layer_name="retrieval",
                score=score,
                confidence=confidence,
                details=details,
                latency_ms=latency,
                attack_type=AttackType.RETRIEVAL_MANIPULATION if score > 0.5 else None,
            )
        except Exception as e:
            logger.error(f"[{session_id}] Retrieval analysis error: {e}")
            return LayerSignal(
                layer_name="retrieval",
                score=0.0,
                confidence=0.0,
                details={"error": str(e)},
                latency_ms=(time.time() - start) * 1000,
            )

    def _run_output_verification(
        self,
        query: str,
        documents: List[Document],
        generated_output: Optional[str],
        session_id: str,
    ) -> LayerSignal:
        """Run output consistency verification layer."""
        start = time.time()
        try:
            score, confidence, details = self.output_verifier.verify(
                query, documents, generated_output
            )
            latency = (time.time() - start) * 1000
            return LayerSignal(
                layer_name="output",
                score=score,
                confidence=confidence,
                details=details,
                latency_ms=latency,
                attack_type=AttackType.OUTPUT_INSTABILITY if score > 0.5 else None,
            )
        except Exception as e:
            logger.error(f"[{session_id}] Output verification error: {e}")
            return LayerSignal(
                layer_name="output",
                score=0.0,
                confidence=0.0,
                details={"error": str(e)},
                latency_ms=(time.time() - start) * 1000,
            )

    def _should_verify_output(self, layer_signals: Dict[str, LayerSignal]) -> bool:
        """Determine if output verification should be triggered.

        Per the paper, output verification only runs for queries with
        elevated threat signals from prior layers (<0.1% of traffic).
        """
        if not layer_signals:
            return False

        # Calculate preliminary threat score
        total_score = sum(
            s.score * self.config.get_layer_weight(s.layer_name)
            for s in layer_signals.values()
        )
        max_weight = sum(
            self.config.get_layer_weight(s.layer_name)
            for s in layer_signals.values()
        )

        if max_weight == 0:
            return False

        preliminary_score = total_score / max_weight
        return preliminary_score > 0.4  # Trigger threshold

    def get_stats(self) -> Dict[str, Any]:
        """Get framework statistics."""
        return {
            "mode": self.config.mode.value if isinstance(self.config.mode, OperationalMode) else self.config.mode,
            "queries_processed": self._query_count,
            "layers_enabled": {
                "prompt": self.prompt_detector is not None,
                "embedding": self.attestation_layer is not None,
                "retrieval": self.retrieval_analyzer is not None,
                "output": self.output_verifier is not None,
            },
            "config": {
                "thresholds": self.config.thresholds,
                "layer_weights": self.config.layer_weights,
            },
        }

    def reset(self) -> None:
        """Reset framework state (e.g., PCA model, query count)."""
        self._query_count = 0
        if self.retrieval_analyzer:
            self.retrieval_analyzer.reset()
        logger.info("EmbedGuard state reset")
