"""
Layer 4: Output Consistency Verification.

This module implements perturbation-based stability testing to detect
output manipulation through document-level perturbations.

Performance (from paper):
    - Stability score computation: 12.8ms per query
    - Triggered for <0.1% of queries (elevated threat only)
    - K=5 perturbations default
"""

import random
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from embedguard.types import Document


class OutputConsistencyVerifier:
    """Verifies output consistency through perturbation testing.

    This implements Layer 4 of the EmbedGuard architecture. It tests
    output stability by:
    1. Generating K perturbations of the document set
    2. Computing semantic similarity between outputs
    3. Flagging unstable outputs that vary significantly

    This layer is only triggered for queries with elevated threat
    signals from prior layers (<0.1% of traffic per paper).

    Attributes:
        model_name: Embedding model for semantic similarity
        device: Device for inference
        k_perturbations: Number of perturbations (K=5 in paper)
        stability_threshold: Minimum stability score

    Example:
        >>> verifier = OutputConsistencyVerifier()
        >>> score, conf, details = verifier.verify(query, documents)
        >>> if score > 0.35:  # Inverted: high score = unstable
        ...     print("Output instability detected")
    """

    # Perturbation strategies
    STRATEGIES = [
        "document_removal",
        "document_reorder",
        "chunk_removal",
        "noise_injection",
    ]

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        device: str = "cpu",
        k_perturbations: int = 5,
        stability_threshold: float = 0.65,
        random_seed: int = 42,
    ):
        """Initialize the output verifier.

        Args:
            model_name: Embedding model for similarity computation
            device: Device for inference
            k_perturbations: Number of perturbations per query (K=5)
            stability_threshold: Minimum required stability
            random_seed: Random seed for reproducibility
        """
        self.model_name = model_name
        self.device = device
        self.k_perturbations = k_perturbations
        self.stability_threshold = stability_threshold
        self.random_seed = random_seed

        # Lazy load embedding model
        self._embedding_model = None

        # Set random seed
        random.seed(random_seed)
        np.random.seed(random_seed)

        logger.debug(f"OutputConsistencyVerifier initialized (K={k_perturbations})")

    def _get_embedding_model(self):
        """Lazily load embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedding_model = SentenceTransformer(
                    self.model_name, device=self.device
                )
                logger.debug("Embedding model loaded for output verification")
            except ImportError:
                logger.warning("sentence-transformers not available")
                self._embedding_model = None
        return self._embedding_model

    def verify(
        self,
        query: str,
        documents: List[Document],
        generated_output: Optional[str] = None,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Verify output consistency through perturbation testing.

        Args:
            query: The user query
            documents: Retrieved documents
            generated_output: Optional pre-generated output to test

        Returns:
            Tuple of (instability_score, confidence, details)
            Note: Higher score = MORE unstable (potential attack)
        """
        if not documents:
            return 0.0, 0.0, {"error": "No documents provided"}

        details: Dict[str, Any] = {
            "num_documents": len(documents),
            "k_perturbations": self.k_perturbations,
            "strategies_used": [],
            "perturbation_results": [],
        }

        # Generate perturbations
        perturbations = self._generate_perturbations(documents)
        details["num_perturbations_generated"] = len(perturbations)

        if not perturbations:
            return 0.0, 0.3, {"error": "Could not generate perturbations"}

        # Compute outputs for each perturbation (simulated)
        outputs = []
        if generated_output:
            outputs.append(generated_output)
        else:
            # Generate baseline output from original documents
            baseline_output = self._generate_synthetic_output(query, documents)
            outputs.append(baseline_output)

        # Generate outputs for perturbations
        for i, (perturbed_docs, strategy) in enumerate(perturbations):
            details["strategies_used"].append(strategy)
            perturbed_output = self._generate_synthetic_output(query, perturbed_docs)
            outputs.append(perturbed_output)

        # Compute pairwise similarities
        similarities = self._compute_output_similarities(outputs)
        details["pairwise_similarities"] = similarities

        # Compute stability score
        if similarities:
            mean_similarity = np.mean(similarities)
            std_similarity = np.std(similarities)
            min_similarity = np.min(similarities)

            # Stability score: average similarity across perturbations
            stability_score = mean_similarity

            # Instability score (what we return): 1 - stability
            instability_score = 1.0 - stability_score

            # Confidence based on consistency of similarities
            confidence = 1.0 - std_similarity if std_similarity < 1.0 else 0.5

            details["stability_score"] = float(stability_score)
            details["instability_score"] = float(instability_score)
            details["mean_similarity"] = float(mean_similarity)
            details["std_similarity"] = float(std_similarity)
            details["min_similarity"] = float(min_similarity)
            details["is_stable"] = stability_score >= self.stability_threshold
            details["threshold"] = self.stability_threshold

            return float(instability_score), float(confidence), details

        return 0.0, 0.0, {"error": "Could not compute similarities"}

    def _generate_perturbations(
        self, documents: List[Document]
    ) -> List[Tuple[List[Document], str]]:
        """Generate K perturbations of the document set.

        Args:
            documents: Original document set

        Returns:
            List of (perturbed_documents, strategy_name) tuples
        """
        perturbations = []

        for i in range(self.k_perturbations):
            strategy = self.STRATEGIES[i % len(self.STRATEGIES)]

            if strategy == "document_removal" and len(documents) > 1:
                # Remove a random document
                perturbed = documents.copy()
                idx = random.randint(0, len(perturbed) - 1)
                perturbed = perturbed[:idx] + perturbed[idx + 1:]
                perturbations.append((perturbed, strategy))

            elif strategy == "document_reorder" and len(documents) > 1:
                # Shuffle document order
                perturbed = documents.copy()
                random.shuffle(perturbed)
                perturbations.append((perturbed, strategy))

            elif strategy == "chunk_removal":
                # Remove portions of document content
                perturbed = []
                for doc in documents:
                    # Remove ~20% of content
                    content = doc.content
                    sentences = re.split(r'[.!?]+', content)
                    if len(sentences) > 2:
                        # Remove one random sentence
                        idx = random.randint(0, len(sentences) - 1)
                        sentences = sentences[:idx] + sentences[idx + 1:]
                    new_content = '. '.join(s.strip() for s in sentences if s.strip())
                    perturbed.append(
                        Document(
                            content=new_content,
                            embedding=doc.embedding,
                            document_id=doc.document_id,
                            metadata=doc.metadata,
                        )
                    )
                perturbations.append((perturbed, strategy))

            elif strategy == "noise_injection":
                # Add noise to document content
                perturbed = []
                for doc in documents:
                    # Add random words
                    words = doc.content.split()
                    if len(words) > 5:
                        idx = random.randint(0, len(words) - 1)
                        noise_words = ["additionally", "furthermore", "however"]
                        words.insert(idx, random.choice(noise_words))
                    new_content = ' '.join(words)
                    perturbed.append(
                        Document(
                            content=new_content,
                            embedding=doc.embedding,
                            document_id=doc.document_id,
                            metadata=doc.metadata,
                        )
                    )
                perturbations.append((perturbed, strategy))

            else:
                # Default: use original with slight modification
                perturbations.append((documents.copy(), "identity"))

        return perturbations

    def _generate_synthetic_output(
        self, query: str, documents: List[Document]
    ) -> str:
        """Generate synthetic output for testing.

        In production, this would call the actual LLM. For testing,
        we generate a deterministic output based on document content.
        """
        # Concatenate key content from documents
        doc_contents = [d.content[:200] for d in documents[:3]]
        combined = f"Based on the query '{query[:50]}': " + " ".join(doc_contents)

        # Truncate to reasonable length
        return combined[:500]

    def _compute_output_similarities(
        self, outputs: List[str]
    ) -> List[float]:
        """Compute pairwise semantic similarities between outputs.

        Args:
            outputs: List of generated outputs

        Returns:
            List of similarity scores
        """
        if len(outputs) < 2:
            return []

        model = self._get_embedding_model()

        if model is not None:
            try:
                # Compute embeddings
                embeddings = model.encode(outputs, convert_to_numpy=True)

                # Compute cosine similarities with baseline (first output)
                baseline = embeddings[0]
                similarities = []
                for i in range(1, len(embeddings)):
                    sim = np.dot(baseline, embeddings[i]) / (
                        np.linalg.norm(baseline) * np.linalg.norm(embeddings[i])
                    )
                    similarities.append(float(sim))

                return similarities

            except Exception as e:
                logger.error(f"Similarity computation error: {e}")

        # Fallback: simple text overlap similarity
        similarities = []
        baseline_words = set(outputs[0].lower().split())
        for i in range(1, len(outputs)):
            other_words = set(outputs[i].lower().split())
            if baseline_words or other_words:
                jaccard = len(baseline_words & other_words) / len(
                    baseline_words | other_words
                )
                similarities.append(jaccard)
            else:
                similarities.append(0.0)

        return similarities


# Convenience function for quick verification
def verify_output_stability(
    query: str,
    documents: List[Document],
    k: int = 5,
    threshold: float = 0.65,
) -> bool:
    """Quick check if output is stable across perturbations.

    Args:
        query: User query
        documents: Retrieved documents
        k: Number of perturbations
        threshold: Stability threshold

    Returns:
        True if output is stable (no detected attack)
    """
    verifier = OutputConsistencyVerifier(
        k_perturbations=k,
        stability_threshold=threshold,
    )
    score, _, details = verifier.verify(query, documents)
    return score < (1 - threshold)  # Invert: low instability = stable
