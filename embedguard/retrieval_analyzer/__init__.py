"""
Layer 3: Retrieval Distributional Analysis.

This experimental module combines simplified PCA reconstruction error,
regularized Mahalanobis distance, and temporal rank correlation. It is not
exercised by the open Tier-2 benchmark.
"""

import hashlib
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from scipy import stats

from embedguard.types import Document


class IncrementalPCA:
    """Simplified bounded-window PCA for streaming embedding analysis.

    New rows accumulate in a bounded buffer. Once warm-up is reached, each
    scheduled update recomputes SVD over that window; this is not a true
    incremental-SVD implementation.

    Attributes:
        n_components: Number of principal components
        n_samples_seen: Total samples processed
        mean: Running mean of the data
        components: Principal component vectors
        singular_values: Singular values corresponding to components
    """

    def __init__(self, n_components: int = 50, batch_size: int = 100):
        """Initialize Incremental PCA.

        Args:
            n_components: Number of components to retain (k=50 in paper)
            batch_size: Batch size for incremental updates
        """
        self.n_components = n_components
        self.batch_size = batch_size
        self.n_samples_seen = 0
        self.mean: Optional[np.ndarray] = None
        self.components: Optional[np.ndarray] = None
        self.singular_values: Optional[np.ndarray] = None
        self._batch_buffer: List[np.ndarray] = []

    def partial_fit(self, X: np.ndarray) -> "IncrementalPCA":
        """Incrementally fit the PCA model with new data.

        Args:
            X: Data matrix of shape (n_samples, n_features)

        Returns:
            self
        """
        X = np.atleast_2d(X)
        n_samples, n_features = X.shape

        if self.mean is None:
            self.mean = np.zeros(n_features)
            self.components = np.zeros((self.n_components, n_features))
            self.singular_values = np.zeros(self.n_components)

        if X.shape[1] != self.mean.shape[0]:
            raise ValueError("PCA feature dimension changed")
        assert self.components is not None
        assert self.singular_values is not None

        # Retain a bounded window so every SVD update sees accumulated rows,
        # not only the latest query batch.
        self._batch_buffer.append(X.copy())
        accumulated = np.vstack(self._batch_buffer)
        if len(accumulated) > self.batch_size:
            accumulated = accumulated[-self.batch_size :]
            self._batch_buffer = [accumulated]

        self.n_samples_seen += n_samples
        self.mean = np.mean(accumulated, axis=0)

        # Simplified bounded-window SVD; this is intentionally not presented as
        # a production incremental-SVD implementation.
        if self.n_samples_seen >= self.batch_size:
            try:
                X_centered = accumulated - self.mean
                U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
                n_comp = min(self.n_components, len(S))
                self.components.fill(0.0)
                self.singular_values.fill(0.0)
                self.components[:n_comp] = Vt[:n_comp]
                self.singular_values[:n_comp] = S[:n_comp]
            except np.linalg.LinAlgError:
                logger.warning("SVD did not converge, keeping previous components")
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Project data onto principal components.

        Args:
            X: Data matrix of shape (n_samples, n_features)

        Returns:
            Projected data of shape (n_samples, n_components)
        """
        if self.mean is None or self.components is None:
            raise ValueError("PCA model not fitted")

        X = np.atleast_2d(X)
        X_centered = X - self.mean
        return X_centered @ self.components.T

    def inverse_transform(self, X_transformed: np.ndarray) -> np.ndarray:
        """Reconstruct data from principal components.

        Args:
            X_transformed: Projected data

        Returns:
            Reconstructed data
        """
        if self.mean is None or self.components is None:
            raise ValueError("PCA model not fitted")

        return X_transformed @ self.components + self.mean

    def reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """Compute reconstruction error for anomaly detection.

        Args:
            X: Data matrix

        Returns:
            Per-sample reconstruction error
        """
        X_transformed = self.transform(X)
        X_reconstructed = self.inverse_transform(X_transformed)
        return np.linalg.norm(X - X_reconstructed, axis=1)


class RetrievalDistributionalAnalyzer:
    """Analyzes retrieval distribution for anomaly detection.

    This implements Layer 3 of the EmbedGuard architecture. It monitors
    the statistical distribution of retrieved documents using:
    1. Incremental PCA for dimension reduction
    2. Mahalanobis distance between expected and observed distributions
    3. Temporal rank correlation analysis

    Attributes:
        n_components: Number of PCA components
        kl_threshold: Legacy configuration field retained for API compatibility;
            the current Mahalanobis scorer does not use it directly
        history_size: Number of queries to maintain in history
        pca: Incremental PCA model
        baseline_distribution: Expected distribution from training

    Example:
        >>> analyzer = RetrievalDistributionalAnalyzer()
        >>> score, conf, details = analyzer.analyze(query, documents)
        >>> if score > 0.85:
        ...     print("Anomalous retrieval distribution detected")
    """

    def __init__(
        self,
        n_components: int = 50,
        kl_threshold: float = 0.15,
        rank_correlation_min: float = 0.30,
        history_size: int = 1000,
        update_frequency: int = 1000,
        component_weights: Optional[Dict[str, float]] = None,
        anomaly_threshold: float = 0.5,
        min_rank_overlap: int = 2,
    ):
        """Initialize the retrieval analyzer.

        Args:
            n_components: PCA components (k=50 in paper)
            kl_threshold: Legacy threshold field retained for compatibility
            rank_correlation_min: Minimum expected rank correlation
            history_size: Number of queries to track
            update_frequency: Update PCA every N queries
            component_weights: Fusion weights for the ``pca``, ``kl`` and
                ``rank`` components (default 0.5/0.3/0.2). Each weight is
                multiplied by the component's confidence; components with
                confidence 0 are excluded and the rest renormalised.
            anomaly_threshold: Fused score above which ``is_anomalous`` is
                set. The 0.5 default is uncalibrated; use
                :meth:`calibrate_threshold` on held-out clean traffic.
            min_rank_overlap: Minimum number of shared retrieved document IDs
                for a prior query to be comparable in the rank component
        """
        self.n_components = n_components
        self.kl_threshold = kl_threshold
        self.rank_correlation_min = rank_correlation_min
        self.history_size = history_size
        self.update_frequency = update_frequency
        weights = {"pca": 0.5, "kl": 0.3, "rank": 0.2}
        if component_weights:
            unknown = set(component_weights) - set(weights)
            if unknown:
                raise ValueError(f"Unknown component weights: {sorted(unknown)}")
            weights.update(component_weights)
        if any(w < 0 for w in weights.values()):
            raise ValueError("Component weights must be non-negative")
        if not any(w > 0 for w in weights.values()):
            raise ValueError("At least one component weight must be positive")
        self.component_weights = weights
        self.anomaly_threshold = float(anomaly_threshold)
        self.min_rank_overlap = max(2, int(min_rank_overlap))

        # Initialize PCA
        self.pca = IncrementalPCA(n_components=n_components)

        # History tracking
        self.query_history: deque = deque(maxlen=history_size)
        self.embedding_history: deque = deque(maxlen=history_size)
        self.score_history: deque = deque(maxlen=history_size)
        # Per-query retrieved document_id ranking (best first)
        self.rank_history: deque = deque(maxlen=history_size)
        # When False, scoring no longer updates the PCA model, the covariance
        # buffer or the baseline mean. See freeze_baseline().
        self.adapt_baseline = True

        # Baseline distribution (updated during training)
        self.baseline_mean: Optional[np.ndarray] = None
        self.baseline_std: Optional[np.ndarray] = None
        self.baseline_ranks: Optional[np.ndarray] = None

        # Query counter for update scheduling
        self._query_count = 0

        logger.debug(f"RetrievalDistributionalAnalyzer initialized (k={n_components})")

    def analyze(
        self,
        query: str,
        documents: List[Document],
        query_id: Optional[int] = None,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Analyze retrieval distribution for anomalies.

        Args:
            query: The user query
            documents: Retrieved documents with embeddings
            query_id: Optional query identifier

        Returns:
            Tuple of (anomaly_score, confidence, details)
        """
        self._query_count += 1

        # Extract embeddings
        embeddings = self._extract_embeddings(documents)

        if embeddings is None or len(embeddings) == 0:
            return 0.0, 0.0, {"error": "No embeddings available"}

        details: Dict[str, Any] = {
            "num_documents": len(documents),
            "embedding_dim": embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
        }

        scores: List[float] = []
        confidences: List[float] = []
        names: List[str] = []

        # 1. PCA-based anomaly detection
        pca_score, pca_conf, pca_details = self._pca_anomaly_score(embeddings)
        details["pca"] = pca_details
        scores.append(pca_score)
        confidences.append(pca_conf)
        names.append("pca")

        # 2. Distribution-distance analysis. The private method name is retained
        # for compatibility, but the implementation computes Mahalanobis distance.
        kl_score, kl_conf, kl_details = self._kl_divergence_score(embeddings)
        details["distribution_distance"] = kl_details
        details["kl_divergence"] = kl_details
        scores.append(kl_score)
        confidences.append(kl_conf)
        names.append("kl")

        # 3. Rank correlation analysis. Every query contributes history;
        # evaluation starts only after the warm-up window is populated.
        if len(self.score_history) >= 10:
            rank_score, rank_conf, rank_details = self._rank_correlation_score(
                documents
            )
            details["rank_correlation"] = rank_details
            scores.append(rank_score)
            confidences.append(rank_conf)
            names.append("rank")
        else:
            details["rank_correlation"] = {
                "status": "warming_up",
                "history_size": len(self.score_history),
                "required_history": 10,
            }

        current_scores = self._document_scores(documents)
        if current_scores:
            self.score_history.append(current_scores)
        current_ranking = self._document_ranking(documents)
        if current_ranking:
            self.rank_history.append(current_ranking)

        # Update history
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        self.query_history.append(query_hash)
        self.embedding_history.append(np.mean(embeddings, axis=0))

        # Update PCA periodically
        if self.adapt_baseline and self._query_count % self.update_frequency == 0:
            self._update_pca(embeddings)

        # Combine scores: configured weight x confidence, dropping components
        # that reported zero confidence (e.g. no comparable rank history).
        fusion_weights = {
            name: self.component_weights[name] * conf
            for name, conf in zip(names, confidences)
            if conf > 0 and self.component_weights[name] > 0
        }
        total_weight = sum(fusion_weights.values())
        if total_weight > 0:
            final_score = sum(
                score * fusion_weights[name]
                for name, score in zip(names, scores)
                if name in fusion_weights
            ) / total_weight
            final_confidence = float(np.mean([
                conf for name, conf in zip(names, confidences)
                if fusion_weights.get(name, 0.0) > 0
            ]))
        else:
            final_score = 0.0
            final_confidence = 0.0

        details["component_scores"] = {
            "pca": pca_score,
            "kl": kl_score,
            "rank": scores[names.index("rank")] if "rank" in names else None,
        }
        details["fusion_weights"] = {
            name: w / total_weight for name, w in fusion_weights.items()
        } if total_weight > 0 else {}
        details["anomaly_threshold"] = self.anomaly_threshold
        details["is_anomalous"] = bool(final_score > self.anomaly_threshold)

        return float(final_score), float(final_confidence), details

    def _extract_embeddings(
        self, documents: List[Document]
    ) -> Optional[np.ndarray]:
        """Extract embeddings from documents."""
        embeddings = []
        for doc in documents:
            if doc.embedding is not None:
                embeddings.append(doc.embedding)

        if not embeddings:
            return None

        return np.array(embeddings)

    def _pca_anomaly_score(
        self, embeddings: np.ndarray
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Compute PCA-based anomaly score.

        Uses reconstruction error to detect out-of-distribution retrievals.
        """
        details = {}

        # Fit PCA if needed. A frozen analyzer never fits on scored traffic.
        if self.pca.n_samples_seen < self.pca.batch_size:
            if not self.adapt_baseline:
                details["status"] = "frozen_before_warmup"
                return 0.0, 0.0, details
            self.pca.partial_fit(embeddings)
            if self.pca.n_samples_seen < self.pca.batch_size:
                details["status"] = "warming_up"
                details["samples_seen"] = self.pca.n_samples_seen
                return 0.0, 0.3, details
            details["status"] = "ready"

        try:
            # Compute reconstruction error
            errors = self.pca.reconstruction_error(embeddings)
            mean_error = np.mean(errors)
            max_error = np.max(errors)

            # Normalize to 0-1 range (assuming typical errors)
            # Higher error = more anomalous
            score = min(mean_error / 10.0, 1.0)
            confidence = 0.8 if self.pca.n_samples_seen > 500 else 0.5

            details["mean_reconstruction_error"] = float(mean_error)
            details["max_reconstruction_error"] = float(max_error)
            details["samples_seen"] = self.pca.n_samples_seen

            return score, confidence, details

        except Exception as e:
            logger.error(f"PCA anomaly detection error: {e}")
            return 0.0, 0.0, {"error": str(e)}

    def _kl_divergence_score(
        self, embeddings: np.ndarray
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Compute Mahalanobis distance from baseline distribution.

        Uses a regularized full covariance once the buffered rows (last 100
        batches) number at least ``d + 10``. Below that it uses a diagonal
        approximation whose per-dimension scale is fixed from the first
        post-initialisation batch. With top-5 retrieval and 768-dimensional
        embeddings the buffer holds at most 500 rows, so only the diagonal
        path runs.
        
        Mahalanobis distance: D² = (x - μ)ᵀ Σ⁻¹ (x - μ)
        where Σ is the covariance matrix of the baseline distribution.
        """
        details = {}

        # Compute current distribution statistics
        current_mean = np.mean(embeddings, axis=0)

        # Update baseline if not set. A frozen analyzer never initialises
        # its baseline from scored traffic, which may be an attack.
        if self.baseline_mean is None and not self.adapt_baseline:
            details["status"] = "frozen_before_warmup"
            return 0.0, 0.0, details
        if self.baseline_mean is None:
            self.baseline_mean = current_mean
            # Initialize covariance as identity (will be updated)
            self._baseline_cov = None
            self._baseline_cov_inv = None
            self._embedding_buffer = [embeddings]
            details["status"] = "baseline_initialized"
            return 0.0, 0.3, details

        try:
            # Accumulate embeddings for covariance estimation
            if not hasattr(self, '_embedding_buffer'):
                self._embedding_buffer = []
            if self.adapt_baseline:
                self._embedding_buffer.append(embeddings)
            
            # Only compute full covariance after sufficient samples
            # Need more samples than dimensions for stable covariance
            all_embeddings = np.vstack(self._embedding_buffer[-100:])  # Last 100 batches
            n_samples = all_embeddings.shape[0]
            n_features = all_embeddings.shape[1]
            
            if n_samples < n_features + 10:
                # Fall back to diagonal covariance until we have enough samples
                current_std = np.std(embeddings, axis=0) + 1e-8
                if not hasattr(self, 'baseline_std') or self.baseline_std is None:
                    if not self.adapt_baseline:
                        return 0.0, 0.0, {"status": "frozen_before_warmup"}
                    self.baseline_std = current_std
                    return 0.0, 0.3, {"status": "accumulating_samples", "n_samples": n_samples}
                
                # Simplified Mahalanobis with diagonal
                diff = current_mean - self.baseline_mean
                mahal_sq = np.sum((diff / self.baseline_std) ** 2)
                mahal_dist = np.sqrt(mahal_sq)
            else:
                # Compute full covariance matrix with regularization
                cov_matrix = np.cov(all_embeddings.T)
                
                # Add Tikhonov regularization for numerical stability
                # λ = 0.01 × trace(Σ) / n_features
                regularization = 0.01 * np.trace(cov_matrix) / n_features
                cov_matrix += regularization * np.eye(n_features)
                
                # Compute inverse using pseudo-inverse for stability
                try:
                    cov_inv = np.linalg.pinv(cov_matrix)
                except np.linalg.LinAlgError:
                    # Fallback to diagonal
                    cov_inv = np.diag(1.0 / (np.diag(cov_matrix) + 1e-8))
                
                # Mahalanobis distance
                diff = current_mean - self.baseline_mean
                mahal_sq = diff @ cov_inv @ diff
                mahal_dist = np.sqrt(max(0, mahal_sq))
                
                details["covariance_rank"] = np.linalg.matrix_rank(cov_matrix)
                details["regularization"] = float(regularization)

            # Chi-squared threshold for multivariate Gaussian
            # At 95% confidence, D² ~ χ²_{n_features}
            chi2_threshold = np.sqrt(n_features)  # Rough approximation
            
            # Normalize to 0-1 score
            score = min(mahal_dist / (chi2_threshold * 3), 1.0)
            confidence = 0.75 if n_samples > 50 else 0.5

            details["mahalanobis_distance"] = float(mahal_dist)
            details["chi2_threshold"] = float(chi2_threshold)
            details["exceeds_threshold"] = mahal_dist > chi2_threshold
            details["n_samples_for_cov"] = n_samples

            # Update baseline with exponential moving average. An adaptive
            # baseline also learns from attack traffic, so a sustained
            # campaign pulls it toward itself; freeze_baseline() stops this.
            if self.adapt_baseline:
                alpha = 0.01
                self.baseline_mean = alpha * current_mean + (1 - alpha) * self.baseline_mean

            return score, confidence, details

        except Exception as e:
            logger.error(f"Mahalanobis distance error: {e}")
            return 0.0, 0.0, {"error": str(e)}

    @staticmethod
    def _document_scores(documents: List[Document]) -> List[float]:
        """Extract comparable retrieval scores for temporal analysis."""
        scores = []
        for doc in documents:
            if doc.metadata.get("similarity_score") is not None:
                scores.append(float(doc.metadata["similarity_score"]))
            elif doc.embedding is not None:
                scores.append(float(np.linalg.norm(doc.embedding)))
            else:
                scores.append(0.0)
        return scores

    @staticmethod
    def _document_ranking(documents: List[Document]) -> List[str]:
        """Return retrieved document IDs ordered best-first.

        Uses ``similarity_score`` metadata when every document has one,
        otherwise the retrieval order supplied by the caller.
        """
        pairs = [
            (doc.document_id, doc.metadata.get("similarity_score"))
            for doc in documents
            if doc.document_id is not None
        ]
        ids = [doc_id for doc_id, _ in pairs]
        sims = [sim for _, sim in pairs]
        if pairs and all(
            sim is not None and np.isfinite(float(sim)) for sim in sims
        ):
            # Stable sort: ties keep the caller's order.
            order = sorted(range(len(pairs)), key=lambda i: -float(sims[i]))
            return [ids[i] for i in order]
        return ids

    def _rank_correlation_score(
        self, documents: List[Document]
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Analyze temporal rank consistency of retrieval results.

        Compares the current document ranking with the most recent prior
        query whose retrieved ID set shares at least ``min_rank_overlap``
        documents, using Spearman correlation over the shared documents'
        ranks. Comparing sorted similarity lists of unrelated queries is
        meaningless (both are monotone), so when no comparable history
        exists the component abstains with confidence 0.
        """
        details: Dict[str, Any] = {}

        if len(self.score_history) < 10:
            details["status"] = "insufficient_history"
            return 0.0, 0.3, details

        current = self._document_ranking(documents)
        if not current:
            return 0.0, 0.0, {"error": "No document IDs available"}
        current_pos = {doc_id: i for i, doc_id in enumerate(current)}

        try:
            for lag, previous in enumerate(reversed(self.rank_history), start=1):
                shared = [d for d in previous if d in current_pos]
                if len(shared) < self.min_rank_overlap:
                    continue
                prev_pos = {doc_id: i for i, doc_id in enumerate(previous)}
                curr_ranks = [current_pos[d] for d in shared]
                prev_ranks = [prev_pos[d] for d in shared]
                correlation_raw, p_value_raw = stats.spearmanr(
                    curr_ranks, prev_ranks
                )
                correlation = float(np.asarray(correlation_raw).item())
                p_value = float(np.asarray(p_value_raw).item())
                if np.isnan(correlation):
                    correlation = 0.0

                # Map correlation from [-1, 1] to anomaly score [1, 0].
                score = max(0.0, (1 - correlation) / 2)
                if correlation < self.rank_correlation_min:
                    score = min(score + 0.3, 1.0)  # Boost if below threshold

                details["rank_correlation"] = correlation
                details["p_value"] = None if np.isnan(p_value) else p_value
                details["threshold"] = self.rank_correlation_min
                details["below_threshold"] = correlation < self.rank_correlation_min
                details["shared_documents"] = len(shared)
                details["history_lag"] = lag
                details["status"] = "evaluated"
                return float(score), 0.6, details
        except Exception as e:
            logger.error(f"Rank correlation error: {e}")
            return 0.0, 0.0, {"error": str(e)}

        details["status"] = "no_comparable_history"
        details["min_overlap"] = self.min_rank_overlap
        return 0.0, 0.0, details

    def freeze_baseline(self) -> None:
        """Stop updating the clean-traffic model from scored requests.

        By default the PCA model, the covariance buffer and the baseline mean
        keep learning from every request, including ones that score as
        anomalous. Under a sustained poisoning campaign that pulls the
        baseline toward the attack and the scores decay. Freeze after
        building the baseline on traffic you trust to be clean, and rebuild
        it periodically (``reset`` + warm-up + ``freeze_baseline``) to track
        legitimate drift. Freezing before warm-up leaves the affected
        components abstaining (confidence 0) rather than letting the next,
        possibly adversarial, request initialise them.
        """
        self.adapt_baseline = False

    def unfreeze_baseline(self) -> None:
        """Resume adaptive updates of the clean-traffic model."""
        self.adapt_baseline = True

    @staticmethod
    def calibrate_threshold(
        clean_scores: List[float], target_fpr: float = 0.05
    ) -> float:
        """Return the fused-score threshold giving ``target_fpr`` on clean data.

        The threshold is the ``1 - target_fpr`` quantile of ``clean_scores``;
        ``is_anomalous`` fires strictly above it. Fit it on held-out clean
        traffic (a calibration split) only - never on the data used to
        report TPR/FPR, or the reported FPR is optimistically biased.
        """
        if not 0.0 < target_fpr < 1.0:
            raise ValueError("target_fpr must be in (0, 1)")
        values = np.asarray(list(clean_scores), dtype=float)
        if values.size == 0:
            raise ValueError("clean_scores must be non-empty")
        return float(np.quantile(values, 1.0 - target_fpr, method="higher"))

    def _update_pca(self, embeddings: np.ndarray) -> None:
        """Update PCA model with new embeddings."""
        try:
            self.pca.partial_fit(embeddings)
            logger.debug(f"PCA updated (samples: {self.pca.n_samples_seen})")
        except Exception as e:
            logger.error(f"PCA update error: {e}")

    def reset(self) -> None:
        """Reset analyzer state."""
        self.pca = IncrementalPCA(n_components=self.n_components)
        self.query_history.clear()
        self.embedding_history.clear()
        self.score_history.clear()
        self.rank_history.clear()
        self.adapt_baseline = True
        self.baseline_mean = None
        self.baseline_std = None
        self._query_count = 0
        logger.info("RetrievalDistributionalAnalyzer reset")

    def get_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics."""
        return {
            "queries_processed": self._query_count,
            "pca_samples_seen": self.pca.n_samples_seen,
            "history_size": len(self.query_history),
            "has_baseline": self.baseline_mean is not None,
        }
