"""
Layer 2: Cryptographic Embedding Attestation.

This module implements TEE-based cryptographic verification of embedding provenance.
It transforms embedding security from a statistical inference problem into a
cryptographic verification problem.

Performance (from paper):
    - Signature generation: 1.8ms per embedding
    - Validation overhead: 0.3ms per document
    - Batch validation (10 docs): 2.1ms

Note:
    Full TEE functionality requires AMD SEV-SNP or Intel SGX hardware.
    This implementation provides a software simulation for development/testing.
"""

import hashlib
import hmac
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from embedguard.types import AttestationResult, Document


@dataclass
class AttestationCertificate:
    """Cryptographic attestation certificate for an embedding.

    Attributes:
        document_hash: SHA-256 hash of the source document
        model_hash: Hash of the embedding model weights
        embedding_hash: Hash of the output embedding vector
        timestamp: Certificate generation timestamp
        validity_period: Certificate validity duration
        signature: Cryptographic signature binding all fields
        pcr_values: Platform Configuration Register values (TEE)
    """

    document_hash: str
    model_hash: str
    embedding_hash: str
    timestamp: str
    validity_period: int  # seconds
    signature: str
    pcr_values: Optional[Dict[str, str]] = None

    def is_expired(self) -> bool:
        """Check if certificate has expired."""
        cert_time = datetime.fromisoformat(self.timestamp)
        expiry = cert_time + timedelta(seconds=self.validity_period)
        return datetime.utcnow() > expiry

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_hash": self.document_hash,
            "model_hash": self.model_hash,
            "embedding_hash": self.embedding_hash,
            "timestamp": self.timestamp,
            "validity_period": self.validity_period,
            "signature": self.signature,
            "pcr_values": self.pcr_values,
        }


class EmbeddingAttestationLayer:
    """TEE-based embedding attestation layer.

    This implements Layer 2 of the EmbedGuard architecture. In production with
    TEE hardware (AMD SEV-SNP), embeddings are generated inside a secure enclave
    and cryptographically signed.

    For development/testing without TEE hardware, this provides a software
    simulation that demonstrates the attestation protocol.

    Attributes:
        model_name: Name of the embedding model
        device: Device for embedding generation
        secret_key: Key for signing certificates (in production, from TEE)
        validity_period: Certificate validity in seconds

    Example:
        >>> attestation = EmbeddingAttestationLayer()
        >>> cert = attestation.generate_attestation(document, embedding)
        >>> is_valid = attestation.verify_attestation(document, embedding, cert)
    """

    # Simulated model hash (in production, computed from actual model weights)
    MODEL_HASH = "sha256:a1b2c3d4e5f6789012345678901234567890abcdef"

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        device: str = "cpu",
        secret_key: Optional[bytes] = None,
        validity_period: int = 86400,  # 24 hours
        tee_available: bool = False,
    ):
        """Initialize attestation layer.

        Args:
            model_name: Embedding model name
            device: Device for inference
            secret_key: HMAC key for signing (auto-generated if None)
            validity_period: Certificate validity in seconds
            tee_available: Whether TEE hardware is available
        """
        self.model_name = model_name
        self.device = device
        self.validity_period = validity_period
        self.tee_available = tee_available

        # In production, this key is protected by TEE
        # Here we simulate with a random key
        self.secret_key = secret_key or self._generate_secret_key()

        # Load embedding model lazily
        self._embedding_model = None

        logger.debug(
            f"EmbeddingAttestationLayer initialized (tee={tee_available})"
        )

    def _generate_secret_key(self) -> bytes:
        """Generate a secret key for signing."""
        import secrets
        return secrets.token_bytes(32)

    def _get_embedding_model(self):
        """Lazily load embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(
                    self.model_name, device=self.device
                )
                logger.debug("Embedding model loaded")
            except ImportError:
                logger.warning("sentence-transformers not available")
                self._embedding_model = None
        return self._embedding_model

    def _compute_document_hash(self, content: str) -> str:
        """Compute SHA-256 hash of document content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _compute_embedding_hash(self, embedding: List[float]) -> str:
        """Compute hash of embedding vector."""
        # Convert to bytes and hash
        arr = np.array(embedding, dtype=np.float32)
        return hashlib.sha256(arr.tobytes()).hexdigest()

    def _sign_certificate(self, data: str) -> str:
        """Sign certificate data with secret key."""
        signature = hmac.new(
            self.secret_key,
            data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _verify_signature(self, data: str, signature: str) -> bool:
        """Verify signature."""
        expected = self._sign_certificate(data)
        return hmac.compare_digest(expected, signature)

    def generate_embedding_with_attestation(
        self, document: str
    ) -> Tuple[List[float], AttestationCertificate]:
        """Generate embedding inside TEE and create attestation certificate.

        In production with TEE hardware, this entire operation happens inside
        the secure enclave, with the signature protected by hardware keys.

        Args:
            document: Document content to embed

        Returns:
            Tuple of (embedding vector, attestation certificate)
        """
        # Generate embedding
        model = self._get_embedding_model()
        if model is not None:
            embedding = model.encode(document, convert_to_numpy=True).tolist()
        else:
            # Fallback: generate random embedding for testing
            embedding = np.random.randn(768).tolist()

        # Create attestation certificate
        document_hash = self._compute_document_hash(document)
        embedding_hash = self._compute_embedding_hash(embedding)
        timestamp = datetime.utcnow().isoformat()

        # Build signature data
        sign_data = f"{document_hash}|{self.MODEL_HASH}|{embedding_hash}|{timestamp}"
        signature = self._sign_certificate(sign_data)

        # PCR values would come from TEE in production
        pcr_values = {
            "PCR0": hashlib.sha256(b"firmware").hexdigest()[:16],
            "PCR7": hashlib.sha256(b"secureboot").hexdigest()[:16],
        } if self.tee_available else None

        certificate = AttestationCertificate(
            document_hash=document_hash,
            model_hash=self.MODEL_HASH,
            embedding_hash=embedding_hash,
            timestamp=timestamp,
            validity_period=self.validity_period,
            signature=signature,
            pcr_values=pcr_values,
        )

        return embedding, certificate

    def verify_attestation(
        self,
        document: str,
        embedding: List[float],
        certificate: AttestationCertificate,
    ) -> AttestationResult:
        """Verify embedding attestation certificate.

        Args:
            document: Original document content
            embedding: Embedding vector to verify
            certificate: Attestation certificate

        Returns:
            AttestationResult with verification status
        """
        errors = []

        # Check expiration
        if certificate.is_expired():
            errors.append("Certificate expired")

        # Verify document hash
        doc_hash = self._compute_document_hash(document)
        if doc_hash != certificate.document_hash:
            errors.append("Document hash mismatch")

        # Verify embedding hash
        emb_hash = self._compute_embedding_hash(embedding)
        if emb_hash != certificate.embedding_hash:
            errors.append("Embedding hash mismatch")

        # Verify model hash
        if certificate.model_hash != self.MODEL_HASH:
            errors.append("Model hash mismatch")

        # Verify signature
        sign_data = (
            f"{certificate.document_hash}|{certificate.model_hash}|"
            f"{certificate.embedding_hash}|{certificate.timestamp}"
        )
        if not self._verify_signature(sign_data, certificate.signature):
            errors.append("Invalid signature")

        is_valid = len(errors) == 0

        return AttestationResult(
            is_valid=is_valid,
            document_hash=certificate.document_hash,
            model_hash=certificate.model_hash,
            timestamp=certificate.timestamp,
            signature=certificate.signature,
            error="; ".join(errors) if errors else None,
        )

    def verify_batch(
        self, documents: List[Document]
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Verify attestation for a batch of documents.

        Documents without attestation certificates are flagged as unverified.

        Args:
            documents: List of Document objects

        Returns:
            Tuple of (score, confidence, details) where:
                - score: 0.0 to 1.0, higher = more unverified documents
                - confidence: 0.0 to 1.0
                - details: Verification details
        """
        if not documents:
            return 0.0, 0.0, {"error": "No documents provided"}

        verified_count = 0
        unverified_count = 0
        failed_count = 0
        results = []

        for doc in documents:
            if doc.attestation is None:
                # No attestation - count as unverified
                unverified_count += 1
                results.append({"doc_id": doc.document_id, "status": "unverified"})
            else:
                # Has attestation - verify it
                if doc.embedding is not None:
                    result = self.verify_attestation(
                        doc.content, doc.embedding,
                        AttestationCertificate(**doc.attestation.__dict__)
                        if hasattr(doc.attestation, '__dict__')
                        else doc.attestation
                    )
                    if result.is_valid:
                        verified_count += 1
                        results.append({"doc_id": doc.document_id, "status": "verified"})
                    else:
                        failed_count += 1
                        results.append({
                            "doc_id": doc.document_id,
                            "status": "failed",
                            "error": result.error,
                        })
                else:
                    unverified_count += 1
                    results.append({"doc_id": doc.document_id, "status": "no_embedding"})

        total = len(documents)
        # Score: proportion of unverified/failed documents
        score = (unverified_count + failed_count) / total
        # Confidence: higher if we have clear results
        confidence = verified_count / total if verified_count > 0 else 0.5

        details = {
            "total_documents": total,
            "verified": verified_count,
            "unverified": unverified_count,
            "failed": failed_count,
            "results": results,
        }

        return score, confidence, details


# Convenience function for creating attested embeddings
def create_attested_embedding(
    document: str,
    model_name: str = "sentence-transformers/all-mpnet-base-v2",
) -> Tuple[List[float], Dict[str, Any]]:
    """Create an embedding with attestation certificate.

    Args:
        document: Document content
        model_name: Embedding model name

    Returns:
        Tuple of (embedding, certificate_dict)
    """
    layer = EmbeddingAttestationLayer(model_name=model_name)
    embedding, cert = layer.generate_embedding_with_attestation(document)
    return embedding, cert.to_dict()
